import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from QtImageStackViewer import QtImageStackViewer
from PIL import Image, ImageSequence


if __name__ == "__main__":

    # -------- Sample input data -------- #
    image = Image.open("sample_sequence.gif")
    _data = np.array(
        [np.array(frame.convert("RGB")) for frame in ImageSequence.Iterator(image)]
    )

    # Create 3 identical images from the data above, but with different colors
    data = np.stack([_data, _data, _data], axis=0)
    for i in range(3):
        all_except_i = [j for j in range(3) if j != i]
        data[i, ..., all_except_i] = 0

    data = data.transpose((0, 2, 3, 4, 1))

    # data needs to be in the shape (n_images, height, width, 3, n_frames)
    # and uint8 in dtype
    print("data shape:", data.shape)
    print("data type:", data.dtype)
    # -------- Sample input data -------- #

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
    viewer = QtImageStackViewer(data, points=existing_points)

    def get_points():
        print("selected points:")
        for image_index, points in enumerate(viewer.points):
            print(f"image {image_index}:")
            for frame_number, points in points.items():
                print(f"  frame {frame_number}: {points}")

    viewer.destroyed.connect(get_points)

    viewer.show()
    sys.exit(app.exec())
