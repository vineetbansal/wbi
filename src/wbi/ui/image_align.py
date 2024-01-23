import sys
import matplotlib.pyplot as plt
import numpy as np
import os.path as path
from PyQt6.QtWidgets import QApplication
from wbi.ui.QtImageStackViewer import QtImageStackViewer


def process_images(e):
    himag_images = e.median_images_himag()
    lomag_images = e.median_images_lomag()

    processed_images = {"S2AHiRes": [], "Hi2LowResF": [], "lowResFluor2BF": []}

    for himag, lomag in zip(himag_images, lomag_images):
        processed_images["S2AHiRes"].append(himag[: himag.shape[0] // 2, :])
        processed_images["Hi2LowResF"].append(himag[himag.shape[0] // 2 :, :])
        processed_images["lowResFluor2BF"].append(lomag)

    for key, img in processed_images.items():
        normalized_image = img / np.max(img)
        cm = plt.get_cmap("viridis")
        colored_images = np.array([cm(frame)[:, :, :3] for frame in normalized_image])
        colored_images_uint8 = (colored_images * 255).astype(np.uint8)
        processed_images[key] = np.transpose(colored_images_uint8, (1, 2, 3, 0))

    return processed_images


def process_coordinates(e):
    alignment = e.alignment

    coords_map = {
        ("S2AHiRes", "Sall"): 0,
        ("S2AHiRes", "Aall"): 1,
        ("Hi2LowResF", "Sall"): 0,
        ("Hi2LowResF", "Aall"): 2,
        ("lowResFluor2BF", "Sall"): 3,  # TODO: We might not need this
        ("lowResFluor2BF", "Aall"): 2,
    }
    dtypes = ("Aall", "Sall")
    existing_points = {"S2AHiRes": [], "Hi2LowResF": [], "lowResFluor2BF": []}

    for val in existing_points.keys():
        existing_points[val] = {
            coords_map[val, dtype]: alignment.alignments[val][dtype] for dtype in dtypes
        }

    return existing_points


def image_align(experiment, output_folder=None):
    output_folder = output_folder or experiment.folder_path
    data = process_images(experiment)

    app = QApplication(sys.argv)

    # what to pre-populate the viewer with; Can be None
    # format: dict of dicts mapping
    #   image name => point_dict
    # where point_dict is a mapping from frame number (0-indexed)
    # to list of points
    existing_points = process_coordinates(experiment)
    viewer = QtImageStackViewer(data, points=existing_points)

    def get_points():
        formatted_data = "Image, Frame, Coords\n"
        for name, point_dict in viewer.points.items():
            for frame_number, points in point_dict.items():
                coords_str = "; ".join([f"({x}, {y})" for x, y in points])
                formatted_data += f"{name}, {frame_number}, {coords_str}\n"
        return formatted_data

    viewer.destroyed.connect(get_points)

    with open(path.join(output_folder, "alignment_points.txt"), "w") as file:
        file.write(get_points())
    viewer.show()
    app.exec()
