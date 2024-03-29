import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import os.path as path
import scipy.io as sio
from PyQt5.QtWidgets import QApplication
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
    alignment = e.alignment

    # Mapping from image names to:
    #   frame_number => points that we want to pre-populate the viewer with.
    #   `None` for frame_number means that the points apply to all frames.
    if alignment.has_frame_values:
        raise NotImplementedError
    else:
        return {
            "S2AHiRes": {None: alignment["S2AHiRes"]["Sall"]},
            "Hi2LowResF": {None: alignment["S2AHiRes"]["Aall"]},
            "lowResFluor2BF": {None: alignment["Hi2LowResF"]["Aall"]},
        }


def save_mat_file(
    raw_data, output_folder, background_file=None, save_frame_value=False
):
    if background_file is not None:
        background = sio.loadmat(background_file)["backgroundImage"]
    else:
        background = np.uint8(0)

    point_mapping = defaultdict(lambda: defaultdict(list))
    # Mapping from image name we get from the UI to matlab structure names
    # (nested).
    image_name_to_matlab_names = {
        "S2AHiRes": [("S2AHiRes", "Sall"), ("Hi2LowResF", "Sall")],
        "Hi2LowResF": [("S2AHiRes", "Aall")],
        "lowResFluor2BF": [
            ("Hi2LowResF", "Aall"),
            ("lowResFluor2BF", "Aall"),
            ("lowResFluor2BF", "Sall"),
        ],
    }

    # All fields for each of the 3 matlab structure names above;
    # We do not populate t_concord/Rsegment.
    for img_name in image_name_to_matlab_names:
        point_mapping[img_name].setdefault("Aall", [])
        point_mapping[img_name].setdefault("Sall", [])
        point_mapping[img_name].setdefault("t_concord", [])
        point_mapping[img_name].setdefault("Rsegment", [])

    if save_frame_value:
        raise NotImplementedError

    for name, point_dict in raw_data:
        for img_name, inner_name in image_name_to_matlab_names[name]:
            for frame_number, points in point_dict.items():
                if points:
                    point_mapping[img_name][inner_name].extend(points)

    # TODO: Current matlab code is saving S2AHiRes.rect1/S2AHiRes.rect2
    # with hardcoded values. We do the same to conform to legacy format.
    point_mapping["S2AHiRes"]["rect1"] = np.array([1, 1, 512, 512]).astype(np.uint16)
    point_mapping["S2AHiRes"]["rect2"] = np.array([1, 513, 512, 512]).astype(np.uint16)

    point_mapping["background"] = background
    matlab_dict = {"alignments": point_mapping}
    file_name = path.join(output_folder, "alignments.mat")
    sio.savemat(file_name, matlab_dict)


def image_align(
    experiment, output_folder=None, background_file=None, save_frame_values=False
):
    output_folder = output_folder or experiment.folder_path
    data = process_images(experiment)

    app = QApplication(sys.argv)

    # what to pre-populate the viewer with; Can be None
    # format: dict of dicts mapping
    #   image name => point_dict
    # where point_dict is a mapping from frame number (0-indexed)
    # to list of points

    n_frames = list(data.values())[0].shape[-1]
    existing_points = process_coordinates(experiment, n_frames=n_frames)

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

    def on_close(save):
        if save:
            save_mat_file(
                viewer.points.items(), output_folder, background_file, save_frame_values
            )

    viewer.closed.connect(on_close)
    viewer.show()
    app.exec()
