import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from glob import glob
from skimage.io import imread
import re
import matplotlib.pyplot as plt
from PIL import Image


class TrainingDataPreparer:

    def __init__(self):
        self.do_sliding_windows = True
        self.labeled = True
        self.sliding_window_side = 256
        self.sliding_window_step = 128
        self.initial_directory = '../test'
        self.save_directory = '../test/save_dir'
        self.output_file_list = []

    def set_labeled_state(self, labeled):
        self.labeled = labeled

    def set_sliding_window_props(self, make_windows, window_side=256, window_step=128):
        self.do_sliding_windows = make_windows
        if make_windows:
            self.sliding_window_side = window_side
            self.sliding_window_step = window_step

    def set_initial_directory(self, path):
        self.initial_directory = path

    def set_save_directory(self, path):
        self.save_directory = path

    def run(self):
        img_df = self.create_dataframe()
        img_df = self.load_all_images(img_df)
        img_df = self.convert_all_images_to_float(img_df)
        self.save_images_as_sliding_windows(img_df)

    def create_dataframe(self):
        image_files, info_files, bbox_files = self.get_initial_file_lists()
        if self.labeled:
            img_df = pd.DataFrame({'img_path': image_files,
                                   'info_path': info_files,
                                   'bounding_boxes_path': bbox_files})
            img_id = lambda in_path: in_path.split('\\')[-2][-6:]
        else:
            img_df = pd.DataFrame({'img_path': image_files})
            img_id = lambda in_path: in_path.split('\\')[-1]
        img_df['ImageID'] = img_df['img_path'].map(img_id)
        return img_df

    def get_initial_file_lists(self):
        info_files = []
        bbox_files = []
        if self.labeled:
            img_files = glob(os.path.join(self.initial_directory, '*', '*.tif'))
            info_files = glob(os.path.join(self.initial_directory, '*', '*.txt'))
            bbox_files = glob(os.path.join(self.initial_directory, '*', '*.csv'))
        else:
            img_files = glob(os.path.join(self.initial_directory, '*.tif'))
        return img_files, info_files, bbox_files

    @staticmethod
    def load_image(img_file):
        image = np.array(Image.open(img_file), dtype=np.uint8)
        return image

    def load_all_images(self, img_df):
        img_df['images'] = img_df['img_path'].map(self.load_image)
        return img_df

    @staticmethod
    def convert_image_to_float(image):
        image_float = image.astype(np.float16) / np.max(image)
        return image_float

    def convert_all_images_to_float(self, img_df):
        img_df['images_float'] = img_df['images'].map(self.convert_image_to_float)
        return img_df

    def yield_sliding_windows(self, image):
        for y in range(0, image.shape[0], self.sliding_window_step):
            for x in range(0, image.shape[1], self.sliding_window_step):
                img_window = image[y:y + self.sliding_window_side, x:x + self.sliding_window_side]
                yield (x, y, img_window)

    def save_images_as_sliding_windows(self, img_df):
        self.output_file_list = []
        for index, row in img_df.iterrows():
            if (index % 500 == 0) & (index > 1):
                print('Splitting image #{}/{}'.format(index, len(img_df)))
            image_dir = self.create_image_directory(index)
            for (x, y, window) in self.yield_sliding_windows(row['images_float']):
                self.save_sliding_window(image_dir, x, y, window)
        self.save_file_list()
        print('Saving done yay')

    def create_image_directory(self, index):
        image_dir = os.path.join(self.save_directory, f'image{index}')
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        return image_dir

    def save_sliding_window(self, image_dir, x, y, window):
        window_file_path = os.path.join(image_dir, f'window_x_{x}_y_{y}_data.npz')
        self.output_file_list.append(window_file_path)
        np.savez(window_file_path, image=window)

    def save_file_list(self):
        np.savez(os.path.join(self.save_directory, 'file_list.npz'), file_list=np.array(self.output_file_list))
