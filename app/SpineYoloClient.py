from __future__ import print_function
import requests
import json
import numpy as np


class SpineYoloClient:

    def __init__(self):
        self.server_address = 'http://localhost:5000'

    def test(self):
        img_path = 'C:\\Users\\smirnovm\\Documents\\Data\\yolo_spine_training\\images\\000001.jpg'
        scale = 9.0
        test_url = self.server_address + '/predict-local/{}/{}'.format(img_path, scale)
        response = requests.post(test_url)
        print(json.loads(response.text))

    def find_spines(self, img_path, scale):
        url = self.server_address + '/predict-local/{}/{}'.format(img_path, scale)
        response = requests.post(url)
        return np.array(json.loads(response.text))
