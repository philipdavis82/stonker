# Python based Gemini File Reader
#
#
#

import sys,os

# Setup globals
import __global__
__global__.HOME_DIR = os.path.abspath(os.path.split(__file__)[0])


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import qtapp
if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    with open(os.path.join("qtapp","css","dark.qss"),'r') as file:
        styletxt = file.read()
    qapp.setStyleSheet(styletxt)
    win = qtapp.mainWindow()
    win.show()
    qapp.exec()