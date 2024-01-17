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
    def __init__(self, images, points=None):
        QWidget.__init__(self)

        self.setWindowTitle("Image Alignment")

        for name, image in images.items():
            assert (
                image.ndim == 4 and image.shape[2] == 3
            ), "image must be of shape (height, width, 3, n_frames)"
            assert image.dtype == "uint8", "image must be of dtype uint8"
        self.n_images = len(images)
        self.n_frames = min(image.shape[-1] for image in images.values())
        self._images = images.copy()

        self._currentFrame = None
        self.points = {name: defaultdict(list) for name in self._images}
        if points is not None:
            for name, point in points.items():
                for frame_number in range(self.n_frames):
                    self.points[name][frame_number] = list(point.get(frame_number, ()))

        self.imageViewers = {}
        for name in self._images:
            imageViewer = QtImageViewer(name=name)
            imageViewer.setSizePolicy(
                QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            )
            imageViewer.setMouseTracking(True)
            imageViewer.mousePositionOnImageChanged.connect(self.updateLabel)
            imageViewer.leftMouseButtonReleased.connect(self.addPoint)
            imageViewer.rightMouseButtonReleased.connect(self.removePoint)
            self.imageViewers[name] = imageViewer

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
        for imageViewer in self.imageViewers.values():
            hbox.addWidget(imageViewer)
        vbox.addWidget(self.toolbar)

        self.updateViewers()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def addPoint(self, name, x, y):
        frame_number = self._scrollbar.value()
        self.points[name][frame_number].append((x, y))
        self.updateFrames()

    def removePoint(self, name, x, y):
        frame_number = self._scrollbar.value()

        min_distance = 10
        closest_point = None
        closest_distance = np.inf
        for existing_point in self.points[name][frame_number]:
            distance = np.hypot(x - existing_point[0], y - existing_point[1])
            if distance < min(closest_distance, min_distance):
                closest_distance = distance
                closest_point = existing_point

        if closest_point is not None:
            self.points[name][frame_number].remove(closest_point)

        self.updateFrames()

    def updateViewers(self):
        scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        scrollbar.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )
        scrollbar.valueChanged.connect(self.updateFrames)
        self.layout().addWidget(scrollbar)
        scrollbar.setRange(0, self.n_frames - 1)
        scrollbar.setValue(0)
        self._scrollbar = scrollbar

        self.updateFrames()

    def updateFrames(self):
        frame_number = self._scrollbar.value()
        for name, image in self._images.items():
            self.imageViewers[name].setImage(
                image[..., frame_number], points=self.points[name][frame_number]
            )

        self.updateLabel()

    def updateLabel(self, name=None, imagePixelPosition=None):
        label = (
            str(self._scrollbar.value() + 1)
            + "/"
            + str(self._scrollbar.maximum() + 1)
            + "; "
        )
        if name is not None and imagePixelPosition is not None:
            x = imagePixelPosition.x()
            y = imagePixelPosition.y()
            if (
                0 <= x < self._images[name].shape[1]
                and 0 <= y < self._images[name].shape[0]
            ):
                label += "; x=" + str(x) + ", y=" + str(y)
                if self._currentFrame is not None:
                    value = self._currentFrame[y, x]
                    label += ", value=" + str(value)
        self.label.setText(label)

    def wheelEvent(self, event):
        if self.n_frames > 1:
            i = self._scrollbar.value()
            if event.angleDelta().y() < 0:
                if i < self.n_frames - 1:
                    self._scrollbar.setValue(i + 1)
                    self.updateFrames()
            else:
                if i > 0:
                    self._scrollbar.setValue(i - 1)
                    self.updateFrames()
            return

        QWidget.wheelEvent(self, event)

    def leaveEvent(self, event):
        self.updateLabel()

    def validate_points(self):
        """
        Make sure that for each frame, the number of points in each image is the same.
        """
        first_image_name = list(self._images.keys())[0]
        for name in self._images:
            for frame_number, points in self.points[name].items():
                if len(points) != len(self.points[first_image_name][frame_number]):
                    raise RuntimeError(
                        f"Number of points in image {name} for frame {frame_number+1} is different from image 0."
                    )

        if (
            len(self.points[first_image_name]) == 0
            or sum(len(v) for k, v in self.points[first_image_name].items()) < 8
        ):
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
