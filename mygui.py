# File: main.py

import sys

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QMessageBox, QLabel, QWidget, QVBoxLayout, QSpinBox, QComboBox)
from PySide2.QtCore import QFile, Slot

# Crazy mlt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

from functools import partial

app = QApplication(sys.argv)
# drwa widget

global_fig = Figure(figsize=(5, 4), dpi=100)
static_canvas_widget = FigureCanvasQTAgg(global_fig)
plotter = global_fig.add_subplot(1, 1, 1)

ui_file = QFile("QtGui.ui")
ui_file.open(QFile.ReadOnly)

loader = QUiLoader()
window = loader.load(ui_file)

# ui -> qt -> layout

plt_lay = QVBoxLayout()
plt_lay.addWidget(static_canvas_widget)
plt_lay.addWidget(NavigationToolbar(static_canvas_widget, window))


class Core():
    def __init__(self, a, b, pi, so, theta, material, so_p=0, theta_p=0):
        self.a = a  # inner radius
        self.b = b  # outter radius
        self.pi = pi  # ->NOTICE<- this might also need to distinguish between different materials
        self.material = material

        # ---> NOTE <----
        # if material type is *soil*, the cohension will not change after the yield point
        # only theta, q, and co are used

        # if material type is *rock*, the cohension will change
        #   when (a <  r < rho) -> plastic (after  yield) -> paramaters: q, co ,theta
        #   when (rho< r < b  ) -> elastic (before yield) -> paramaters: q',co',theta' < notice the prime

        # >>>> paramaters initilization <<<<
        if self.material == "soil":
            self.co = 2 * so
            self.theta = np.radians(theta)
            self.po = self.co
            self.q = (1 + np.sin(self.theta)) / (1 - np.sin(self.theta))
        elif self.material == "rock":
            self.co = 2 * so
            self.theta = np.radians(theta)
            self.q = (1 + np.sin(self.theta)) / (1 - np.sin(self.theta))

            self.co_p = 2 * so_p
            self.theta_p = np.radians(theta_p)
            self.q_p = (1 + np.sin(self.theta_p)) / (1 - np.sin(self.theta_p))

            self.po = self.co_p

        # >>>> calculation of yield point & B  <<<<

        if self.material == "soil":
            # equation (9.28) & (9.29)
            self.rho = self.a * (2 * (self.po * (self.q - 1) + self.co) / (
                    (self.pi * (self.q - 1) + self.co) * (self.q + 1))) ** (1 / (self.q - 1))
            self.B = (self.rho ** 2) * (self.co + self.po * (self.q - 1)) / (self.q + 1)

        elif self.material == "rock":
            # equation (9.35) & (9.36) 0> care for difference between "primes"
            self.rho = self.a * (((2 * self.po - self.co_p) * (1 - self.q) - self.co * (1 + self.q_p)) / (
                    (self.pi * (1 - self.q) - self.co) * (1 + self.q_p))) ** (1 / (self.q - 1))
            self.B = (self.rho ** 2) * (self.co_p + self.po * (self.q_p - 1)) / (self.q_p + 1)
        else:
            print("wtf???")

    # =============================================================================

    def radical_stress(self, r):
        if self.a <= r and r < self.rho:
            return self.co / (1 - self.q) + (self.pi - self.co / (1 - self.q)) * (r / self.a) ** (self.q - 1)
        elif r > self.rho:
            return self.po - self.B / (r ** 2)
        else:
            return np.nan

    def tangential_stress(self, r):
        if self.a <= r and r < self.rho:
            return self.co / (1 - self.q) + self.q * (self.pi - self.co / (1 - self.q)) * (r / self.a) ** (self.q - 1)
        elif r > self.rho:
            return self.po + self.B / (r ** 2)
        else:
            return np.nan

    def plot(self):
        plotter.clear()
        # plotting-related
        # ps:code below suck, cuz matplotlib use similar api of MATLAB which have bad plotting functions.....
        x_a_rho = np.linspace(self.a, self.rho, 500)
        x_rho_b = np.linspace(self.rho, self.b, 500)

        rsline = plotter.plot(x_a_rho, [self.radical_stress(r)/self.pi for r in x_a_rho], "b",
                              x_rho_b, [self.radical_stress(r)/self.pi for r in x_rho_b], "b",
                              )
        rsline[0].set_label("Radical stress")

        tsline = plotter.plot(x_a_rho, [self.tangential_stress(r)/self.pi for r in x_a_rho], "g",
                              x_rho_b, [self.tangential_stress(r)/self.pi for r in x_rho_b], "g",
                              )
        tsline[0].set_label("Tangential stress")

        plotter.set_xlabel(r'radius r (m)')
        plotter.set_ylabel(r'Relative Stress to the stress at inner radius ')

        # Styling the plot
        plotter.grid()
        plotter.legend()
        plotter.figure.canvas.draw()


