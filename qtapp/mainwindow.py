
from qtapp.appwidgets.C_QNavigator import C_QNavigatorDock
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import stonks
import filters
import datetime
import qplotting

# Get App specific widgets
from . import appwidgets
from . import subwindows

class Action(QAction):
    def __init__(self,*args,shortcut=None):
        super(Action,self).__init__(*args)
        if not shortcut is None:
            self.setShortcut(shortcut) 
    
    def connect(self,fn):
        self.triggered.connect(fn)
        return self


class mainWindow(QMainWindow):
    def __init__(self,sysargs = None):
        super().__init__()

        #Widget Layout
        self.setGeometry(100,100,1500,1500)
        self.centralWidget = QWidget(self)
        self.layout = QGridLayout(self.centralWidget)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.setContentsMargins(0,0,0,0)

        self.setCentralWidget(self.centralWidget)

        # TODO: Add Drag function
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
  
        # Internal Memory
        self.mainWidgetMap = {}
        self.currentMainWidget = None

        # Build the gui
        self.createMenu()
        self.createInputs()

     
    def createMenu(self):
        self.mainMenu = self.menuBar()
        self.mainMenu.installEventFilter(self)
        # TODO make left and right menuBar
        # leftMenu = QMenuBar(self)
        # rightMenu = QMenuBar(self)
        # mainMenu.addWidget(leftMenu)
        # mainMenu.addWidget(rightMenu)
        
        #
        ## File Menu
        #
        fileMenu = self.mainMenu.addMenu('&File')

        # Actions
        # loadAct = Action("load",self).connect(self.openFile)
        # self.mainMenu.addAction(loadAct)

        #exit
        exitAct = Action("Exit",self).connect(self.close)
        self.mainMenu.addAction(exitAct)
        pass

    def createWidgets(self):
        self.searchWidget = subwindows.SearchWidget(self)
        self.searchWidget.setVisible(False)
        self.mainWidgetMap['search'] = self.searchWidget

        self.mainWidgetMap['dummy'] = QWidget(self)
        self.mainWidgetMap['dummy'].setVisible(False)
        pass

    def createInputs(self):
        self.createWidgets()
        # Left Side
        self.leftNavigator = appwidgets.C_QNavigator(self)
        for name,widget in self.mainWidgetMap.items(): self.leftNavigator.addButton(name,widget)
        self.leftNavigator.setMaximumWidth(200)
        self.leftNavigator.setMinimumWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea,C_QNavigatorDock(self,self.leftNavigator))
        self.leftNavigator.onPress.connect(self.mainWidgetChanged)
        # self.layout.addWidget(self.leftNavigator,0,0)

        self.mainWidgetChanged('search')
        # self.layout.addWidget(self.searchWidget,0,1)

        
        pass

        
    def eventFilter(self,watched,event):
        if(watched == self.mainMenu):
            if (event.type() == QEvent.MouseButtonPress):
                # QMouseEvent* mouse_event = dynamic_cast<QMouseEvent*>(event)
                if (event.button() == Qt.LeftButton):
                    self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
                    return False
            elif (event.type() == QEvent.MouseMove):
                if (event.buttons() & Qt.LeftButton):
                    self.move(event.globalPos() - self.dragPosition)
                    return False
        return super(mainWindow, self).eventFilter(watched, event)
    
    def mainWidgetChanged(self,widgetName):
        if not self.currentMainWidget is None: 
            self.layout.removeWidget(self.currentMainWidget)
            self.currentMainWidget.setVisible(False)
        self.currentMainWidget = self.mainWidgetMap[widgetName]
        self.layout.addWidget(self.currentMainWidget,0,1)
        self.currentMainWidget.setVisible(True)
