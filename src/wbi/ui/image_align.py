from itertools import islice
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication
from wbi.ui.QtImageStackViewer import QtImageStackViewer


def process_images(e):
    himag_images = e.median_images_himag()
    lomag_images = e.median_images_lomag()

    min_count = min(
        len(list(e.median_images_himag())), len(list(e.median_images_lomag()))
    )
    processed_images = {"image1": [], "image2": [], "image3": []}

    for himag, lomag in zip(
        islice(himag_images, min_count), islice(lomag_images, min_count)
    ):
        processed_images["image1"].append(himag[: himag.shape[0] // 2, :])
        processed_images["image2"].append(himag[himag.shape[0] // 2 :, :])
        processed_images["image3"].append(lomag)

    for key, img in processed_images.items():
        normalized_image = img / np.max(img)
        cm = plt.get_cmap("viridis")
        colored_images = np.array([cm(frame)[:, :, :3] for frame in normalized_image])
        colored_images_uint8 = (colored_images * 255).astype(np.uint8)
        processed_images[key] = np.transpose(colored_images_uint8, (1, 2, 3, 0))

    return processed_images


def image_align(experiment):
    data = process_images(experiment)

    app = QApplication(sys.argv)

    # what to prepopulate the viewer with; Can be None
    # format: dict of dicts mapping
    #   image name => point_dict
    # where point_dict is a mapping from frame number (0-indexed)
    # to list of points
    existing_points = {
        "image1": {0: ((20, 25), (36.32, 40.11)), 1: ((100.52, 80.5),), 3: ((85, 92),)},
        "image2": {0: ((74, 31), (53, 64.113)), 1: ((32.53, 40.5),), 3: ((95, 66),)},
        "image3": {0: ((31, 22), (22, 20)), 1: ((63.1, 53.22),), 3: ((76, 42),)},
    }
    viewer = QtImageStackViewer(data, points=existing_points)

    def get_points():
        print("selected points:")
        for name, point_dict in viewer.points.items():
            print(f"image {name}:")
            for frame_number, points in point_dict.items():
                print(f"  frame {frame_number}: {points}")

    viewer.destroyed.connect(get_points)

    viewer.show()
    sys.exit(app.exec())