gui_parts_name = [
    "ui_a",
    "ui_b",
    "ui_pi",
    "ui_so",
    "ui_so_p",
    "ui_theta_p",
    "ui_theta"]

[ui_a, ui_b, ui_pi, ui_so, ui_so_p, ui_theta_p, ui_theta] = \
    [window.findChild(QSpinBox, part_name) for part_name in gui_parts_name]

ui_type = window.findChild(QComboBox, "ui_type")
ui_plt = window.findChild(QWidget, "ui_plt_region")
#ui_plt_btn = window.findChild(QPushButton, "ui_plot_pushbtn")

ui_so_p_label = window.findChild(QLabel, "ui_so_p_label")
ui_theta_p_label = window.findChild(QLabel, "ui_theta_p_label")

@Slot()
def ui_plot():
    Core(
        a=ui_a.value(),
        b=ui_b.value(),
        pi=ui_pi.value(),
        so=ui_so.value(),
        so_p=ui_so_p.value(),
        theta_p=ui_theta_p.value(),
        theta=ui_theta.value(),
        material=ui_type.itemText(ui_type.currentIndex())).plot()

@Slot()
def ui_plot_type_change():
    new_type = ui_type.itemText(ui_type.currentIndex())

    if new_type == "soil":
        ui_a.setProperty("value", 1)
        ui_b.setProperty("value", 10)
        ui_so.setProperty("value", 10)
        ui_pi.setProperty("value", 0)
        ui_theta.setProperty("value", 60)

        ui_so_p.hide()
        ui_theta_p.hide()
        ui_so_p_label.hide()
        ui_theta_p_label.hide()

    elif new_type == "rock":

        ui_so_p.show()
        ui_theta_p.show()
        ui_so_p_label.show()
        ui_theta_p_label.show()

        ui_a.setProperty("value", 1)
        ui_b.setProperty("value", 10)
        ui_pi.setProperty("value", 1)
        ui_so.setProperty("value", 0)
        ui_so_p.setProperty("value", 10)
        ui_theta_p.setProperty("value", 30)
        ui_theta.setProperty("value", 30)

    else:
        print("The internal QComboBox suck")


    ui_plot()


# TODO: there mush be some way to deal the SHIT below
ui_plot()
#ui_plt_btn.clicked.connect(ui_plot)

ui_a.valueChanged.connect(ui_plot)
ui_b.valueChanged.connect(ui_plot)
ui_pi.valueChanged.connect(ui_plot)
ui_so.valueChanged.connect(ui_plot)
ui_so_p.valueChanged.connect(ui_plot)
ui_theta.valueChanged.connect(ui_plot)
ui_theta_p.valueChanged.connect(ui_plot)

ui_type.currentIndexChanged.connect(ui_plot_type_change)

ui_plt.setLayout(plt_lay)




ui_file.close()
window.show()

msgBox=QMessageBox()
msgBox.setText("""Change the parameters to calculate relative stresses interactively for a circular hole in an elastic–brittle–plastic rock mass.""")
msgBox.exec()

# ===============================================================================
sys.exit(app.exec_())
