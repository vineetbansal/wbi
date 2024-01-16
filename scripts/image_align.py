import cv2
import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from QtImageStackViewer import QtImageStackViewer
from wbi.experiment import Experiment

FOLDER = "/Users/aa9078/Documents/Projects/LeiferLab/Data/20231024_alignment_test/BrainScanner_20231018_143745/"


def process_images(e, target_shape, n_frames):
    himag_images = e.median_images_himag()
    lomag_images = e.median_images_lomag()

    processed_images = []

    for himag, lomag in zip(himag_images, lomag_images):
        red_channel = resize_or_pad(himag[: himag.shape[0] // 2, :], target_shape)
        green_channel = resize_or_pad(himag[himag.shape[0] // 2 :, :], target_shape)
        lomag = resize_or_pad(lomag, target_shape)
        processed_images.extend([red_channel, green_channel, lomag])

    processed_images = np.array(processed_images)
    n_images = len(processed_images)
    height, width = processed_images[0].shape

    transformed_images = np.zeros(
        (n_images, height, width, 3, n_frames), dtype=np.uint8
    )

    for i, img in enumerate(processed_images):
        img_expanded = np.expand_dims(img, axis=-1)

        channel_index = 0 if i % 2 == 0 else 1
        transformed_images[
            i, ..., channel_index, :
        ] = img_expanded  # Use 1 for green channel

    return transformed_images[::17]


def resize_or_pad(image, target_shape):
    height_ratio, width_ratio = (
        target_shape[0] / image.shape[0],
        target_shape[1] / image.shape[1],
    )

    ratio = min(height_ratio, width_ratio)

    resized_image = cv2.resize(
        image,
        (int(image.shape[1] * ratio), int(image.shape[0] * ratio)),
        interpolation=cv2.INTER_AREA,
    )
    pad_vert = target_shape[0] - resized_image.shape[0]
    pad_top, pad_bottom = pad_vert // 2, pad_vert - (pad_vert // 2)
    pad_horiz = target_shape[1] - resized_image.shape[1]
    pad_left, pad_right = pad_horiz // 2, pad_horiz - (pad_horiz // 2)
    padded_image = cv2.copyMakeBorder(
        resized_image,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0],
    )

    return padded_image


if __name__ == "__main__":
    e = Experiment(FOLDER)

    image = e.median_images_himag()

    _data = process_images(e, (512, 512), 1)

    app = QApplication(sys.argv)

    # what to prepopulate the viewer with; Can be None
    # format: list of dicts of the same size as data.shape[0],
    # where each dict is a mapping from frame number (0-indexed)
    # to list of points
    existing_points = [
        {0: ((20, 25), (36.32, 40.11)), 1: ((100.52, 80.5),), 3: ((85, 92),)},
        {0: ((74, 31), (53, 64.113)), 1: ((32.53, 40.5),), 3: ((95, 66),)},
        {0: ((31, 22), (22, 20)), 1: ((63.1, 53.22),), 3: ((76, 42),)},
    ]
    viewer = QtImageStackViewer(_data, points=existing_points)

    def get_points():
        print("selected points:")
        for image_index, points in enumerate(viewer.points):
            print(f"image {image_index}:")
            for frame_number, points in points.items():
                print(f"  frame {frame_number}: {points}")

    viewer.destroyed.connect(get_points)

    viewer.show()
    sys.exit(app.exec())
