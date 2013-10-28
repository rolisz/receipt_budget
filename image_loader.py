from __future__ import division
import copy
from SimpleCV.Features.Blob import Blob
from scipy import signal
from time import sleep
from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QApplication, QMainWindow, QWidget, QImage, QPainter, QPen, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QDialog
import sys
import SimpleCV
from SimpleCV import Image, ROI, FeatureSet
from SimpleCV.Color import Color
from SimpleCV.DrawingLayer import DrawingLayer
from SimpleCV.Features import Features
import cPickle
import numpy as np
import matplotlib.pyplot as plt
# from helper.qimage2ndarray import rgb2qimage, qimage2numpy
# from model.receipt import Receipt
from Expenses.helper.qimage2ndarray import rgb2qimage
from Expenses.model.receipt import Receipt


def smooth(x,window_len=11,window='hanning'):
    """
    http://wiki.scipy.org/Cookbook/SignalSmooth
    """
    if x.ndim != 1:
            raise ValueError, "smooth only accepts 1 dimension arrays."
    if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."
    if window_len<3:
            return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    s=np.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
            w=np.ones(window_len,'d')
    else:
            w=eval('np.'+window+'(window_len)')
    y=np.convolve(w/w.sum(),s,mode='same')
    return y[window_len:-window_len+1]



class MainWindow(QDialog):
    def __init__(self):
        QDialog.__init__(self, None)

        vbox = QVBoxLayout()
        self.setLayout(vbox)
        hbox = QHBoxLayout()

        self.labeled = QWidget(self)
        hbox.addWidget(self.labeled)
        self.labeled.setMinimumSize(1400, 600)
        btn = QPushButton("Load")
        btn.clicked.connect(self.load_image)
        vbox.addItem(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(btn)
        btn = QPushButton("Close")
        btn.clicked.connect(self.done_btn)
        hbox.addWidget(btn)
        btn = QPushButton("Next")
        btn.clicked.connect(self.next)
        hbox.addWidget(btn)
        vbox.addLayout(hbox)

        self.i = 1
        self.analyze_image("D:/AI/Bonuri/bonuri/bon1.jpg")


    def paintEvent(self, event):
        self.qp = QPainter()
        self.qp.begin(self)
        self.qp.drawImage(0, 0, self.img_orig)

        self.qp.drawImage(300, 0, self.img_straight)
        self.qp.drawImage(600, 0, self.cleaned)
        self.qp.drawImage(1000, 0, self.find_lines)
        self.qp.end()


    def load_image(self):
        file = QFileDialog.getOpenFileName(self, "Select Image", "D:\\AI\\Bonuri\\bonuri", "Images (*.png *.jpg)")
        if file:
            self.analyze_image(file)

    def analyze_image(self, file):
        rec = Receipt(str(file))
        self.img_orig = rgb2qimage(rec.oimg).scaled(200,600)
        self.img_straight = rgb2qimage(rec.simg).scaled(200,600)
        self.cleaned = rgb2qimage(rec.cimg).scaled(300,800)
        self.find_lines = rgb2qimage(rec.nimg).scaled(300,800)

        self.update()

    def done_btn(self):
        pass

    def next(self):
        self.i += 1
        self.analyze_image("D:/AI/Bonuri/bonuri/bon%d.jpg" %self.i)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()
    sys.exit()