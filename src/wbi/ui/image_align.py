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


def process_coordinates(e, n_frames):
    a = e.alignment

    point_channel = ("Aall", "Sall") if not a.has_frame_values else ("Aall2", "Sall2")
    existing_points = {"S2AHiRes": {}, "Hi2LowResF": {}, "lowResFluor2BF": {}}

    coords_map = {
        ("S2AHiRes", point_channel[1]): "S2AHiRes",
        ("S2AHiRes", point_channel[0]): "Hi2LowResF",
        ("Hi2LowResF", point_channel[1]): "S2AHiRes",
        ("Hi2LowResF", point_channel[0]): "lowResFluor2BF",
        ("lowResFluor2BF", point_channel[0]): "lowResFluor2BF",
    }

    for img_key in list(existing_points):
        for channel in point_channel:
            if img_key == "lowResFluor2BF" and channel == point_channel[1]:
                # This would map to the fourth image channel that is no longer in existence
                continue
            if not a.has_frame_values:
                existing_points[coords_map[img_key, channel]] = {
                    None: a.data[img_key][channel]
                }
            else:
                for coords in a.data[img_key][channel][:n_frames]:
                    if (frame_no := coords[2].astype(int)) not in (
                        points_map := existing_points[coords_map[img_key, channel]]
                    ):
                        points_map[frame_no] = []

                    if not (
                        (point := np.ndarray.tolist(coords[:2])) in points_map[frame_no]
                    ):
                        points_map[frame_no].append(point)

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

    existing_points = process_coordinates(
        experiment, n_frames=data[next(iter(data))].shape[-1]
    )

    # Format of `points` argument:
    # existing_points = {
    #     "S2AHiRes": {
    #         0: ((20, 25), (36.32, 40.11)),
    #         1: ((100.52, 80.5),),
    #         None: ((85, 92),),
    #     },
    #     "Hi2LowResF": {
    #         0: ((74, 31), (53, 64.113)),
    #         1: ((32.53, 40.5),),
    #         None: ((95, 66),),
    #     },
    #     "lowResFluor2BF": {
    #         0: ((31, 22), (22, 20)),
    #         1: ((63.1, 53.22),),
    #         2: ((76, 42),),
    #     },
    # }
    viewer = QtImageStackViewer(data, points=existing_points)

    def get_points():
        formatted_data = "Image, Frame, Coords\n"
        for name, point_dict in viewer.points.items():
            for frame_number, points in point_dict.items():
                coords_str = "; ".join([f"({x}, {y})" for x, y in points])
                formatted_data += f"{name}, {frame_number}, {coords_str}\n"

        with open(path.join(output_folder, "alignment_points.txt"), "w") as file:
            file.write(formatted_data)

    viewer.destroyed.connect(get_points)
    viewer.show()
    app.exec()
