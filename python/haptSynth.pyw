#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Shunya Sato
# Author: Shunya Sato
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Recommend to run this with anaconda.

If you already have a version of anaconda installed, then create a new environment

conda create -n haptSynth Python=3.5 anaconda
source activate haptSynth
conda install pyserial

"""

import sys

import serial
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import seaborn as sns

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUiType

#from ui_haptSynth import Ui_MainWindow
Ui_MainWindow, QMainWindow = loadUiType('haptSynth.ui')

SAMPLING_RATE = 8000
FULL_SCALE_PEAK_VOLTAGE = 100.0

class SerialWorker(QtCore.QObject):
    # http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
    finished = QtCore.pyqtSignal()
    dataReady = QtCore.pyqtSignal(bytes)

    def __init__(self):
        super(SerialWorker, self).__init__()
        self.addr  = "COM1"
        self.baud  = 115200 #9600
        self.running = False
        self.port = None
        self.fname = "magi_log.txt"
        self.use_file = False

    @QtCore.pyqtSlot()
    def processA(self):
        print("SerialWorker.processA")
        if self.use_file:
            self.port = open(self.fname, "r")
        else:
            try:
                print("Try opening serial port: {}".format(self.addr))
                self.port = serial.Serial(self.addr,self.baud)
            except:
                print("Error opening serial port!")
                self.port = None
                return None
        print("opened port")
        while self.running:
            #print "SerialWorker is running"
            #line = self.port.readline()
            line = self.port.read()
            # line is bytes
            print("Received: {}".format(line))
            self.dataReady.emit(line)
            if self.use_file:
                time.sleep(0.01)

        print("SerialWorker finished processA")
        self.port.close()
        print("port is closed")
        self.finished.emit()

    def startRunning(self, portname):
        if portname == "FILE":
            self.use_file = True
        else:
            self.use_file = False
            self.addr = portname
        self.running = True

    def stopRunning(self):
        self.running = False

    def setFilename(self, fname):
        self.fname = fname

    def write(self, data):
        # data must be bytes
        if self.running:
            print("Writing: {}".format(data))
            self.port.write(data)

    def __del__(self):
        self.running = False
        if self.port:
            self.port.close()

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.running = False
        self.sampling_ms = 1/SAMPLING_RATE * 1000

        self.thread = QtCore.QThread()  # no parent!
        self.serialreader = SerialWorker()  # no parent!
        self.serialreader.moveToThread(self.thread)
        self.serialreader.dataReady.connect(self.processPayload)
        self.thread.started.connect(self.serialreader.processA)

        self.pushButton_open.clicked.connect(self.onPushButton_open)
        self.pushButton_run.clicked.connect(self.onPushButton_run)
        self.pushButton_update.clicked.connect(self.populatePort)
        self.spinBox_amp.valueChanged.connect(self.updateAmp)
        self.spinBox_freq.valueChanged.connect(self.updateFreq)
        #self.spinBox_freq.valueChanged.connect(self.updateDuration)
        self.spinBox_duration.valueChanged.connect(self.updateDuration)
        self.spinBox_up.valueChanged.connect(self.updateRampUp)
        self.spinBox_down.valueChanged.connect(self.updateRampDown)

        self.ready=False
        self.updateAmp(self.spinBox_amp.value())
        self.updateFreq(self.spinBox_freq.value())
        self.updateDuration(self.spinBox_duration.value())
        self.updateRampUp(self.spinBox_up.value())
        self.updateRampDown(self.spinBox_down.value())
        self.ready=True
        self.populatePort()

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.plot(np.random.rand(5))
        self.addmpl(self.fig)
        self.updatePlot()

    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                self.widget_mpl, coordinates=True)
        vbox.addWidget(self.toolbar)
        self.widget_mpl.setLayout(vbox)
        self.canvas.draw()

    def plot_synth(self, ax, sampling_ms, amp, freq, duration, rampup, rampdown):
        ax.cla()
        x_ramp_up = np.arange(0, rampup+sampling_ms, sampling_ms)
        x_sin = np.arange(rampup, duration+sampling_ms, sampling_ms)
        x_ramp_down = np.arange(duration, duration+rampdown+sampling_ms, sampling_ms)
        if rampup == 0:
            y_ramp_up = np.array([1])
        else:
            y_ramp_up = 1/rampup*x_ramp_up * np.sin(2*np.pi*x_ramp_up*0.001*freq)
        y_sin = np.sin(2*np.pi*x_sin*0.001*freq)
        if rampdown == 0:
            y_ramp_down = np.array([1])
        else:
            y_ramp_down = ((-1/(rampdown))*(x_ramp_down-duration)+1)*np.sin(2*np.pi*x_ramp_down*0.001*freq)
        ax.plot(x_ramp_up, amp*y_ramp_up, label='ramp up')
        ax.plot(x_sin, amp*y_sin, label="body")
        ax.plot(x_ramp_down, amp*y_ramp_down, label='ramp down')
        ax.set_xlabel("time(ms)")
        ax.set_ylabel("Amplitude(V)")
        ax.set_title("waveform")
        #ax.legend()
        ax.get_figure().tight_layout()
        self.canvas.draw()

    def updatePlot(self):
        if self.ready:
            amp = float(self.lineEdit_amp.text())
            freq = float(self.lineEdit_freq.text())
            duration = float(self.lineEdit_duration.text())
            rampup = int(self.lineEdit_up.text())
            rampdown = int(self.lineEdit_down.text())
            self.plot_synth(self.ax, self.sampling_ms, amp, freq, duration, rampup, rampdown)
            if self.checkBox_continuous.isChecked():
                self.onPushButton_run()

    def onPushButton_open(self):
        if not self.running:
            print("Start running!")
            self.serialreader.startRunning(str(self.comboBox_serial.currentText()))
            self.thread.start()
            self.running = True
            self.pushButton_open.setText("CLOSE")

        else:
            print("Stop running.")
            self.serialreader.stopRunning()
            self.thread.quit()
            self.running = False
            self.pushButton_open.setText("OPEN")

    def processPayload(self, payloadBytes):
        """
        Receive QString payload
        """
        #convert QString payload to Python String
        #payload = payloadBytes.decode('latin-1')
        payload = payloadBytes.decode("utf-8")
        # insert at end
        self.textBrowser_log.moveCursor(QtGui.QTextCursor.End)
        self.textBrowser_log.insertPlainText(payload)
        # append with implicit new line
        #self.textBrowser_log.append(payload.strip())
        #if self.checkBox_autoscroll.isChecked():
        #    self.textBrowser_log.moveCursor(QtGui.QTextCursor.End)

    def onPushButton_run(self):
        #self.port.write("hi¥n")
        if self.running:
            #self.serialreader.write('Hello from Python\r\n'.encode('latin-1'))
            #self.serialreader.write(bytes.fromhex('F1d2'))
            msg = self.composeMessage()
            self.serialreader.write(msg)

    def updateAmp(self, value):
        peak_voltage = value / 255. * FULL_SCALE_PEAK_VOLTAGE
        self.lineEdit_amp.setText("{:0.1f}".format(peak_voltage))
        self.updatePlot()

    def updateFreq(self, value):
        sinusoid_frequency_hz = 7.8125 * value
        self.lineEdit_freq.setText("{:0.1f}".format(sinusoid_frequency_hz))
        if self.lineEdit_duration.text():
            current_duration_ms = float(self.lineEdit_duration.text())
            new_cycles = int(np.round(current_duration_ms / 1000 * sinusoid_frequency_hz))
            self.spinBox_duration.setValue(new_cycles)

    def updateDuration(self, value):
        value = self.spinBox_duration.value()
        duration_ms = 1000 * value / (7.8125 * self.spinBox_freq.value())
        self.lineEdit_duration.setText("{:0.1f}".format(duration_ms))
        up_text = self.lineEdit_up.text()
        if up_text != '':
            if duration_ms < float(up_text):
                up_val = int(duration_ms / 32)
                self.spinBox_up.setValue(up_val)
        self.updatePlot()

    def updateRampUp(self, value):
        rampUp_ms = 32 * value
        duration_ms = float(self.lineEdit_duration.text())
        if duration_ms > rampUp_ms:
            self.lineEdit_up.setText("{}".format(rampUp_ms))
        else:
            value = int(duration_ms / 32)
            self.spinBox_up.setValue(value)
        self.updatePlot()

    def updateRampDown(self, value):
        rampDown_ms = 32 * value
        self.lineEdit_down.setText("{}".format(rampDown_ms))
        self.updatePlot()

    def composeMessage(self):
        ampBytes = bytes([self.spinBox_amp.value()])
        freqBytes = bytes([self.spinBox_freq.value()])
        durationBytes = bytes([self.spinBox_duration.value()])
        upInt = self.spinBox_up.value()
        downInt = self.spinBox_down.value()
        envelopeBytes = bytes([(upInt<<4)+downInt])
        msg = ampBytes + freqBytes + durationBytes + envelopeBytes
        return msg

    def populatePort(self):
        self.comboBox_serial.clear()
        serials = []
#        import serial.tools.list_ports
#        #print list(serial.tools.list_ports.comports())
#        serials += list(serial.tools.list_ports.comports())
#        print(serials)
#        for device in serials:
#            self.comboBox_serial.addItem(device[0])
        self.comboBox_serial.addItem("/dev/cu.usbmodem1411")
        # select last one as default
        nports = self.comboBox_serial.count()
        if nports != 0:
            self.comboBox_serial.setCurrentIndex(nports-1)

    def __del__(self):
        # make sure serial is closed.
        #super(MainWindow, self).__del__(parent)
        self.serialreader.stopRunning()
        self.thread.quit()

    def closeEvent(self, event):
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("PiezoHapt Synth")
    form = MainWindow()
    form.show()
    app.exec_()
