#Std Lib
import copy
import time
# import pickle

#PyQt5 Lib
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#Matplotlib Lib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.cm import cmap_d as colorMap
from matplotlib.pyplot import rcParams 
from matplotlib.transforms import BboxTransformTo,Bbox

#Common 3rd Party Libs
import numpy as np

#utils
# from .plot_utils import *
from .canvas import PlotCanvas
from . import utils
from .trace import Trace


class plot_toolbar(QWidget):
    def __init__(self,parent=None):
        super(plot_toolbar,self).__init__(parent)
        self.setMaximumHeight(50)
        self.layout = QGridLayout(self)
        self.toolbar = QToolBar(self)
        self.layout.addWidget(self.toolbar)
        self.basePalette = None
        self.actions = {}
    def addAction(self,name,shortcut=None, toggelable=True):
        newAction = QAction(name,self)
        if(not shortcut is None): newAction.setShortcut(shortcut)
        self.actions[newAction] = False
        self.toolbar.addAction(newAction)
        self.basePalette = self.toolbar.widgetForAction(newAction).palette()
        if toggelable: newAction.triggered.connect(lambda: self.actionTriggered(newAction))
        return newAction
    def actionTriggered(self,action):
        if self.actions[action] == False:
            button = self.toolbar.widgetForAction(action)
            button.setDown(True)
            self.actions[action] = True
        elif self.actions[action] == True:
            self.actions[action] = False
            button = self.toolbar.widgetForAction(action)
            button.setDown(False)

