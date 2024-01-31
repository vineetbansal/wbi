"""
Copied from
https://github.com/marcel-goldschen-ohm/PyQtImageViewer

Original Author: Marcel Goldschen-Ohm <marcel.goldschen@gmail.com>

Simplified to strip out unneeded features and to add support for
point annotation and multiple images.
"""

from collections import defaultdict
import numpy as np
from PyQt5.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QScrollBar,
    QMessageBox,
    QLabel,
    QToolBar,
)
from PyQt5.QtGui import QIcon
from wbi.ui.QtImageViewer import QtImageViewer


class QtImageStackViewer(QWidget):

    # True: save, False: don't save
    closed = pyqtSignal(bool)

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
                # points that apply to all frames of this image
                self.points[name][None] = np.array(point.get(None, [])).tolist()
                for frame_number in range(self.n_frames):
                    self.points[name][frame_number] = np.array(
                        point.get(frame_number, [])
                    ).tolist()

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

        scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        scrollbar.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )
        scrollbar.valueChanged.connect(self.updateFrames)
        self.layout().addWidget(scrollbar)
        scrollbar.setRange(0, self.n_frames - 1)
        scrollbar.setValue(0)
        self._scrollbar = scrollbar

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateFrames(initial=True)

    def __len__(self):
        return len(self._images)

    def addPoint(self, name, x, y):
        frame_number = self._scrollbar.value()
        self.points[name][frame_number].append((x, y))
        self.updateFrames()

    def removePoint(self, name, x, y):
        frame_number = self._scrollbar.value()

        min_distance = 10
        closest_point = None
        closest_point_key = None
        closest_distance = np.inf

        for which in (None, frame_number):
            for existing_point in self.points[name][which]:
                distance = np.hypot(x - existing_point[0], y - existing_point[1])
                if distance < min(closest_distance, min_distance):
                    closest_distance = distance
                    closest_point = existing_point
                    closest_point_key = which

        if closest_point is not None:
            self.points[name][closest_point_key].remove(closest_point)
            self.updateFrames()
        else:
            self.imageViewers[name].zoomOut()

    def updateFrames(self, initial=False):
        frame_number = self._scrollbar.value()
        for i, (name, image) in enumerate(self._images.items()):
            all_frame_points = self.points[name][None]
            this_frame_points = self.points[name][frame_number]
            self.imageViewers[name].setImage(
                image[..., frame_number], points=all_frame_points + this_frame_points
            )

            # The last image is zoomed to a 512x512 region centered on the image
            # TODO: Very hacky! Find a better long term solution to this!
            if initial and i == len(self) - 1:
                image_viewer = self.imageViewers[name]
                image_viewer.zoomIn(
                    QRectF(
                        (image_viewer.width - 512) // 2,
                        (image_viewer.height - 512) // 2,
                        512,
                        512,
                    )
                )

        self.updateLabel()

    def updateLabel(self, name=None, imagePixelPosition=None):
        label = (
            "Frame "
            + str(self._scrollbar.value() + 1)
            + "/"
            + str(self._scrollbar.maximum() + 1)
            + "; "
        )

        label += " Points ("
        for _name in self._images:
            _n_points = sum([len(v) for v in self.points[_name].values()])
            label += f"{_name}: {_n_points}, "
        label = label[:-2]
        label += ")"

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

    def wheelEvent(self, a0):
        if self.n_frames > 1:
            i = self._scrollbar.value()
            if a0.angleDelta().y() < 0:
                if i < self.n_frames - 1:
                    self._scrollbar.setValue(i + 1)
                    self.updateFrames()
            else:
                if i > 0:
                    self._scrollbar.setValue(i - 1)
                    self.updateFrames()
            return

        QWidget.wheelEvent(self, a0)

    def leaveEvent(self, a0):
        self.updateLabel()

    def validate_points(self):
        """
        Make sure that for each frame, the number of points in each image is the same.
        """
        first_image_name = list(self._images.keys())[0]
        first_image_n_points = sum(
            len(v) for v in self.points[first_image_name].values()
        )

        for name in self._images:
            this_image_n_points = sum(len(v) for v in self.points[name].values())
            if first_image_n_points != this_image_n_points:
                raise RuntimeError(
                    f"Number of points in image {name} is different from {first_image_name}."
                )

        if (
            len(self.points[first_image_name]) == 0
            or sum(len(v) for k, v in self.points[first_image_name].items()) < 8
        ):
            raise RuntimeError(
                "Number of total selected points for each image is less than 8."
            )

    def closeEvent(self, a0):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Question)
        has_error = False
        try:
            self.validate_points()
        except RuntimeError as e:
            has_error = True
            msg_box.setText(
                f'There are errors in point selection.\n\n{e}\n\nClick "Discard" to discard all changes, or "Fix" to go back and fix the errors,'
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.button(QMessageBox.StandardButton.Yes).setText("Fix")
            msg_box.button(QMessageBox.StandardButton.No).setText("Discard")
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setText(
                'Point selection has passed validation. Click "Save" to save, "Discard" to discard all changes, or "Cancel" to back to the editing window.'
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel
            )
            msg_box.button(QMessageBox.StandardButton.Yes).setText("Save")
            msg_box.button(QMessageBox.StandardButton.No).setText("Discard")
            msg_box.button(QMessageBox.StandardButton.Cancel).setIcon(QIcon())
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Cancel:
            a0.ignore()
        elif has_error and result == QMessageBox.StandardButton.Yes:
            a0.ignore()
        else:
            self.closed.emit(result == QMessageBox.StandardButton.Yes)
            a0.accept()
