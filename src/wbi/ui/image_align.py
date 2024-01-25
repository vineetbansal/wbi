from collections import defaultdict
import sys
import matplotlib.pyplot as plt
import numpy as np
import os.path as path
import scipy.io as sio
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

    channels = ("Aall", "Sall") if not a.has_frame_values else ("Aall2", "Sall2")
    points_mapping = {"S2AHiRes": {}, "Hi2LowResF": {}, "lowResFluor2BF": {}}

    channel_map = {
        ("S2AHiRes", channels[1]): "S2AHiRes",
        ("S2AHiRes", channels[0]): "Hi2LowResF",
        ("Hi2LowResF", channels[1]): "S2AHiRes",
        ("Hi2LowResF", channels[0]): "lowResFluor2BF",
        ("lowResFluor2BF", channels[0]): "lowResFluor2BF",
    }

    for img_key in list(points_mapping):
        for channel in channels:
            if img_key == "lowResFluor2BF" and channel == channels[1]:
                # This would map to the fourth image channel that is no longer in existence
                continue

            target_key = channel_map.get((img_key, channel))
            points_mapping[target_key] = defaultdict(list)
            data_points = a.data[img_key][channel]

            if not a.has_frame_values:
                points_mapping[target_key][None] = data_points
            else:
                for coords in data_points[:n_frames]:
                    frame_no = coords[2].astype(int)
                    point = np.ndarray.tolist(coords[:2])
                    if point not in points_mapping[target_key][frame_no]:
                        points_mapping[target_key][frame_no].append(point)

    return points_mapping


def save_mat_file(raw_data, output_folder, save_frame_value=False):
    point_channel = ("Aall", "Sall") if not save_frame_value else ("Aall2", "Sall2")
    formatted_data = {"S2AHiRes": {}, "Hi2LowResF": {}, "lowResFluor2BF": {}}
    reverse_coords_map = {
        "S2AHiRes": [("S2AHiRes", point_channel[1]), ("Hi2LowResF", point_channel[1])],
        "Hi2LowResF": [("S2AHiRes", point_channel[0])],
        "lowResFluor2BF": [
            ("Hi2LowResF", point_channel[0]),
            ("lowResFluor2BF", point_channel[0]),
        ],
    }

    for name, point_dict in raw_data:
        for img_name, inner_name in reverse_coords_map[name]:
            formatted_data[img_name][inner_name] = []
            for frame_number, points in point_dict.items():
                if len(points) != 0:
                    if not save_frame_value:
                        for y in points:
                            formatted_data[img_name][inner_name].append(y)
                    else:
                        for y in np.array([[x[0], x[1], frame_number] for x in points]):
                            formatted_data[img_name][inner_name].append(y)

    matlab_dict = {"alignments": formatted_data}
    file_name = path.join(output_folder, "alignments.mat")
    sio.savemat(file_name, matlab_dict)


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
        save_mat_file(viewer.points.items(), output_folder, save_frame_value=False)

    viewer.destroyed.connect(get_points)
    viewer.show()
    app.exec()
