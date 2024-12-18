import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QPainter

class Segment:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

class ClippingWindow:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin, self.ymin, self.xmax, self.ymax = xmin, ymin, xmax, ymax


def midpoint_clip(segment, window):
    def is_point_inside(x, y):
        return window.xmin <= x <= window.xmax and window.ymin <= y <= window.ymax

    x1, y1, x2, y2 = segment.x1, segment.y1, segment.x2, segment.y2
    clipped_points = []

    if is_point_inside(x1, y1) and is_point_inside(x2, y2):
        return [(x1, y1), (x2, y2)]
    
   
    def intersect(x1, y1, x2, y2, edge):
        if edge == "left":
            return window.xmin, y1 + (y2 - y1) * (window.xmin - x1) / (x2 - x1)
        if edge == "right":
            return window.xmax, y1 + (y2 - y1) * (window.xmax - x1) / (x2 - x1)
        if edge == "bottom":
            return x1 + (x2 - x1) * (window.ymin - y1) / (y2 - y1), window.ymin
        if edge == "top":
            return x1 + (x2 - x1) * (window.ymax - y1) / (y2 - y1), window.ymax

    if x1 < window.xmin:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "left")
        clipped_points.append((x_intersect, y_intersect))
    if x2 < window.xmin:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "left")
        clipped_points.append((x_intersect, y_intersect))

    if x1 > window.xmax:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "right")
        clipped_points.append((x_intersect, y_intersect))
    if x2 > window.xmax:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "right")
        clipped_points.append((x_intersect, y_intersect))

    if y1 < window.ymin:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "bottom")
        clipped_points.append((x_intersect, y_intersect))
    if y2 < window.ymin:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "bottom")
        clipped_points.append((x_intersect, y_intersect))

    if y1 > window.ymax:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "top")
        clipped_points.append((x_intersect, y_intersect))
    if y2 > window.ymax:
        x_intersect, y_intersect = intersect(x1, y1, x2, y2, "top")
        clipped_points.append((x_intersect, y_intersect))

    return clipped_points
    
def sutherland_hodgman_clip(polygon, window):
    def inside(p, edge):
        if edge == "left":
            return p.x() >= window.xmin
        if edge == "right":
            return p.x() <= window.xmax
        if edge == "bottom":
            return p.y() >= window.ymin
        if edge == "top":
            return p.y() <= window.ymax

    def intersection(p1, p2, edge):
        if edge == "left":
            return QPointF(window.xmin, p1.y() + (p2.y() - p1.y()) * (window.xmin - p1.x()) / (p2.x() - p1.x()))
        if edge == "right":
            return QPointF(window.xmax, p1.y() + (p2.y() - p1.y()) * (window.xmax - p1.x()) / (p2.x() - p1.x()))
        if edge == "bottom":
            return QPointF(p1.x() + (p2.x() - p1.x()) * (window.ymin - p1.y()) / (p2.y() - p1.y()), window.ymin)
        if edge == "top":
            return QPointF(p1.x() + (p2.x() - p1.x()) * (window.ymax - p1.y()) / (p2.y() - p1.y()), window.ymax)

    clipped_polygon = polygon
    for edge in ["left", "right", "bottom", "top"]:
        input_polygon = clipped_polygon
        clipped_polygon = []
        if len(input_polygon) == 0:
            break
        p1 = input_polygon[-1]
        for p2 in input_polygon:
            if inside(p2, edge):
                if not inside(p1, edge):
                    clipped_polygon.append(intersection(p1, p2, edge))
                clipped_polygon.append(p2)
            elif inside(p1, edge):
                clipped_polygon.append(intersection(p1, p2, edge))
            p1 = p2
    return clipped_polygon

class SegmentItem(QGraphicsItem):
    def __init__(self, segment, color):
        super().__init__()
        self.segment = segment
        self.color = color

    def boundingRect(self):
        return QRectF(self.segment.x1, self.segment.y1, self.segment.x2 - self.segment.x1, self.segment.y2 - self.segment.y1)

    def paint(self, painter, option, widget):
        painter.setPen(QPen(self.color, 2))
        painter.drawLine(self.segment.x1, self.segment.y1, self.segment.x2, self.segment.y2)

class ClippingWindowItem(QGraphicsItem):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def boundingRect(self):
        return QRectF(self.window.xmin, self.window.ymin, self.window.xmax - self.window.xmin, self.window.ymax - self.window.ymin)

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.red, 2))
        painter.setBrush(QBrush(Qt.transparent))
        painter.drawRect(self.window.xmin, self.window.ymin, self.window.xmax - self.window.xmin, self.window.ymax - self.window.ymin)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Алгоритмы отсечения")
        self.setGeometry(100, 100, 800, 600)

        scene = QGraphicsScene(self)
        self.view = QGraphicsView(scene)
        self.setCentralWidget(self.view)

        self.segments = [
            Segment(50, 50, 200, 200),
            Segment(100, 100, 250, 50),
            Segment(300, 300, 350, 350)
        ]
        self.clipping_window = ClippingWindow(100, 100, 400, 400)

        self.window_item = ClippingWindowItem(self.clipping_window)
        scene.addItem(self.window_item)

        for seg in self.segments:
            segment_item = SegmentItem(seg, Qt.blue)
            scene.addItem(segment_item)

        self.clipped_segments = []
        for seg in self.segments:
            clipped = midpoint_clip(seg, self.clipping_window)
            for point in clipped:
                self.clipped_segments.append((point[0], point[1]))

        polygon = [QPointF(50, 50), QPointF(200, 50), QPointF(200, 200), QPointF(50, 200)]
        clipped_polygon = sutherland_hodgman_clip(polygon, self.clipping_window)

        self.view.setSceneRect(scene.itemsBoundingRect())
        self.view.centerOn(self.view.sceneRect().center())

        self.show()

    def closeEvent(self, event):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())