class PlotWidget(QWidget):
    class InternalWidget():
        #This just hold variables that all Internal widgets will need
        def __init__(self,*args):
            self.active = False
            self.graphNameToID = {}
            self.graphNameToAxisID = {}
            self.staticWidth = 300 
            self.setMaximumWidth(300)
            self.setMinimumWidth(300)
            
        def activate(self):
            if(self.active):
                self.Parent.popOutOfLayout(self)
            else:
                self.Parent.pushIntoLayout(self)
        def rebuildGraphList(self,canvas):
            print("Should be overwritten")
            traces = canvas.getAllTraces()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID

    
    class AnalysisWidget(QWidget,InternalWidget):
        # Tools
        #  - Rolling average function
        #  - Adding and subtracting 2 plots
        #  - ...
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.selectedIndex2 = 0
            # self.setMaximumWidth(400)
            self.createInputs()
        
        def createInputs(self):
            #Create Inputs
            
            self.titleLbl = QLabel("- Analysis -",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            
            self.graphSelectLine = QLineEdit("",self)
            self.graphSelectLine.returnPressed.connect(self.graphLabelChanged)

            self.removeTraceBtn = QPushButton("Remove",self)
            self.removeTraceBtn.clicked.connect(self.removeTrace)

            self.averageTraceLabel = QLabel("Average Trace",self)
            self.averageTraceSlider = QSlider(Qt.Horizontal,self)
            self.averageTraceSlider.setMinimum(2)
            self.averageTraceSlider.setMaximum(100)
            self.averageTraceSlider.valueChanged.connect(self.averageTrace)
            self.averageTraceEdit = QLineEdit("2",self)
            self.averageTraceEdit.textChanged.connect(self.averageTrace)
            
            self.singleTraceLbl = QLabel("- Single Trace Math -",self)
            self.singleTraceLbl.setAlignment(Qt.AlignCenter)

            self.flipTraceBtn = QPushButton("Flip X",self)
            self.flipTraceBtn.clicked.connect(self.flipTrace)

            self.dervTraceBtn = QPushButton("Derivate",self)
            self.dervTraceBtn.clicked.connect(self.derivitaveTrace)
            
            self.intgTraceBtn = QPushButton("Integrate",self)
            self.intgTraceBtn.clicked.connect(self.integrateTrace)

            self.fftTraceBtn = QPushButton("FFT",self)
            self.fftTraceBtn.clicked.connect(self.fouierTrasnformTrace)

            self.sortTraceBtn = QPushButton("Sort",self)
            self.sortTraceBtn.clicked.connect(self.sortTrace)
            
            self.multiTraceLbl = QLabel("- Multi Trace Math -",self)
            self.multiTraceLbl.setAlignment(Qt.AlignCenter) 

            self.graphSelectLabel2 = QLabel("Graph Selection 2",self)
            self.graphSelectBox2 = QComboBox(self)
            self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)

            self.addGraphsBtn = QPushButton("Add",self)
            self.addGraphsBtn.clicked.connect(self.addGraphs)
            self.subGraphsBtn = QPushButton("Subtract",self)
            self.subGraphsBtn.clicked.connect(self.subGraphs)
            self.mulGraphsBtn = QPushButton("Multiply",self)
            self.mulGraphsBtn.clicked.connect(self.mulGraphs)
            self.divGraphsBtn = QPushButton("Divide",self)
            self.divGraphsBtn.clicked.connect(self.divGraphs)
            
            #Build layout
            I = utils.Counter()
            I.set(1)
            self.layout.addWidget(self.titleLbl,I(),1)
            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            self.layout.addWidget(self.graphSelectLine,I(),1)
            self.layout.addWidget(self.removeTraceBtn,I(),1)
            self.layout.addWidget(self.averageTraceLabel,I(),1)
            self.layout.addWidget(self.averageTraceSlider,I(),1)
            self.layout.addWidget(self.averageTraceEdit,I(),1)
            self.layout.addWidget(self.singleTraceLbl,I(),1)
            self.layout.addWidget(self.flipTraceBtn,I(),1)
            self.layout.addWidget(self.dervTraceBtn,I(),1)
            self.layout.addWidget(self.intgTraceBtn,I(),1)
            self.layout.addWidget(self.fftTraceBtn,I(),1)
            self.layout.addWidget(self.sortTraceBtn,I(),1) 
            self.layout.addWidget(self.graphSelectLabel2,I(),1)
            self.layout.addWidget(self.graphSelectBox2,I(),1)
            self.layout.addWidget(self.multiTraceLbl,I(),1)
            self.layout.addWidget(self.addGraphsBtn,I(),1)
            self.layout.addWidget(self.subGraphsBtn,I(),1)
            self.layout.addWidget(self.mulGraphsBtn,I(),1)
            self.layout.addWidget(self.divGraphsBtn,I(),1)
            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
        
        def graphSelectionChanged(self,index):
            # print(self.selectedIndex)
            self.selectedIndex = index
            self.graphSelectLine.setText(self.graphSelectBox.currentText())
        
        def graphLabelChanged(self):
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            self.Parent.canvas.updatePlotName(traceName,self.graphSelectLine.text(),traceID)
            self.Parent.canvas.plot(rescale=False)

        def graphSelectionChanged2(self,index):
            self.selectedIndex2 = index

        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            # traces = canvas.getAllTraces()
            self.graphSelectBox.currentIndexChanged.disconnect(self.graphSelectionChanged)
            self.graphSelectBox2.currentIndexChanged.disconnect(self.graphSelectionChanged2)
            self.graphSelectBox.clear()
            self.graphSelectBox2.clear()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphSelectBox.addItem(val.name)
                self.graphSelectBox2.addItem(val.name)
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            if(self.selectedIndex >= self.graphSelectBox.count()):
                self.selectedIndex = 0
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            if(self.selectedIndex2 >= self.graphSelectBox2.count()):
                self.selectedIndex2 = 0
            self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
            # self.graphSelectionChanged(self.selectedIndex)

        def removeTrace(self):
            traceName = self.graphSelectBox.currentText()
            index = self.graphSelectBox.currentIndex()
            if self.selectedIndex > index: self.selectedIndex = 0
            elif self.selectedIndex == index: self.selectedIndex = 0
            try:
                traceID = self.graphNameToID[traceName]
                self.Parent.canvas.removePlot(traceID)
                self.Parent.canvas.plot(rescale=False)
            except Exception as e:
                print(e)
                return

        def getSelectedGraph(self):
            # self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            # traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceName = self.graphSelectBox.currentText()
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def getSelectedGraph2(self):
            # self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
            # traceName = self.graphSelectBox2.itemText(self.selectedIndex2)
            traceName = self.graphSelectBox2.currentText()
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def averageTrace(self,value):
            if(type(value)==str):
                try:
                    value = int(value)
                    if value<2:
                        return
                except Exception as e:
                    print(e)
                    return
            else:
                self.averageTraceEdit.textChanged.disconnect(self.averageTrace)
                self.averageTraceEdit.setText(str(value))
                self.averageTraceEdit.textChanged.connect(self.averageTrace)
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = traceName + "_AVG"
                if(value>=len(trace.x)):return
                newY = np.copy(trace.y)
                kernal = np.ones(value)/value
                newY = np.convolve(kernal,newY,mode="valid")
                N = newY.size
                dN = int((trace.y.size - newY.size)/2)
                newX = np.copy(trace.x[dN:dN+N])
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

        def flipTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                trace.y = np.flip(trace.y)
            except Exception as e:
                print(e)
                return
            # self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

        def sortTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newY = np.sort(trace.y)
                newX = trace.x.copy()
                newName = traceName+"_Sorted"
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

        def derivitaveTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = "Δ"+traceName
                newX = np.copy(trace.x).astype("double")
                newY = np.copy(trace.y).astype("double")
                # kernal = np.ones(value)/value
                newY = newY[1:] - newY[:-1]
                newX = newX[1:] 
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)
        
        def integrateTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = "∫"+traceName
                newX = np.copy(trace.x)
                newY = np.copy(trace.y)
                # kernal = np.ones(value)/value
                newY = np.cumsum(newY) 
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

        def fouierTrasnformTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = "F("+traceName+")"
                newX = np.copy(trace.x)
                newY = np.copy(trace.y)
                newY = np.abs(np.fft.fftshift(np.fft.fft(np.fft.fftshift(newY))))/len(newY)*2
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)  
    
        def addGraphs(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                traceName2,traceID2,axesID2,trace2 = self.getSelectedGraph2()
                newName = traceName+"+"+traceName2
                y2 = np.interp(trace.x,trace2.x,trace2.y)
                newY = trace.y+y2
            except Exception as e:
                print(e)
            self.Parent.canvas.setPlot(trace.x,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)
        
        def subGraphs(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                traceName2,traceID2,axesID2,trace2 = self.getSelectedGraph2()
                newName = traceName+"-"+traceName2
                y2 = np.interp(trace.x,trace2.x,trace2.y)
                newY = trace.y-y2
            except Exception as e:
                print(e)
            self.Parent.canvas.setPlot(trace.x,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)
        
        def mulGraphs(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                traceName2,traceID2,axesID2,trace2 = self.getSelectedGraph2()
                newName = traceName+"*"+traceName2
                y2 = np.interp(trace.x,trace2.x,trace2.y)
                newY = trace.y*y2
            except Exception as e:
                print(e)
            self.Parent.canvas.setPlot(trace.x,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)
        
        def divGraphs(self):
            tol = 0.0000001
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                traceName2,traceID2,axesID2,trace2 = self.getSelectedGraph2()
                newName = traceName+"/"+traceName2
                y2 = np.interp(trace.x,trace2.x,trace2.y)
                y2[np.abs(y2)<tol] = tol
                newY = trace.y/y2
            except Exception as e:
                print(e)
            self.Parent.canvas.setPlot(trace.x,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

    class ConversionWidget(QWidget,InternalWidget):
        # Tools
        #  - Rolling average function
        #  - Adding and subtracting 2 plots
        #  - ...
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.selectedIndex2 = 0
            # self.setMaximumWidth(400)
            self.createInputs()

        def createInputs(self):
            #Create Inputs
            
            self.titleLbl = QLabel("- Conversion -",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            
            # self.graphSelectLine = QLineEdit("",self)
            # self.graphSelectLine.returnPressed.connect(self.graphLabelChanged)
        
            self.optionsLbl = QLabel("- Options -",self)
            self.optionsLbl.setAlignment(Qt.AlignCenter)

            self.radToDegTraceBtn = QPushButton("Radians To Degrees",self)
            self.radToDegTraceBtn.clicked.connect(self.radToDegTrace)

            self.degToRadTraceBtn = QPushButton("Degrees To Radians",self)
            self.degToRadTraceBtn.clicked.connect(self.degToRadTrace)

            #Build layout
            I = utils.Counter()
            I.set(1)
            self.layout.addWidget(self.titleLbl,I(),1)
            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            # self.layout.addWidget(self.graphSelectLine,I(),1)
            self.layout.addWidget(self.optionsLbl,I(),1)
            self.layout.addWidget(self.radToDegTraceBtn,I(),1)
            self.layout.addWidget(self.degToRadTraceBtn,I(),1)

            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
            
        def graphSelectionChanged(self,index):
            # print(self.selectedIndex)
            self.selectedIndex = index
            # self.graphSelectLine.setText(self.graphSelectBox.currentText())
        
        def graphLabelChanged(self):
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            self.Parent.canvas.updatePlotName(traceName,self.graphSelectLine.text(),traceID)
            self.Parent.canvas.plot(rescale=False)
        
        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            # traces = canvas.getAllTraces()
            self.graphSelectBox.currentIndexChanged.disconnect(self.graphSelectionChanged)
            # self.graphSelectBox2.currentIndexChanged.disconnect(self.graphSelectionChanged2)
            self.graphSelectBox.clear()
            # self.graphSelectBox2.clear()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphSelectBox.addItem(val.name)
                # self.graphSelectBox2.addItem(val.name)
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            # self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            if(self.selectedIndex >= self.graphSelectBox.count()):
                self.selectedIndex = 0
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            # if(self.selectedIndex2 >= self.graphSelectBox2.count()):
                # self.selectedIndex2 = 0
            # self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
        
        def getSelectedGraph(self):
            # self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            # traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceName = self.graphSelectBox.currentText()
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace
        
        def radToDegTrace(self,value):
            if(type(value)==str):
                try:
                    value = int(value)
                    if value<2:
                        return
                except Exception as e:
                    print(e)
                    return
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = traceName + "_Deg"
                if(value>=len(trace.x)):return
                newY = np.copy(trace.y)
                newY *= (180/np.pi) # Scale Factor
                N = newY.size
                newX = np.copy(trace.x)
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)
        
        def degToRadTrace(self,value):
            if(type(value)==str):
                try:
                    value = int(value)
                    if value<2:
                        return
                except Exception as e:
                    print(e)
                    return
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = traceName + "_Rad"
                if(value>=len(trace.x)):return
                newY = np.copy(trace.y)
                newY *= (np.pi/180) # Scale Factor
                N = newY.size
                newX = np.copy(trace.x)
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

    class MetricsWidget(QWidget,InternalWidget):
        # Tools
        #  - METRICS!
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.selectedIndex2 = 0
            # self.setMaximumWidth(400)
            self.fnList = {}
            self.makeFnList()
            self.createInputs()
        
        def createInputs(self):
            #Create Inputs
            self.singleTraceLbl = QLabel("- Metrics -",self)
            self.singleTraceLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)

            self.updateValuesBtn = QPushButton("Update",self)
            self.updateValuesBtn.clicked.connect(self.updateValues)
            
            self.graphSelectLine = QLabel("",self)
            self.graphSelectLine.setAlignment(Qt.AlignCenter)

            self.valuesList = QTreeWidget(self)
            self.valuesList.setColumnCount(2)
            self.valuesList.setHeaderLabels(['Metric','Value'])
            
            #Build layout
            I = utils.Counter()
            I.set(1)
            
            self.layout.addWidget(self.singleTraceLbl,I(),1)
            
            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            self.layout.addWidget(self.updateValuesBtn,I(),1)
            self.layout.addWidget(self.graphSelectLine,I(),1)
            
            self.layout.addWidget(self.valuesList,I(),1)
        
        def graphSelectionChanged(self,index):
            self.selectedIndex = index
            self.graphSelectLine.setText(self.graphSelectBox.currentText())
            self.updateValues()

        def newMetric(self,fn):
            self.fnList[fn.__name__] = fn

        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            # traces = canvas.getAllTraces()
            self.graphSelectBox.currentIndexChanged.disconnect(self.graphSelectionChanged)
            # self.graphSelectBox2.currentIndexChanged.disconnect(self.graphSelectionChanged2)
            self.graphSelectBox.clear()
            # self.graphSelectBox2.clear()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphSelectBox.addItem(val.name)
                # self.graphSelectBox2.addItem(val.name)
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            # self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            self.graphSelectionChanged(self.selectedIndex)

        def getSelectedGraph(self):
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def updateValues(self):
            if self.isVisible():
                try:
                    self.valuesList.clear()
                    traceName,traceID,axesID,trace = self.getSelectedGraph()
                    for name,fn in self.fnList.items():
                        self.valuesList.addTopLevelItem(QTreeWidgetItem([str(name),str(fn(self,trace))]))
                    self.valuesList.update()        
                except:
                    print("Failed to updae metrics")
            
        def makeFnList(self):
            # Add Functions Here
            # The format is :
            #   @self.newMetric
            #   def name(self,trace)
            @self.newMetric
            def average(self,trace): return np.mean(trace.y)
            @self.newMetric
            def min(self,trace): indx = np.argmin(trace.y); return (trace.x[indx],trace.y[indx])
            @self.newMetric
            def max(self,trace): indx = np.argmax(trace.y); return (trace.x[indx],trace.y[indx])
            @self.newMetric
            def length(self,trace): return trace.y.size
                        
    class StatisticsWidget(QWidget,InternalWidget):
        # Tools
        #  - METRICS!
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.selectedIndex2 = 0
            # self.setMaximumWidth(400)
            self.createInputs()
        
        def createInputs(self):
            #Create Inputs
            self.titleLbl = QLabel("Special Analysis Methods",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            
            self.graphSelectLine = QLabel("",self)

            # self.graphSelectLine = QLabel("",self)

            self.unwrapLabel = QLabel("Unwrapping Function",self)
            self.unwrapValueInput = QLineEdit("Threshold",self)
            self.unwrapValueToAdd = QLineEdit("To Shift",self)
            self.unwrapButton = QPushButton("Unwrap",self)
            self.unwrapButton.clicked.connect(self.unwrapTrace)

            self.multiTraceLbl = QLabel("- Multi Trace Math -",self)
            self.multiTraceLbl.setAlignment(Qt.AlignCenter) 

            self.graphSelectLabel2 = QLabel("Graph Selection 2",self)
            self.graphSelectBox2 = QComboBox(self)
            self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            
            #Build layout
            I = utils.Counter()
            I.set(1)
            
            self.layout.addWidget(self.titleLbl,I(),1)

            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            self.layout.addWidget(self.graphSelectLine,I(),1)
            
            self.layout.addItem(QSpacerItem(0,20),I(),1)

            self.layout.addWidget(self.unwrapLabel,I(),1)
            self.layout.addWidget(self.unwrapValueInput,I(),1)
            self.layout.addWidget(self.unwrapValueToAdd,I(),1)
            self.layout.addWidget(self.unwrapButton,I(),1)

            self.layout.addItem(QSpacerItem(0,20),I(),1)

            self.layout.addWidget(self.multiTraceLbl,I(),1)
            self.layout.addWidget(self.graphSelectLabel2,I(),1)
            self.layout.addWidget(self.graphSelectBox2,I(),1)

            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
        
        def graphSelectionChanged(self,index):
            self.selectedIndex = index
            self.graphSelectLine.setText(self.graphSelectBox.currentText())
        
        def graphLabelChanged(self):
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            self.Parent.canvas.updatePlotName(traceName,self.graphSelectLine.text(),traceID)
            self.Parent.canvas.plot(rescale=False)

        def graphSelectionChanged2(self,index):
            self.selectedIndex2 = index

        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            # traces = canvas.getAllTraces()
            self.graphSelectBox.currentIndexChanged.disconnect(self.graphSelectionChanged)
            self.graphSelectBox2.currentIndexChanged.disconnect(self.graphSelectionChanged2)
            self.graphSelectBox.clear()
            self.graphSelectBox2.clear()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphSelectBox.addItem(val.name)
                self.graphSelectBox2.addItem(val.name)
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            self.graphSelectionChanged(self.selectedIndex)

        def getSelectedGraph(self):
            # self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            # traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceName = self.graphSelectBox.currentText()
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def getSelectedGraph2(self):
            # self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
            # traceName = self.graphSelectBox2.itemText(self.selectedIndex2)
            traceName = self.graphSelectBox.currentText()
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def unwrapTrace(self):
            
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = traceName+"_unwrap"
                unwrapThreshold = float(self.unwrapValueInput.text())
                unwrapShift = float(self.unwrapValueToAdd.text())
                dY = trace.y[1:]-trace.y[:-1]
                newY = trace.y.copy()
                newX = trace.x.copy()
                # print(dY)
                # print(unwrapThreshold)
                # print(dY < unwrapThreshold)
                indxsUp = np.nonzero(dY < -unwrapThreshold)[0]
                indxsUp += 1
                indxsDown = np.nonzero(dY > unwrapThreshold)[0]
                indxsDown += 1
                # print(indxsUp)
                # print(indxsDown)
                for i in indxsUp:
                    newY[i:]+=unwrapShift
                for i in indxsDown:
                    newY[i:]-=unwrapShift
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot(rescale=False)

    class MathInterpWidget(QWidget,InternalWidget):
        # Tools
        #  - Create an interpreter
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.selectedIndex2 = 0
            self.yID = "y"
            self.xID = "x"
            self.idToGraphName = {}
            # self.setMaximumWidth(400)
            self.createInputs()
        
        def createInputs(self):
            #Create Inputs
            self.titleLbl = QLabel("- WIP -",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            
            self.graphSelectionTree = QTreeWidget(self)
            self.graphSelectionTree.setColumnCount(2)
            self.graphSelectionTree.setHeaderLabels(["id","Trace"])

            self.graphNameLb = QLabel("New Graph Name")
            self.graphNameLn = QLineEdit("tmp",self)

            self.yInterpreterLb = QLabel("Y") 
            self.yInterpreterLn = QLineEdit(r"{y0}-{y0}+1",self)

            self.xInterpreterLb = QLabel("X")
            self.xInterpreterLn = QLineEdit(r"{x0}",self)

            self.startCalculationBtn = QPushButton("Calculate",self)
            self.startCalculationBtn.clicked.connect(self.interpret)
            
            #Build layout
            I = utils.Counter()
            I.set(1)
            
            self.layout.addWidget(self.titleLbl,I(),1)
            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectionTree,I(),1)
            self.layout.addWidget(self.graphNameLb,I(),1)
            self.layout.addWidget(self.graphNameLn,I(),1)
            self.layout.addWidget(self.yInterpreterLb,I(),1)
            self.layout.addWidget(self.yInterpreterLn,I(),1)
            self.layout.addWidget(self.xInterpreterLb,I(),1)
            self.layout.addWidget(self.xInterpreterLn,I(),1)
            self.layout.addWidget(self.startCalculationBtn,I(),1)
            
            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
        
        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            self.graphSelectionTree.clear()
            maxln = (-1,None)
            try:
                tx = list(traces.values())[0]
            except:
                return
            xrange = (tx.x.min(),tx.x.max())
            
            for i,(key,val) in enumerate(traces.items()):
                if tx.x.min() > xrange[0]: xrange[0] = tx.x.min()
                if tx.x.max() < xrange[1]: xrange[1] = tx.x.max()
            
            for i,(key,val) in enumerate(traces.items()):
                sx = val.x[(val.x>xrange[0]) & (val.x<xrange[1])]
                if sx.size > maxln[0]: maxln=(sx.size,sx)

            for i,(key,val) in enumerate(traces.items()):
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
                xID = self.xID+str(i)
                yID = self.yID+str(i)
                indx = (val.x>xrange[0]) & (val.x<xrange[1])
                newx = np.linspace(float(xrange[0]),float(xrange[1]),maxln[0])
                self.idToGraphName[xID] = newx 
                self.idToGraphName[yID] = np.interp(newx,val.x,val.y)
                self.graphSelectionTree.addTopLevelItem(QTreeWidgetItem([str(i),val.name]))

        def getSelectedGraphData(self,ID):
            # self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            # traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceName = self.idToGraphName[ID]
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            if ID.count(self.xID):
                return trace.x
            if ID.count(self.yID):
                return trace.y
            raise Exception("x-y ID not found in string")        
            # return traceName,traceID,axesID,trace

        def interpret(self):
            tmpTable = {}
            lenList = []
            for key,val in self.idToGraphName.items():
                lenList.append(len(val))


           
            tmpTable = self.idToGraphName
            print(self.yInterpreterLn.text())
            name = self.graphNameLn.text()
            if name == "": name = "nan"
            try:
                if self.yInterpreterLn.text() != "":
                    y = utils.MathInterpreter.interpretString(self.yInterpreterLn.text(),tmpTable)
                else:
                    return
                if self.xInterpreterLn.text() != "":
                    x = utils.MathInterpreter.interpretString(self.xInterpreterLn.text(),tmpTable)
                else:
                    x = np.arange(len(y))
            except Exception as e:
                print(e)
                return
            if(x.size < y.size): y = y[:x.size]
            if(y.size < x.size): x = x[:y.size]
            self.Parent.canvas.setPlot(x,y,label=name)
            self.Parent.canvas.plot(rescale=False)
            pass

    class ValuesWidget(QWidget,InternalWidget):
        # Tools
        #  - METRICS!
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            self.selectedIndex = 0
            self.createInputs()
        
        def createInputs(self):
            #Create Inputs
            self.titleLbl = QLabel("- Values -",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            
            self.graphSelectLine = QLabel("",self)

            self.updateBtn = QPushButton("Update",self)
            self.updateBtn.clicked.connect(self.updateValues)

            self.valuesList = QTreeWidget(self)
            self.valuesList.setColumnCount(2)
            self.valuesList.setHeaderLabels(['X','Y'])
            #Build layout
            I = utils.Counter()
            I.set(1)
            
            self.layout.addWidget(self.titleLbl,I(),1)

            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            self.layout.addWidget(self.graphSelectLine,I(),1)
            
            self.layout.addWidget(self.updateBtn,I(),1)

            self.layout.addWidget(self.valuesList,I(),1)
            
            # self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
        
        def graphSelectionChanged(self,index):
            self.selectedIndex = index
            self.graphSelectLine.setText(self.graphSelectBox.currentText())
            if(self.isVisible()):
                try:
                    print("Updating")
                    self.updateValues()
                except:
                    print("Failed To Update Value List")     
        def graphLabelChanged(self):
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            self.Parent.canvas.updatePlotName(traceName,self.graphSelectLine.text(),traceID)
            self.Parent.canvas.plot(rescale=False)

        def rebuildGraphList(self):
            traces = self.Parent.canvas.getAllTraces()
            # traces = canvas.getAllTraces()
            self.graphSelectBox.currentIndexChanged.disconnect(self.graphSelectionChanged)
            self.graphSelectBox.clear()
            self.graphNameToID.clear()
            self.graphNameToAxisID.clear()
            for key,val in traces.items():
                self.graphSelectBox.addItem(val.name)
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            self.graphSelectionChanged(self.selectedIndex)

        def getSelectedGraph(self):
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace  
        
        def updateValues(self):
            self.valuesList.clear()
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            lims = self.Parent.canvas.getXLim()
            if type(lims) == list:
                mina,maxa = lims[0]
            else:
                mina,maxa = lims
            for x,y in zip(trace.x[(trace.x>mina) & (trace.x<maxa)],trace.y[(trace.x>mina) & (trace.x<maxa)]):
                self.valuesList.addTopLevelItem(QTreeWidgetItem([str(x),str(y)]))
            self.valuesList.update()

    class LayoutWidget(QWidget,InternalWidget):
        class fnHolder():
                def __init__(self,Ln,ID,updateFunction,IDOnly=False):
                    self.Ln = Ln
                    self.update = self.update1
                    if IDOnly: self.update = self.update2
                    if IDOnly is False: self.Ln.returnPressed.connect(self.update)
                    else: self.Ln.stateChanged.connect(self.update)
                    self.updateFunction = updateFunction
                    self.ID = ID
                def update1(self):
                    self.updateFunction(self.Ln.text(),self.ID) 
                def update2(self):
                    self.updateFunction(self.ID)
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) 
            self.setMaximumWidth(200) 
            self.axesList = []
            self.IDList = []
            self.fnList = []
            self.labelList = []
            self.createInputs()
            

        def createInputs(self):
            self.FigLb = QLabel("Figure Title:",self)
            self.layout.addWidget(self.FigLb,0,0)
            
            try:
                name = self.Parent.canvas.fig._suptitle.get_text()
            except:
                name = ""
            self.FigLn = QLineEdit(name,self)
            self.figTitlefn = self.fnHolder(self.FigLn,None,self.Parent.canvas.setFigureName)
            self.layout.addWidget(self.FigLn,1,0)

            self.darkThemeChk = QCheckBox("Dark Theme",self)
            self.darkThemeChk.toggled.connect(self.Parent.enableDarkTheme)
            self.layout.addWidget(self.darkThemeChk,2,0)
            pass

        def rebuildGraphList(self):
            class INDX():
                def __init__(self):
                    self._i=0
                def __call__(self):
                    __i = self._i
                    self._i+=1
                    return __i
            self.axesList.clear()
            self.fnList.clear()
            self.labelList.clear()
            try:
                for i in reversed(range(self.layout.count())): 
                    if(i==2):break
                    widget = self.layout.itemAt(i).widget() 
                    self.layout.removeWidget(widget)
                    if not widget is None: widget.setParent(None)
            except Exception as e:
                print(e)
                return
            self.repaint()
            I = INDX()
            I._i = 3
            looped = False
            for ID,axes in self.Parent.canvas.axes.items():
                # if looped:
                sepLb = QLabel("============",self)
                self.labelList.append(sepLb)
                self.layout.addWidget(sepLb,I(),0)
                
                self.IDList.append(ID)

                axesLb = QLabel("Title:",self)
                self.labelList.append(axesLb)
                self.layout.addWidget(axesLb,I(),0)
                
                axesLn = QLineEdit(axes.get_title(),self)
                fn = self.fnHolder(axesLn,ID,self.Parent.canvas.setAxesNames)
                self.fnList.append(fn)
                self.axesList.append(axesLn)
                self.layout.addWidget(axesLn,I(),0)
                
                xLb = QLabel("X Axes Label",self)
                self.labelList.append(xLb)
                self.layout.addWidget(xLb,I(),0)

                xLn = QLineEdit(axes.get_xlabel(),self)
                fn = self.fnHolder(xLn,ID,self.Parent.canvas.setXAxesNames)
                self.fnList.append(fn)
                self.axesList.append(xLn)
                self.layout.addWidget(xLn,I(),0)
                
                yLb = QLabel("Y Axes Label",self)
                self.labelList.append(yLb)
                self.layout.addWidget(yLb,I(),0)

                yLn = QLineEdit(axes.get_ylabel(),self)
                fn = self.fnHolder(yLn,ID,self.Parent.canvas.setYAxesNames)
                self.fnList.append(fn)
                self.axesList.append(yLn)
                self.layout.addWidget(yLn,I(),0)

                gChk = QCheckBox("Toggle Grid",self)
                fn = self.fnHolder(gChk,ID,self.Parent.canvas.toggleGrid,IDOnly=True)
                self.fnList.append(fn)
                self.axesList.append(gChk)
                self.layout.addWidget(gChk,I(),0)

                looped = True
            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),I(),1)

    class ExportWidget(QWidget,InternalWidget):
        def __init__(self,parent):
            super().__init__(parent)
            self.Parent = parent
            self.layout = QGridLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) 
            self.setMaximumWidth(200) 

    def __init__(self,canvas,parent=None,withToolbar=True,width=800,height=800,application=None):
        super(PlotWidget,self).__init__(parent)
        typ = type(canvas)
        if(typ!=PlotCanvas): raise Exception("Type "+str(typ)+" is not Canvas")
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.layout = QGridLayout(self)
        self.canvas = canvas
        self.navBar = NavigationToolbar2QT(self.canvas,self)
        self.App = application
        # Filter for right click on pan or zoom in navbar
        def event_filter(event):
            if event.button == 3:
                if self.navBar._active == 'PAN':
                    self.navBar.release_pan(event)
                if self.navBar._active == 'ZOOM': 
                    self.navBar.release_zoom(event)
        self.navBar.press = event_filter
        self.navBar._actions['zoom'].triggered.emit() # Set Zoom as default state 

        if(withToolbar):
            self.toolbar = plot_toolbar(self)
            self.setupInteralWidgets()
            self.setupToolbar()
            self.layout.addWidget(self.toolbar,1,1,1,2)

        self.op_mapping = {}

        self.layout.addWidget(self.canvas,2,1)
        self.layout.addWidget(self.navBar,3,1)
        self.resize(width,height)

        self.buildOpMap()

    def buildOpMap(self):
        self.op_mapping["canvas"] = self.canvas.parseOpStr
        self.op_mapping["analysis:derivate"]    = self.analysisWidget.derivitaveTrace
        self.op_mapping["analysis:integrate"]   = self.analysisWidget.integrateTrace
        self.op_mapping["analysis:fft"]         = self.analysisWidget.fouierTrasnformTrace

    def parseOpStr(self,opsStr):
        # print(opsStr)
        ops = opsStr.split(">>")
        for op in ops:
            print(op)
            fn,args = op.split("::")
            if fn == "canvas":
                self.op_mapping[fn](args)
                continue
            args = args.split("&")
            if args[0] == "":
                args = ()
            try:
                args = [ eval(arg) for arg in args ]
            except:
                print(f"Failed to parse arguments {args}")
                return
            fn = self.op_mapping[fn]
            fn(*args)
        pass

    def setupInteralWidgets(self):
        # Setup widget holder
        self.widgetHolder = QWidget(self)
        self.widgetHolder.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Minimum)
        self.holderLayout = QHBoxLayout(self.widgetHolder)
        self.layout.addWidget(self.widgetHolder,2,2,2,1)
        # Create Internal Widgets
        # Analysis
        self.analysisWidget = self.AnalysisWidget(self)
        self.analysisWidget.setVisible(False)
        # Analysis
        self.conversionWidget = self.ConversionWidget(self)
        self.conversionWidget.setVisible(False)
        # Metric
        self.metricsWidget = self.MetricsWidget(self)
        self.metricsWidget.setVisible(False)
        # Statistics
        self.statsWidget = self.StatisticsWidget(self)
        self.statsWidget.setVisible(False)
        # Gen Math
        self.mathWidget = self.MathInterpWidget(self)
        self.mathWidget.setVisible(False)
        # Values 
        self.valuesWidget = self.ValuesWidget(self)
        self.valuesWidget.setVisible(False)
        # Canvas Layout Widget
        self.layoutWidget = self.LayoutWidget(self)
        self.layoutWidget.rebuildGraphList()
        self.layoutWidget.setVisible(False)
        # Connect Traces changed signal for internal widgets
        self.canvas.tracesChanged.connect(self.updatePlotTraces)
        self.canvas.axesChanged.connect(self.updateAxesInformation)

    def setupToolbar(self):
        self.toolbar.addAction("Save",toggelable=False).triggered.connect(self.saveImage)
        self.toolbar.addAction("Copy","Ctrl+c",toggelable=False).triggered.connect(self.copyTracesInCanvas)
        self.toolbar.addAction("Paste","Ctrl+v",toggelable=False).triggered.connect(self.pasteTracesInCanvas)
        self.toolbar.addAction("Analysis").triggered.connect(self.analysisWidget.activate)#activateAnalysisWidget)
        self.toolbar.addAction("Conversions").triggered.connect(self.conversionWidget.activate)#self.activateMetricWidget)
        self.toolbar.addAction("Metrics").triggered.connect(self.metricsWidget.activate)#self.activateMetricWidget)
        self.toolbar.addAction("Statistics").triggered.connect(self.statsWidget.activate)#self.activateStatsWidget)
        self.toolbar.addAction("Math").triggered.connect(self.mathWidget.activate)#self.activateMathWidget)
        self.toolbar.addAction("Values").triggered.connect(self.valuesWidget.activate)#self.activateValuesWidget)
        self.toolbar.addAction("Layout").triggered.connect(self.layoutWidget.activate)#self.activateLayoutWidget)

    def keyPressEvent(self,event):
        self.canvas.keyPressEvent(event)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self,event):
        self.canvas.keyReleaseEvent(event)
        super().keyReleaseEvent(event)

    def pushIntoLayout(self,widget):
        self.holderLayout.addWidget(widget)
        self.resize(self.width()+widget.staticWidth,self.height())
        widget.setVisible(True)
        widget.active = True

    def popOutOfLayout(self,widget):
        self.canvas.setMinimumWidth(self.canvas.width())
        self.holderLayout.removeWidget(widget)
        widget.setVisible(False)
        widget.active = False
        self.resize(self.width()-widget.staticWidth,self.height())
        if not self.App is None: self.App.processEvents()
        self.canvas.setMinimumWidth(20)

    def updatePlotTraces(self):
        # print("Plots Updated")
        self.analysisWidget.rebuildGraphList()
        self.conversionWidget.rebuildGraphList()
        self.metricsWidget.rebuildGraphList()
        self.statsWidget.rebuildGraphList()
        self.mathWidget.rebuildGraphList()
        self.valuesWidget.rebuildGraphList()
        
    def updateAxesInformation(self):
        # print("Axes Changed")
        self.layoutWidget.rebuildGraphList()

    def copyTracesInCanvas(self):
        clip = QGuiApplication.clipboard()
        clip.setText(utils.traceDictToCsv(self.canvas.getAllTraces()))
        
    def pasteTracesInCanvas(self):
        try:
            clip = QGuiApplication.clipboard()
            traces = csvToTraceDict(clip.text())
            self.canvas.setPlotFromTraceDict(traces)
            self.canvas.plot(rescale=False)
        except Exception as e:
            print("Failed to Paste")
            print(e)

    def enableDarkTheme(self,enable=True):
        self.setAutoFillBackground(True)
        if enable:
            self.setPalette(utils.darkPalette())
            self.canvas.setTheme("dark")
        else:
            self.setPalette(utils.lightPalette())
            self.canvas.setTheme("light")

    def saveImage(self):
        
        try: 
            defName = list(self.canvas.traces.keys())[0]
        except:
            defName = 'image'
        defName = defName.replace("/","_")
        defName = defName.replace("(","_")
        defName = defName.replace(")","_")
        filename = QFileDialog.getSaveFileName(self,'Save Image',defName)[0]
        filename = filename.replace(" ","_") # I Will Force People not to use spaces :)
        self.canvas.fig.savefig(filename+".png")

    def dummy(self):
        # help(self.navBar.save_figure)
        print("Dummy function called")
        
        
