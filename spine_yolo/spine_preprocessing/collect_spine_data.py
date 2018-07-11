import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
from glob import glob
from skimage.io import imread
import re
import matplotlib.pyplot as plt

# Create a dataframe for images and coordinates
root = tk.Tk()
root.withdraw()

data_dir = os.path.normpath(filedialog.askdirectory())
all_images = glob(os.path.join(data_dir, '*', '*.tif'))
all_info = glob(os.path.join(data_dir, '*', '*.txt'))
img_df = pd.DataFrame({'img_path': all_images, 'info_path': all_info})
img_id = lambda in_path: in_path.split('\\')[-2][-6:]
img_df['ImageID'] = img_df['img_path'].map(img_id)

# define regular expressions to get coordinates
regexp_x = re.compile("x = ([0-9.]*),")
regexp_y = re.compile("y = ([0-9.]*)\n")


# function to read coordinates from text file
def read_and_parse_coordinates(info_file):
    file = open(info_file, "r")
    lines = file.readlines()
    x = []
    y = []
    for line in lines:
        xi = regexp_x.search(line)
        if xi:
            x.append(xi.group(1))
            y.append(regexp_y.search(line).group(1))
    file.close()
    return np.array(x, dtype=np.float32), np.array(y, dtype=np.float32)

def load_image(img_file):
    return imread(img_file)

img_df['x_y_coordinates'] = img_df['info_path'].map(read_and_parse_coordinates)
img_df['images'] = img_df['img_path'].map(load_image)
# read and parse the text files for coordinates

print(img_df.sample(2))

images_np = img_df['images'].as_matrix()
np.savez('spine_images',images_np)

# #Show a few sample images
# n_img = 6
# fig, m_axs = plt.subplots(1, n_img, figsize=(12, 4))
# for img,ax_ind in zip(img_df['images'].sample(n_img), range(6)):
#     m_axs[ax_ind].imshow(img)
#
# plt.show(fig)

# data_dir = os.path.join('..', 'input')

# info_file = os.path.normpath('C:\\Users\\smirnovm\\Documents\\Data\\Labeled_Spines\\spine000001\\spine_info000001.txt')
