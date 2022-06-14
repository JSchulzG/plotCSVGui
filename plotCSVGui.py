import sys
import os
from pathlib import Path
from matplotlib.pyplot import tight_layout
import pandas
import datetime
from scipy.signal import argrelextrema
import numpy as np


from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QApplication, QStackedWidget, QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QTimer

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.subplots(3, sharex=True, gridspec_kw={'hspace': 0})
        super(MplCanvas, self).__init__(fig)


class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.ui = self.load_ui()
        self.pushButton.clicked.connect(self.plot)
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.sc, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)
        self.widgetPlot.setLayout(layout)

    def load_ui(self):
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        loadUi(path, self)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","CSV Files (*.csv)", options=options)
        if fileName:
            print(fileName)
            return fileName

    def plot(self):
        path = self.openFileNameDialog()
        if type(path) != type('str'):
            return
        print(path)
        for i in self.sc.axes:
            i.clear()

        file = open(path)
        startData = 0
        title = ''
        while True:
            line = file.readline()
            if 'Time,Pos/[cm]' in line:
                break
            if line != '\n':
                title += line
                startData += 1
        file.close()
        dataFrame = pandas.read_csv(path, header=startData)
        timeLine = [(datetime.datetime.strptime(time, '%H:%M:%S.%f') - 
                 datetime.datetime.strptime(dataFrame['Time'][0], 
                 '%H:%M:%S.%f'))/datetime.timedelta(seconds=1) for time in dataFrame['Time'] ]
        dataFrame['Time'] = timeLine
        dataFrame.set_index('Time', inplace=True)
        print(dataFrame)
        
        for key in dataFrame.keys():
            if key != 'Unnamed: 0' and key != 'Time':
                if '°C' in key:
                    self.sc.axes[0].plot(dataFrame[key], linewidth=1.5, label=key)
                    self.sc.axes[0].set(ylabel='°C')
                if 'Bar' in key:
                    self.sc.axes[1].plot(dataFrame[key], linewidth=1.5, label=key)
                    self.sc.axes[1].set(ylabel='Bar')
                if 'cm' in key:
                    self.sc.axes[2].plot(dataFrame[key], linewidth=1.5, label=key)
                    self.sc.axes[2].set(ylabel='cm')
        
        if self.findMinButton.isChecked():
            # Bestimmung der lokalen Minima 
            dataFrame['min'] = dataFrame.iloc[argrelextrema(dataFrame['Pos/[cm]'].values, np.less_equal,
                            order=2000)[0]]['Pos/[cm]']
            #axS.scatter(dataFrame.index, dataFrame['min'], c='r')
            dataFrame['max'] = dataFrame.iloc[argrelextrema(dataFrame['Pos/[cm]'].values, np.greater_equal,
                            order=2000)[0]]['Pos/[cm]']
            #axS.scatter(dataFrame.index, dataFrame['max'], c='g')
            # Bestimmung der Zykluszeit von erstem lokalen Min zu dem nächsten.
            # D.h. Zeit die der Kolben braucht um von links nach rechts und zurück zu fahren.
            # Daraus liesse sich die Leistung berechnen.
            deltaTime = 0.0
            startTime = 0.0
            dataFrame['startZyklus'] = np.nan
            timesStarting =[]
            for time in dataFrame.index:
                if dataFrame['min'][time] >= 0 and startTime == 0.0:
                    #print(time)
                    startTime = time
                    timesStarting.append(time)
                    dataFrame.at[time, 'startZyklus'] = dataFrame['min'][time]
                    self.sc.axes[2].annotate('%.1f'%time, (time-40, dataFrame['startZyklus'][time]-0.5))
                elif dataFrame['min'][time] >= 0 and deltaTime < 40.0:
                    deltaTime = time - startTime
                elif dataFrame['min'][time] >= 0 and deltaTime >40.0:
                    deltaTime = time - startTime
                    print('Zyklus Zeit: %.3f' %deltaTime)
                    dataFrame.at[time, 'startZyklus'] = dataFrame['min'][time]
                    self.sc.axes[2].annotate('%.1f'%time, (time-40, dataFrame['startZyklus'][time]-0.5))
                    timesStarting.append(time)
                    startTime = time
                    deltaTime = 0.0
            self.sc.axes[2].scatter(dataFrame.index, dataFrame['startZyklus'], c='r')

        self.sc.axes[0].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.sc.axes[1].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.sc.axes[2].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        self.sc.axes[2].set_xlabel('Zeit in Sekunden')

        self.sc.draw()


    
        



if __name__ == "__main__":
    
    app = QApplication([])
    window = Widget()
    window.show()
    sys.exit(app.exec_())
