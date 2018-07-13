"""
This is a class for training and evaluating yadk2
"""
import os

import numpy as np
import tensorflow as tf
from PIL import Image
from keras import backend as K
from keras.callbacks import TensorBoard, ModelCheckpoint, EarlyStopping
from keras.layers import Input, Lambda, Conv2D
from keras.models import load_model, Model

from spine_yolo.data_generator import DataGenerator
from spine_yolo.spine_preprocessing.spine_preprocessing import process_data
from spine_yolo.yad2k.models.keras_yolo import (yolo_body,
                                                yolo_eval, yolo_head, yolo_loss)
from spine_yolo.yad2k.utils.draw_boxes import draw_boxes
from spine_yolo.yolo_argparser import YoloArgparse

argparser = YoloArgparse()

# Default anchor boxes
YOLO_ANCHORS = np.array(
    ((0.57273, 0.677385), (1.87446, 2.06253), (3.33843, 5.47434),
     (7.88282, 3.52778), (9.77052, 9.16828)))

MODEL_FILES = {1: 'trained_stage_1',
               2: 'trained_stage_2',
               3: 'trained_stage_3',
               'best': 'trained_stage_3_best',
               'latest': 'trained_latest',
               'testing': 'yolo_spine_model_testing'}


class SpineYolo(object):

    def __init__(self, _args):
        self.data_path = os.path.expanduser(_args.data_path)
        self.classes_path = os.path.expanduser(_args.classes_path)
        self.anchors_path = os.path.expanduser(_args.anchors_path)
        self.starting_weights = os.path.expanduser(_args.starting_weights)
        self.from_scratch = _args.from_scratch == 'on'
        self.training_on = _args.train == 'on'
        self.overfit_single_image = _args.overfit_single_image == 'on'
        self.file_list = None
        self.class_names = None
        self.anchors = None
        self.partition = None
        self.model_save_path = ''
        self.trained_model_path = '../test'
        self.detectors_mask_shape = (13, 13, 5, 1)
        self.matching_boxes_shape = (13, 13, 5, 5)
        self.model_body = None
        self.model = None

    def get_model_file(self, stage):
        model_file = MODEL_FILES[stage] + '.h5'
        file = os.path.join(self.model_save_path, model_file)
        return file

    def set_data_path(self, data_path):
        self.data_path = os.path.expanduser(data_path)
        self.file_list = np.load(self.data_path)['file_list']
        self.partition = self.get_partition()
        self.class_names = self.get_classes()
        self.anchors = self.get_anchors()
        self.partition = self.get_partition()

    def set_trained_model_path(self, path):
        self.trained_model_path = path

    def set_model_save_path(self, path):
        self.model_save_path = path

    def toggle_training(self, do_training):
        self.training_on = do_training

    def run(self):
        if self.training_on:
            self.train()
            self.draw(image_set='validation',  # assumes training/validation split is 0.9
                      weights_name=self.get_model_file('best'),
                      save_all=False)
        else:
            self.draw(test_model_path=self.trained_model_path,
                      image_set='validation',  # assumes training/validation split is 0.9
                      save_all=True)

    def get_partition(self):
        data_len = self.file_list.size
        partition = dict(train=np.array(range(int(0.9 * data_len))),
                         validation=np.array(range(int(0.9 * data_len), data_len)))
        return partition

    def get_classes(self):
        """loads the classes"""
        with open(self.classes_path) as f:
            class_names = f.readlines()
        class_names = [c.strip() for c in class_names]
        return class_names

    def get_anchors(self):
        """loads the anchors from a file"""
        if os.path.isfile(self.anchors_path):
            with open(self.anchors_path) as f:
                anchors = f.readline()
                anchors = [float(x) for x in anchors.split(',')]
                return np.array(anchors).reshape(-1, 2)
        else:
            Warning("Could not open anchors file, using default.")
            return YOLO_ANCHORS

    def create_model(self, load_pretrained=True, freeze_body=True):
        """
        returns the body of the model and the model

        # Params:

        load_pretrained: whether or not to load the pretrained model or initialize all weights

        freeze_body: whether or not to freeze all weights except for the last layer's

        # Returns:

        model_body: YOLOv2 with new output layer

        model: YOLOv2 with custom loss Lambda layer

        """

        # Create model input layers.
        image_input = Input(shape=(416, 416, 3))
        boxes_input = Input(shape=(None, 5))
        detectors_mask_input = Input(shape=self.detectors_mask_shape)
        matching_boxes_input = Input(shape=self.matching_boxes_shape)

        # Create model body.
        yolo_model = yolo_body(image_input, len(self.anchors), len(self.class_names))
        topless_yolo = Model(yolo_model.input, yolo_model.layers[-2].output)

        if load_pretrained:
            # Save topless yolo:
            topless_yolo_path = os.path.join('model_data', 'yolo_topless.h5')
            if not os.path.exists(topless_yolo_path):
                print("CREATING TOPLESS WEIGHTS FILE")
                yolo_path = os.path.join('model_data', 'yolo.h5')
                self.model_body = load_model(yolo_path)
                self.model_body = Model(self.model_body.inputs, self.model_body.layers[-2].output)
                self.model_body.save_weights(topless_yolo_path)
            topless_yolo.load_weights(topless_yolo_path)

        if freeze_body:
            for layer in topless_yolo.layers:
                layer.trainable = False
        final_layer = Conv2D(len(self.anchors) * (5 + len(self.class_names)), (1, 1), activation='linear')(
            topless_yolo.output)

        self.model_body = Model(image_input, final_layer)

        # Place model loss on CPU to reduce GPU memory usage.
        with tf.device('/cpu:0'):
            # TODO: Replace Lambda with custom Keras layer for loss.
            model_loss = Lambda(
                yolo_loss,
                output_shape=(1,),
                name='yolo_loss',
                arguments={'anchors': self.anchors,
                           'num_classes': len(self.class_names)})([
                self.model_body.output, boxes_input,
                detectors_mask_input, matching_boxes_input])

        self.model = Model(
            [self.model_body.input, boxes_input, detectors_mask_input,
             matching_boxes_input], model_loss)

    def train(self):
        """
        retrain/fine-tune the model

        logs training with tensorboard

        saves training weights in current directory

        best weights according to val_loss is saved as trained_stage_3_best.h5
        """
        logging = TensorBoard()
        checkpoint_final_best = ModelCheckpoint(self.get_model_file('best'), monitor='val_loss',
                                                save_weights_only=True, save_best_only=True)
        checkpoint = ModelCheckpoint(self.get_model_file('latest'), monitor='val_loss',
                                     save_weights_only=True, save_best_only=True)

        early_stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=15, verbose=1, mode='auto')

        first_round_weights = self.starting_weights

        # if starting from scratch, train model with frozen body first
        if self.from_scratch:
            first_round_weights = self.get_model_file(1)
            self.create_model()
            self.model.compile(
                optimizer='adam', loss={
                    'yolo_loss': lambda y_true, y_pred: y_pred
                })  # This is a hack to use the custom loss function in the last layer.

            params = {'dim': (416, 416),
                      'batch_size': 32,
                      'n_classes': 1,
                      'n_channels': 3,
                      'shuffle': True}

            training_generator, validation_generator = self.make_data_generators(params)

            self.model.fit_generator(generator=training_generator,
                                     validation_data=validation_generator,
                                     use_multiprocessing=True,
                                     workers=6,
                                     epochs=5,
                                     callbacks=[logging, checkpoint])

            self.model.save_weights(self.get_model_file(1))
            self.draw(image_set='validation', weights_name=first_round_weights,
                      out_path="output_images_stage_1", save_all=False)

        self.create_model(load_pretrained=False, freeze_body=False)

        self.model.load_weights(first_round_weights)

        self.model.compile(
            optimizer='adam', loss={
                'yolo_loss': lambda y_true, y_pred: y_pred
            })  # This is a hack to use the custom loss function in the last layer.

        params = {'dim': (416, 416),
                  'batch_size': 8,
                  'n_classes': 1,
                  'n_channels': 3,
                  'shuffle': True}

        training_generator, validation_generator = self.make_data_generators(params)

        self.model.fit_generator(generator=training_generator,
                                 validation_data=validation_generator,
                                 use_multiprocessing=True,
                                 workers=4,
                                 epochs=30,
                                 callbacks=[logging, checkpoint])

        self.model.save_weights(self.get_model_file(2))

        self.draw(image_set='validation', weights_name=self.get_model_file(2),
                  out_path="output_images_stage_2", save_all=False)

        self.model.fit_generator(generator=training_generator,
                                 validation_data=validation_generator,
                                 use_multiprocessing=True,
                                 workers=4,
                                 epochs=30,
                                 callbacks=[logging, checkpoint_final_best, early_stopping])

        self.model.save_weights(self.get_model_file(3))
        self.model_body.load_weights(self.get_model_file('best'))
        self.model_body.save(self.get_model_file('testing'))

    def make_data_generators(self, params):
        if self.overfit_single_image:
            params['batch_size'] = 1
            partition_train = self.partition['train'][[0, 0]]
            partition_validation = self.partition['train'][[0, 0]]
        else:
            partition_train = self.partition['train']
            partition_validation = self.partition['validation']
        training_generator = DataGenerator(partition_train,
                                           anchors=self.anchors,
                                           file_list=self.file_list,
                                           **params)
        validation_generator = DataGenerator(partition_validation,
                                             anchors=self.anchors,
                                             file_list=self.file_list,
                                             **params)
        return training_generator, validation_generator

    def draw(self, test_model_path=None, image_set='validation',
             weights_name=None,
             out_path="output_images", save_all=True):
        """
        Draw bounding boxes on image data
        """
        if weights_name is None:
            weights_name = self.get_model_file('best')

        if test_model_path is None:
            self.model_body.load_weights(weights_name)
        else:
            self.model_body = load_model(test_model_path)
        if self.overfit_single_image:
            partition_eval = self.partition["train"][[0, 0]]
        else:
            partition_eval = self.partition[image_set]
        # load validation data
        # only annotate 100 images max
        if len(partition_eval) > 100:
            partition_eval = np.random.choice(partition_eval, (100,))

        files_to_load = self.file_list[partition_eval]
        print(files_to_load.shape)
        image_data = [np.load(file)['image'] for file in files_to_load]
        image_data = process_data(image_data)
        image_data = np.array([np.expand_dims(image, axis=0)
                               for image in image_data])

        # Create output variables for prediction.
        yolo_outputs = yolo_head(self.model_body.output, self.anchors, len(self.class_names))
        input_image_shape = K.placeholder(shape=(2,))
        boxes, scores, classes = yolo_eval(
            yolo_outputs, input_image_shape, score_threshold=0.5, iou_threshold=0.5)

        # Run prediction images.
        sess = K.get_session()

        if not os.path.exists(out_path):
            os.makedirs(out_path)
        for i in range(len(image_data)):
            out_boxes, out_scores, out_classes = sess.run(
                [boxes, scores, classes],
                feed_dict={
                    self.model_body.input: image_data[i],
                    input_image_shape: [image_data.shape[2], image_data.shape[3]],
                    K.learning_phase(): 0
                })
            print('Found {} boxes for image.'.format(len(out_boxes)))
            print(out_boxes)

            # Plot image with predicted boxes.
            image_with_boxes = draw_boxes(image_data[i][0], out_boxes, out_classes,
                                          self.class_names, out_scores)
            # Save the image:
            if save_all or (len(out_boxes) > 0):
                image = Image.fromarray(image_with_boxes)
                image.save(os.path.join(out_path, str(i) + '.tif'))


if __name__ == '__main__':
    args = argparser.parse_args()
    app = SpineYolo(args)
