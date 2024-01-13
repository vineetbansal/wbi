import numpy as np
from PyQt6.QtCore import Qt, QRectF, QPoint, QPointF, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainterPath, QMouseEvent, QPen, QFont
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QSizePolicy,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
)


class QtImageViewer(QGraphicsView):
    # Mouse button signals emit image scene (x, y) coordinates.
    # !!! For image (row, column) matrix indexing, row = y and column = x.
    # !!! These signals will NOT be emitted if the event is handled by an interaction such as zoom or pan.
    # !!! If aspect ratio prevents image from filling viewport, emitted position may be outside image bounds.
    leftMouseButtonPressed = pyqtSignal(float, float)
    leftMouseButtonReleased = pyqtSignal(int, float, float)
    middleMouseButtonPressed = pyqtSignal(float, float)
    middleMouseButtonReleased = pyqtSignal(float, float)
    rightMouseButtonPressed = pyqtSignal(float, float)
    rightMouseButtonReleased = pyqtSignal(int, float, float)
    leftMouseButtonDoubleClicked = pyqtSignal(float, float)
    rightMouseButtonDoubleClicked = pyqtSignal(float, float)

    # Emitted upon zooming/panning.
    viewChanged = pyqtSignal()

    # Emitted on mouse motion.
    # Emits mouse position over image in image pixel coordinates.
    # !!! setMouseTracking(True) if you want to use this at all times.
    mousePositionOnImageChanged = pyqtSignal(QPoint)

    def __init__(self, index, parent=None):
        QGraphicsView.__init__(self, parent)

        self.index = index

        # Image is displayed as a QPixmap in a QGraphicsScene attached to this QGraphicsView.
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Better quality pixmap scaling?
        # self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        # Displayed image pixmap in the QGraphicsScene.
        self._image = None

        # Image aspect ratio mode.
        #   Qt.IgnoreAspectRatio: Scale image to fit viewport.
        #   Qt.KeepAspectRatio: Scale image to fit inside viewport, preserving aspect ratio.
        #   Qt.KeepAspectRatioByExpanding: Scale image to fill the viewport, preserving aspect ratio.
        self.aspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio

        # Scroll bar behaviour.
        #   Qt.ScrollBarAlwaysOff: Never shows a scroll bar.
        #   Qt.ScrollBarAlwaysOn: Always shows a scroll bar.
        #   Qt.ScrollBarAsNeeded: Shows a scroll bar only when zoomed.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Interactions (set buttons to None to disable interactions)
        # !!! Events handled by interactions will NOT emit *MouseButton* signals.
        #     Note: regionZoomButton will still emit a *MouseButtonReleased signal on a click (i.e. tiny box).
        self.regionZoomButton = Qt.MouseButton.LeftButton  # Drag a zoom box.
        self.zoomOutButton = (
            Qt.MouseButton.RightButton
        )  # Pop end of zoom stack (double click clears zoom stack).
        self.panButton = Qt.MouseButton.MiddleButton  # Drag to pan.

        # Stack of QRectF zoom boxes in scene coordinates.
        # !!! If you update this manually, be sure to call updateViewer() to reflect any changes.
        self.zoomStack = []

        # Flags for active zooming/panning.
        self._isZooming = False
        self._isPanning = False

        # Store temporary position in screen pixels or scene units.
        self._pixelPosition = QPoint()
        self._scenePosition = QPointF()

        # Track mouse position. e.g., For displaying coordinates in a UI.
        # self.setMouseTracking(True)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.points = []

    def sizeHint(self):
        return QSize(900, 600)

    def hasImage(self):
        return self._image is not None

    def pixmap(self):
        if self.hasImage():
            return self._image.pixmap()
        return None

    def image(self):
        if self.hasImage():
            return self._image.pixmap().toImage()
        return None

    def setImage(self, image, points=[]):
        image = image.astype(np.float32)
        image -= image.min()
        image /= image.max()
        image *= 255
        image[image > 255] = 255
        image[image < 0] = 0
        image = image.astype(np.uint8)
        height, width, channels = image.shape
        assert channels == 3
        bytes = image.tobytes()
        qimage = QImage(bytes, width, height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        if self.hasImage():
            self._image.setPixmap(pixmap)
        else:
            self._image = self.scene.addPixmap(pixmap)

        for item in self.scene.items():
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsTextItem)):
                self.scene.removeItem(item)

        for i, (point_x, point_y) in enumerate(points, start=1):
            ellipse = QGraphicsEllipseItem(0, 0, 1, 1)
            ellipse.setPos(point_x, point_y)
            pen = QPen(Qt.GlobalColor.green)
            pen.setWidth(1)
            ellipse.setPen(pen)
            self.scene.addItem(ellipse)
            label = QGraphicsTextItem(str(i))
            label.setPos(point_x, point_y)
            label.setFont(QFont("Courier New", 5))
            self.scene.addItem(label)

        self.setSceneRect(QRectF(pixmap.rect()))  # Set scene size to image size.
        self.updateViewer()

    def updateViewer(self):
        """Show current zoom (if showing entire image, apply current aspect ratio mode)."""
        if not self.hasImage():
            return
        if len(self.zoomStack):
            self.fitInView(
                self.zoomStack[-1], self.aspectRatioMode
            )  # Show zoomed rect.
        else:
            self.fitInView(self.sceneRect(), self.aspectRatioMode)  # Show entire image.

    def clearZoom(self):
        if len(self.zoomStack) > 0:
            self.zoomStack = []
            self.updateViewer()
            self.viewChanged.emit()

    def resizeEvent(self, event):
        """Maintain current zoom on resize."""
        self.updateViewer()

    def mousePressEvent(self, event):
        """Start mouse pan or zoom mode."""
        # Ignore dummy events. e.g., Faking pan with left button ScrollHandDrag.
        dummyModifiers = Qt.KeyboardModifier(
            Qt.KeyboardModifier.ShiftModifier
            | Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        )
        if event.modifiers() == dummyModifiers:
            QGraphicsView.mousePressEvent(self, event)
            event.accept()
            return

        # Start dragging a region zoom box?
        if (self.regionZoomButton is not None) and (
            event.button() == self.regionZoomButton
        ):
            self._pixelPosition = event.pos()  # store pixel position
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            QGraphicsView.mousePressEvent(self, event)
            event.accept()
            self._isZooming = True
            return

        if (self.zoomOutButton is not None) and (event.button() == self.zoomOutButton):
            if len(self.zoomStack):
                self.zoomStack.pop()
                self.updateViewer()
                self.viewChanged.emit()
            event.accept()
            return

        # Start dragging to pan?
        if (self.panButton is not None) and (event.button() == self.panButton):
            self._pixelPosition = event.pos()  # store pixel position
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            if self.panButton == Qt.MouseButton.LeftButton:
                QGraphicsView.mousePressEvent(self, event)
            else:
                # ScrollHandDrag ONLY works with LeftButton, so fake it.
                # Use a bunch of dummy modifiers to notify that event should NOT be handled as usual.
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                dummyModifiers = Qt.KeyboardModifier(
                    Qt.KeyboardModifier.ShiftModifier
                    | Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.AltModifier
                    | Qt.KeyboardModifier.MetaModifier
                )
                dummyEvent = QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    QPointF(event.pos()),
                    Qt.MouseButton.LeftButton,
                    event.buttons(),
                    dummyModifiers,
                )
                self.mousePressEvent(dummyEvent)
            sceneViewport = (
                self.mapToScene(self.viewport().rect())
                .boundingRect()
                .intersected(self.sceneRect())
            )
            self._scenePosition = sceneViewport.topLeft()
            event.accept()
            self._isPanning = True
            return

        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.MouseButton.LeftButton:
            self.leftMouseButtonPressed.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middleMouseButtonPressed.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightMouseButtonPressed.emit(scenePos.x(), scenePos.y())

        QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Stop mouse pan or zoom mode (apply zoom if valid)."""
        # Ignore dummy events. e.g., Faking pan with left button ScrollHandDrag.
        dummyModifiers = Qt.KeyboardModifier(
            Qt.KeyboardModifier.ShiftModifier
            | Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        )
        if event.modifiers() == dummyModifiers:
            QGraphicsView.mouseReleaseEvent(self, event)
            event.accept()
            return

        # Finish dragging a region zoom box?
        if (self.regionZoomButton is not None) and (
            event.button() == self.regionZoomButton
        ):
            QGraphicsView.mouseReleaseEvent(self, event)
            zoomRect = (
                self.scene.selectionArea().boundingRect().intersected(self.sceneRect())
            )
            # Clear current selection area (i.e. rubberband rect).
            self.scene.setSelectionArea(QPainterPath())
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            # If zoom box is 3x3 screen pixels or smaller, do not zoom and proceed to process as a click release.
            zoomPixelWidth = abs(event.pos().x() - self._pixelPosition.x())
            zoomPixelHeight = abs(event.pos().y() - self._pixelPosition.y())
            if zoomPixelWidth > 3 and zoomPixelHeight > 3:
                if zoomRect.isValid() and (zoomRect != self.sceneRect()):
                    self.zoomStack.append(zoomRect)
                    self.updateViewer()
                    self.viewChanged.emit()
                    event.accept()
                    self._isZooming = False
                    return

        # Finish panning?
        if (self.panButton is not None) and (event.button() == self.panButton):
            if self.panButton == Qt.MouseButton.LeftButton:
                QGraphicsView.mouseReleaseEvent(self, event)
            else:
                # ScrollHandDrag ONLY works with LeftButton, so fake it.
                # Use a bunch of dummy modifiers to notify that event should NOT be handled as usual.
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                dummyModifiers = Qt.KeyboardModifier(
                    Qt.KeyboardModifier.ShiftModifier
                    | Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.AltModifier
                    | Qt.KeyboardModifier.MetaModifier
                )
                dummyEvent = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,
                    QPointF(event.pos()),
                    Qt.MouseButton.LeftButton,
                    event.buttons(),
                    dummyModifiers,
                )
                self.mouseReleaseEvent(dummyEvent)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            if len(self.zoomStack) > 0:
                sceneViewport = (
                    self.mapToScene(self.viewport().rect())
                    .boundingRect()
                    .intersected(self.sceneRect())
                )
                delta = sceneViewport.topLeft() - self._scenePosition
                self.zoomStack[-1].translate(delta)
                self.zoomStack[-1] = self.zoomStack[-1].intersected(self.sceneRect())
                self.viewChanged.emit()
            event.accept()
            self._isPanning = False
            return

        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.MouseButton.LeftButton:
            self.leftMouseButtonReleased.emit(self.index, scenePos.x(), scenePos.y())
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.middleMouseButtonReleased.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightMouseButtonReleased.emit(self.index, scenePos.x(), scenePos.y())

        QGraphicsView.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        """Show entire image."""
        # Zoom out on double click?
        if (self.zoomOutButton is not None) and (event.button() == self.zoomOutButton):
            self.clearZoom()
            event.accept()
            return

        scenePos = self.mapToScene(event.pos())
        if event.button() == Qt.MouseButton.LeftButton:
            self.leftMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())

        QGraphicsView.mouseDoubleClickEvent(self, event)

    def mouseMoveEvent(self, event):
        # Emit updated view during panning.
        if self._isPanning:
            QGraphicsView.mouseMoveEvent(self, event)
            if len(self.zoomStack) > 0:
                sceneViewport = (
                    self.mapToScene(self.viewport().rect())
                    .boundingRect()
                    .intersected(self.sceneRect())
                )
                delta = sceneViewport.topLeft() - self._scenePosition
                self._scenePosition = sceneViewport.topLeft()
                self.zoomStack[-1].translate(delta)
                self.zoomStack[-1] = self.zoomStack[-1].intersected(self.sceneRect())
                self.updateViewer()
                self.viewChanged.emit()

        scenePos = self.mapToScene(event.pos())
        if self.sceneRect().contains(scenePos):
            # Pixel index offset from pixel center.
            x = int(round(scenePos.x() - 0.5))
            y = int(round(scenePos.y() - 0.5))
            imagePos = QPoint(x, y)
        else:
            # Invalid pixel position.
            imagePos = QPoint(-1, -1)
        self.mousePositionOnImageChanged.emit(imagePos)

        QGraphicsView.mouseMoveEvent(self, event)

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.CrossCursor)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
