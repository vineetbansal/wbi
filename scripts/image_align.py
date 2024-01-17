import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from QtImageStackViewer import QtImageStackViewer
from PIL import Image, ImageSequence


if __name__ == "__main__":

    # -------- Sample input data -------- #
    image = Image.open("sample_sequence.gif")
    _array = np.array(
        [np.array(frame.convert("RGB")) for frame in ImageSequence.Iterator(image)]
    )

    data = {}
    # Create 3 identical images from the data above, but with different colors
    for i, name in enumerate(("image1", "image2", "image3")):
        array = _array.copy()
        all_except_i = [j for j in range(3) if j != i]
        array[..., all_except_i] = 0
        array = array.transpose((1, 2, 3, 0))

        # clip second imag
        if name == "image2":
            array = array[:-100, :, :, :]

        # shorten time steps for 3rd image
        if name == "image3":
            array = array[:, :, :, 5:-5]

        data[name] = array

    # -------- Sample input data -------- #

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
