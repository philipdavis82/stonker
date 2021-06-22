from stonks.tickers.tickers import getStockTickers
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import datetime

from stonks import tickers
import stonks
import qplotting
class _SIGNAL_HOLDER():
    def __init__(self,signal,*args):
        self.signal = signal
        self.args = args
    def fn(self):
        self.signal(*self.args)

class _DatePicker(QWidget):
    updated = pyqtSignal(str)

    def __init__(self,parent,*args,**kwargs):
        super().__init__(parent)
    
        self.layout = QHBoxLayout(self)
        self.buttonsMade = []
        self.fnList = []

    def buildDates(self,dateList:list):
        for button in self.buttonsMade:
            self.layout.removeWidget(button)
        self.fnList.clear()
        for i,date in enumerate(dateList):
            button = QPushButton(date,self)
            args = _SIGNAL_HOLDER(self.updated.emit,date)
            self.fnList.append(args) 
            button.clicked.connect(args.fn)
            self.layout.addWidget(button)
            

class SearchWidget(QWidget):
    
    def __init__(self,parent):
        super().__init__(parent)
        # Widget Memory
        self.companyList = {}
        self.dateRanges = {
            '1-week' : datetime.timedelta(days=7),
            '2-week' : datetime.timedelta(days=14),
            '1-month': datetime.timedelta(days=30),
            '3-month': datetime.timedelta(days=90),
            '1-year' : datetime.timedelta(days=365),
            '5-year' : datetime.timedelta(days=365*5),
            '10-year': datetime.timedelta(days=365*10),
        }

        # Plotting Widgets
        self.plotCanvas = qplotting.d_1.PlotCanvas(dpi=150)
        self.plotWidget = qplotting.d_1.PlotWidget(self.plotCanvas,parent=self,withToolbar=False)
        self.plotWidget.enableDarkTheme()

        # Current State
        self.currentTicker = None
        self.currentDateRange = '1-week'

        # Layout Information
        self.layout = QGridLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0,0,0,0)
        self.createLayout()
        self.populateCompanyList()

    def createLayout(self):
        self.layout.addWidget(self.plotWidget,0,0)
        
        self.datePicker = _DatePicker(self)
        self.datePicker.buildDates(list(self.dateRanges.keys()))
        self.datePicker.updated.connect(self.updateSelectedRange)
        self.layout.addWidget(self.datePicker,1,0)

        self.companyFilterBar = QLineEdit("",self)
        self.companyFilterBar.textChanged.connect(self.filterCompanyList)
        self.layout.addWidget(self.companyFilterBar,2,0)

        self.companyListWidget = QListWidget(self)
        self.companyListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.companyListWidget.itemClicked.connect(self.updateSelectedTicker)
        self.layout.addWidget(self.companyListWidget,3,0)

    def populateCompanyList(self):
        tlist = tickers.getStockTickers()
        self.companyList.clear()
        for comp,table in tlist.items():
            self.companyList[comp] = table['ticker']
        self.companyListWidget.addItems(self.companyList)

    def filterCompanyList(self,filtertext):
        if type(filtertext) != str: filtertext = filtertext.text() 
        newCompList = [ comp for comp in self.companyList if comp.lower().count(filtertext.lower()) ]
        self.companyListWidget.clear()
        self.companyListWidget.addItems(newCompList)

    def updateSelectedRange(self,range):
        print(range)
        self.currentDateRange = range
        self.updateSelectedTicker(None)

    def updateSelectedTicker(self,ticker):
        
        self.plotCanvas.clearAllPlots()
        
        for item in self.companyListWidget.selectedItems():
            item = item.text()
            ticker = self.companyList[item]
            today = datetime.datetime.today()
            start = today - self.dateRanges[self.currentDateRange]
            hist = stonks.historical(ticker,start,today)
            if hist is None: return print(f"Failed to find company info {ticker}")
            self.plotCanvas.setPlot(hist._time,hist._high,label=item)
        self.plotCanvas.plot()
        self.plotWidget.enableDarkTheme()
