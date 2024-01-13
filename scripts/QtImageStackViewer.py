"""
Copied from
https://github.com/marcel-goldschen-ohm/PyQtImageViewer

Original Author: Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>

Simplified to strip out unneeded features and to add support for
point annotation and multiple images.
"""

from collections import defaultdict
import numpy as np
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QScrollBar,
    QMessageBox,
    QLabel,
    QToolBar,
)
from QtImageViewer import QtImageViewer


class QtImageStackViewer(QWidget):
    def __init__(self, image, points=None):
        QWidget.__init__(self)

        self.setWindowTitle("Image Alignment")

        assert (
            image.ndim == 5 and image.shape[3] == 3
        ), "image must be of shape (n_images, height, width, 3, n_frames)"
        assert image.dtype == "uint8", "image must be of dtype uint8"
        self.n_images, self.height, self.width, _, self.n_frames = image.shape
        self._image = image

        self._currentFrame = None
        self.points = [defaultdict(list) for _ in range(self.n_images)]
        if points is not None:
            for i, point in enumerate(points):
                for frame_number in range(self.n_frames):
                    self.points[i][frame_number] = list(point.get(frame_number, ()))

        self.imageViewers = [None] * self.n_images
        for i in range(self.n_images):
            imageViewer = QtImageViewer(index=i)
            imageViewer.setSizePolicy(
                QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            )
            imageViewer.setMouseTracking(True)
            imageViewer.mousePositionOnImageChanged.connect(self.updateLabel)
            imageViewer.leftMouseButtonReleased.connect(self.addPoint)
            imageViewer.rightMouseButtonReleased.connect(self.removePoint)
            self.imageViewers[i] = imageViewer

        self._scrollbar = None

        self.label = QLabel()
        font = self.label.font()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )

        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Orientation.Horizontal)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(10, 10))
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setStyleSheet("QToolBar { spacing: 2px; }")
        self.toolbar.addWidget(self.label)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(2)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(2)

        vbox.addLayout(hbox)
        for imageViewer in self.imageViewers:
            hbox.addWidget(imageViewer)
        vbox.addWidget(self.toolbar)

        self.updateViewers()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def addPoint(self, i, x, y):
        frame_number = self._scrollbar.value()
        self.points[i][frame_number].append((x, y))
        self.updateFrames()

    def removePoint(self, i, x, y):
        frame_number = self._scrollbar.value()

        min_distance = 10
        closest_point = None
        closest_distance = np.inf
        for existing_point in self.points[i][frame_number]:
            distance = np.hypot(x - existing_point[0], y - existing_point[1])
            if distance < min(closest_distance, min_distance):
                closest_distance = distance
                closest_point = existing_point

        if closest_point is not None:
            self.points[i][frame_number].remove(closest_point)

        self.updateFrames()

    def image(self):
        return self._image

    def setImage(self, im):
        self._image = im
        self.updateViewers()

    def updateViewers(self):
        scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        scrollbar.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )
        scrollbar.valueChanged.connect(self.updateFrames)
        self.layout().addWidget(scrollbar)
        scrollbar.setRange(0, self._image.shape[-1] - 1)
        scrollbar.setValue(0)
        self._scrollbar = scrollbar

        self.updateFrames()

    def updateFrames(self):
        frame_number = self._scrollbar.value()
        self._currentFrames = self._image[..., frame_number]
        frames_data = self._currentFrames.copy()
        for i, frame_data in enumerate(frames_data):
            self.imageViewers[i].setImage(
                frame_data, points=self.points[i][frame_number]
            )

        self.updateLabel()

    def updateLabel(self, imagePixelPosition=None):
        label = (
            str(self._scrollbar.value() + 1)
            + "/"
            + str(self._scrollbar.maximum() + 1)
            + "; "
        )
        label += str(self.width) + "x" + str(self.height)
        if imagePixelPosition is not None:
            x = imagePixelPosition.x()
            y = imagePixelPosition.y()
            if 0 <= x < self.width and 0 <= y < self.height:
                label += "; x=" + str(x) + ", y=" + str(y)
                if self._currentFrame is not None:
                    value = self._currentFrame[y, x]
                    label += ", value=" + str(value)
        self.label.setText(label)

    def validate_points(self):
        """
        Make sure that for each frame, the number of points in each image is the same.
        """
        for i in range(self.n_images):
            for frame_number, points in self.points[i].items():
                if len(points) != len(self.points[0][frame_number]):
                    raise RuntimeError(
                        f"Number of points in image {i+1} for frame {frame_number+1} is different from image 0."
                    )

        if len(self.points) == 0 or sum(len(v) for k, v in self.points[0].items()) < 8:
            raise RuntimeError(
                "Number of total selected points for each image is less than 8."
            )

    def show_ok_cancel_dialog(self, msg):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(
            f"There are errors in point selection.\n\n{msg}\n\nClick Ok to close without saving, or Cancel to go back and fix the errors."
        )
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Ok

    def closeEvent(self, event):
        try:
            self.validate_points()
        except RuntimeError as e:
            if self.show_ok_cancel_dialog(str(e)):
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
