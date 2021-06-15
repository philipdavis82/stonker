
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import stonks
import filters
import datetime
import qplotting

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
        self.setCentralWidget(self.centralWidget)

        # TODO: Add Drag function
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
  

        # File Memory
        self.stonkNames = []
        self.currentFile = None

        # Build the gui
        self.createMenu()
        self.createInputs()
        
        # Connect Filters
        self.updateCompanyList()

     
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
        print(fileMenu)
        # Actions
        # loadAct = Action("load",self).connect(self.openFile)
        # self.mainMenu.addAction(loadAct)

        #exit
        exitAct = Action("Exit",self).connect(self.close)
        self.mainMenu.addAction(exitAct)
        pass

    def createInputs(self):
        # Left Side
        self.filterLine = QLineEdit(self)
        self.filterLine.textChanged.connect(self.filterStonks)
        # Loaded Files
        self.fileList = QListWidget(self)
        # self.fileList.setMaximumWidth(700)
        self.fileList.itemDoubleClicked.connect(self.temp_PlotData)
        # Button To Load File
        # self.fileLoadBtn = QPushButton("Load",self)
        # self.fileLoadBtn.setMaximumWidth(300)
        # Right Side
        # self.fileOptions = QWidget(self)
        
        # Add To Layout
        # Left
        self.layout.addWidget(self.filterLine,0,0)
        self.layout.addWidget(self.fileList,1,0)
        # self.layout.addWidget(self.fileLoadBtn,2,0,1,1)
        # Right
        # self.layout.addWidget(self.fileOptions,0,1,1,3)
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
    
    def updateCompanyList(self,*args):
        self.fileList.clear()
        self.stonkNames = list(stonks.tickers.getStockTickers().keys())
        self.fileList.addItems(self.stonkNames)
            
    def filterStonks(self,*args):
        filterText = self.filterLine.text()
        filterText = filterText.split(" ")
        foundStonks = set([])
        for text in filterText:
            filterFn = lambda stonk: str.count(stonk.lower(),text.lower())>0
            temp = set(filter(filterFn,self.stonkNames))
            foundStonks |= temp
        foundStonks = list(foundStonks)
        self.fileList.clear()
        self.fileList.addItems(foundStonks)

    def openFile(self):
        pass

    def temp_PlotData(self,item):
        cname = item.text()
        info = stonks.tickers.getStockTickerInfo(cname)
        ticker = info["ticker"]
        today = datetime.datetime.today()
        last2y = datetime.datetime(today.year-20,today.month,today.day)
        data = stonks.web.yahoo.historical(ticker,last2y,today)
        if data is None: return print(f"Failed to get data {ticker}")
        time = data._time##.astype(float)#[ t.astype(float) for t in data._time ]
        high = data._high
        low = data._low
        canvas = qplotting.plot_canvas()
        widget = qplotting.plot_widget(canvas)
        canvas.setPlot(time,high,label="high")
        canvas.setPlot(time,low,label="low")
        canvas.setFigureName(cname)
        canvas.plot()
        widget.show()