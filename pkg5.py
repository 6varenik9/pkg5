import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QDoubleSpinBox, QDockWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

def midpoint_algorithm(segment, clip_rect):
    x1, y1 = segment[0]
    x2, y2 = segment[1]
    xmin, ymin, xmax, ymax = clip_rect

    def is_inside(x, y):
        return xmin <= x <= xmax and ymin <= y <= ymax

    if is_inside(x1, y1) and is_inside(x2, y2):
        return segment

    if not is_inside(x1, y1) and not is_inside(x2, y2):
        return None

    midpoint = ((x1 + x2) / 2, (y1 + y2) / 2)

    if abs(x1 - x2) < 1e-5 and abs(y1 - y2) < 1e-5:
        return midpoint if is_inside(*midpoint) else None

    if is_inside(x1, y1):
        clipped_end = midpoint_algorithm((midpoint, (x2, y2)), clip_rect)
        return (segment[0], clipped_end[0]) if clipped_end else None
    else:
        clipped_start = midpoint_algorithm(((x1, y1), midpoint), clip_rect)
        return (clipped_start[1], segment[1]) if clipped_start else None

def clip_segment_with_polygon(segment, polygon):
    x1, y1 = segment[0]
    x2, y2 = segment[1]

    def is_inside(p, edge):
        a, b = edge
        return (b[0] - a[0]) * (p[1] - a[1]) > (b[1] - a[1]) * (p[0] - a[0])

    def intersection(edge, s, e):
        a, b = edge
        dx = e[0] - s[0]
        dy = e[1] - s[1]
        edge_dx = b[0] - a[0]
        edge_dy = b[1] - a[1]

        denominator = edge_dx * dy - edge_dy * dx
        if abs(denominator) < 1e-5:
            return None

        ua = ((a[1] - s[1]) * dx - (a[0] - s[0]) * dy) / denominator
        return (a[0] + ua * edge_dx, a[1] + ua * edge_dy)

    clipped_segment = [segment[0], segment[1]]
    for i in range(len(polygon)):
        edge = (polygon[i], polygon[(i + 1) % len(polygon)])
        input_list = clipped_segment
        clipped_segment = []

        for j in range(len(input_list)):
            s = input_list[j - 1]
            e = input_list[j]
            if is_inside(e, edge):
                if not is_inside(s, edge):
                    clipped_segment.append(intersection(edge, s, e))
                clipped_segment.append(e)
            elif is_inside(s, edge):
                clipped_segment.append(intersection(edge, s, e))

        if len(clipped_segment) < 2:
            return None

    return clipped_segment[:2]

class ClippingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipping Algorithms")
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.clip_rect = (1, 1, 8, 8)
        self.polygon = [(2, 2), (6, 2), (7, 5), (5, 8), (3, 7)]
        self.segments = [((0, 0), (9, 9)), ((2, 7), (8, 3)), ((5, 1), (1, 9))]

        self.init_ui()
        self.plot()

    def init_ui(self):
        layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        midpoint_button = QPushButton("Midpoint Algorithm")
        polygon_button = QPushButton("Polygon Clipping")

        midpoint_button.clicked.connect(self.run_midpoint)
        polygon_button.clicked.connect(self.run_polygon)

        controls_layout.addWidget(midpoint_button)
        controls_layout.addWidget(polygon_button)

        layout.addWidget(self.canvas)
        layout.addLayout(controls_layout)
        self.setLayout(layout)

    def plot(self):
        self.ax.clear()

        xmin, ymin, xmax, ymax = self.clip_rect
        rect = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)]
        self.ax.plot(*zip(*rect), color='blue', label='Clip Rectangle')

        poly = Polygon(self.polygon, closed=True, edgecolor='green', fill=False, linewidth=2)
        self.ax.add_patch(poly)

        for segment in self.segments:
            x1, y1 = segment[0]
            x2, y2 = segment[1]
            self.ax.plot([x1, x2], [y1, y2], color='red', linestyle='--', label='Original Segment')

        self.ax.legend()
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.canvas.draw()

    def run_midpoint(self):
        self.ax.clear()
        self.plot()
        for segment in self.segments:
            result = midpoint_algorithm(segment, self.clip_rect)
            if result:
                x1, y1 = result[0]
                x2, y2 = result[1]
                self.ax.plot([x1, x2], [y1, y2], color='green', label='Clipped Segment')
        self.canvas.draw()

    def run_polygon(self):
        self.ax.clear()
        self.plot()
        for segment in self.segments:
            result = clip_segment_with_polygon(segment, self.polygon)
            if result:
                x1, y1 = result[0]
                x2, y2 = result[1]
                self.ax.plot([x1, x2], [y1, y2], color='purple', label='Clipped Segment')
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ClippingApp()
    main_window.show()
    sys.exit(app.exec_())
