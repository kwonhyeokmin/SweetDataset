import numpy as np
import skimage.io
import cv2
from matplotlib import pyplot as plt
import copy
import os
from abc import abstractmethod
import json
import glob
import time
from matplotlib.patches import Polygon


def search_file(directory, extension, recursive=False):
    files = []
    paths = []
    if recursive:
        for i, (path, _, filenames) in enumerate(os.walk(directory)):
            for file in filenames:
                if extension in file.split('.'):
                    files.append(file)
                    paths.append(os.path.join(path, file))
    else:
        search_path = os.path.join(directory, '*.{}'.format(extension))

        for file in glob.glob(search_path, recursive=True):
            files.append(os.path.basename(file))
            paths.append(file)
    return files, paths


class Dataset(object):
    def __init__(self):
        self.dataset_info = []
        self.video_info = []
        self.image_info = []
        self.keypoint_info = []
        self.image_ids = []

    @abstractmethod
    def load_data(self, dataset_dir):
        pass


class Dataset2d(Dataset):

    def _load_anno(self, ann_dir):
        _, json_path = search_file(ann_dir, 'json')
        for path in json_path:
            with open(path, 'r') as f:
                self.dataset_info.append(json.load(f))

    def add_image(self, source, image_no, path, **kwargs):
        self.image_ids.append(image_no)
        image_info = {'image_no': image_no, 'path': path, **source}
        image_info.update(kwargs)
        self.image_info.append(image_info)

    def load_data(self, dataset_dir):
        print('loading data into memory...')
        start_time = time.time()
        ANN_DIR = os.path.join(dataset_dir, 'annotations/2d')
        IMG_DIR = os.path.join(dataset_dir, 'images')
        self._load_anno(ANN_DIR)
        for dataset in self.dataset_info:
            for image in dataset['images']:
                source = copy.deepcopy(
                    next(iter([x for x in dataset['annotations'] if x['img_no'] == image['img_no']]), None))
                source.pop('img_no')
                self.add_image(source, image['img_no'], os.path.join(IMG_DIR, image['img_path']))
        print('Done (t={}s)'.format(round((time.time() - start_time) / 1000), 2))
        print('Image Count: {}'.format(len(self.image_ids)))

    def display_instance(self, image_no, show_bbox=False):
        try:
            image = self.load_image(image_no)
        except IOError:
            print('No instances to display')
        keypoints = self.load_keypoints(image_no).reshape(-1, 3)
        color = [116, 193, 0]
        line = [[keypoints[0], keypoints[1]], [keypoints[1], keypoints[2]], [keypoints[3], keypoints[4]],
                [keypoints[4], keypoints[5]], [keypoints[2], keypoints[6]], [keypoints[3], keypoints[6]],
                [keypoints[6], keypoints[7]], [keypoints[7], keypoints[8]], [keypoints[8], keypoints[9]],
                [keypoints[10], keypoints[11]], [keypoints[11], keypoints[12]], [keypoints[13], keypoints[14]],
                [keypoints[14], keypoints[15]], [keypoints[12], keypoints[8]], [keypoints[13], keypoints[8]]]
        for k in line:
            image = cv2.line(image, tuple(k[0][:2]), tuple(k[1][:2]), color, 3)
        for k in keypoints:
            image = cv2.circle(image, tuple(k[:2]), 10, color, -1)
        if show_bbox:
            bbox = self.load_bbox(image_no).reshape(-1, 2)
            image = cv2.rectangle(image, tuple(bbox[0]), tuple(bbox[1]), color, 3)
        plt.title('image_no: %d' % image_no)
        plt.axis('off')
        plt.imshow(image)

    def load_image(self, img_no):
        path = next(iter([x['path'] for x in self.image_info if x['image_no'] == img_no]), None)
        if path is not None:
            image = skimage.io.imread(path)
            # If has an alpha channel, remove it for consistency
            if image.shape[-1] == 4:
                image = image[..., :3]
            return image
        raise IOError('There is no image file that have img_no {}'.format(img_no, path))

    def load_keypoints(self, image_no):
        return np.array(
            next(iter([x['keypoints'] for x in self.image_info if x['image_no'] == image_no]), None)).astype(np.int)

    def load_bbox(self, image_no):
        return np.array(
            next(iter([x['bbox'] for x in self.image_info if x['image_no'] == image_no]), None)).astype(np.int)


if __name__ == '__main__':
    ROOT_DIR = '/Users/kwon/PycharmProjects/SweetDataset'
    DATA_DIR = os.path.join(ROOT_DIR, 'datasets')
    dataset = Dataset2d()
    dataset.load_data(DATA_DIR)
    dataset.display_instance(dataset.image_ids[0])
