
"""
    TODO: Line Plot
        - Add Common Regression to analysis - Possibly new Widget
            - Linear
            - Polynomic (Add Line for Nth Order)
            - Sinusoidal
        - Add Metric Generation
            - Single Trace Metrics
                - Average
                - Max (X,Y)
                - Min (X,Y)
                - Noise Floor (Maybe)
                - Dynamic Range (Maybe)
            - Multi Trace Metrics
                - Correlation coefecient
                - ???
        - Add General Math Interpriter Widget
            - Generate Labels for each plot
                - If 3 plots there will be a list of key val pairs {y1:plot_1,y2:plot_2,y3:plot_3}
                - use these to do math -> {Name_of_graph} = {y1}**2+{y2}**2
                - {Name_of_graph} can also be an already created plot {y1} = {y1}**2+{y2}**2 
"""
#Std Lib
import copy
import time
import pickle

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

#Common 3rd Party Libs
import numpy as np


#########################################################
##                    2 Deminsional                    ##
#########################################################
class trace_2d():
    def __init__(self,name):
        self._x = np.array([])
        self._y = np.array([])
        self._name = ""
        self._trace = None
        self._axesID = None
        self._hasUpdated = False
        self._infoHasUpdated = False
        self._isSplit = False
    @property 
    def x(self):
        return self._x
    @x.setter
    def x(self,x):
        typ = type(x)
        if(typ == np.ndarray):
            self._x = x
        elif(typ == list):
            self._x = np.array(x)
        else:
            raise Exception("trace_2d data only accepts numpy array and lists")
        self._hasUpdated = True
    @property 
    def y(self):
        return self._y
    @y.setter
    def y(self,y):
        typ = type(y)
        if(typ == np.ndarray):
            self._y = y
        elif(typ == list):
            self._y = np.array(y)
        else:
            raise Exception("trace_2d data only accepts numpy array and lists")
        self._hasUpdated = True
    @property 
    def trace(self):
        return self._trace
    @trace.setter
    def trace(self,trace):
        self._trace = trace
    @property 
    def name(self):
        return self._name
    @name.setter
    def name(self,name):
        self._name = name
        self._infoHasUpdated = True
    @property
    def axesID(self):
        return self._axesID
    @axesID.setter
    def axesID(self,axesID):
        self._axesID = axesID
    @property
    def isSplit(self):
        return self._isSplit
    @isSplit.setter
    def isSplit(self,state):
        self._isSplit = bool(state)
    def update(self):
        redrawLegend = False
        if self._hasUpdated:
            self._trace.set_data(self.x,self.y)
        if self._infoHasUpdated:
            print("New Name",self._name)
            self._trace.set_label(self._name)
            redrawLegend = True
        self._hasUpdated = False
        self._infoHasUpdated = False
        return redrawLegend
          
class plot_canvas(FigureCanvasQTAgg):
    TracesChanged = pyqtSignal() #Signal for when the trace table has changed
    AxesChanged = pyqtSignal()   #Signal for when the plot window layout has changed
    def __init__(self,parent=None,width=5,height=4,dpi=100):
        self.VERSION = 1.0
        self.fig = Figure(figsize=(width,height),dpi=dpi,tight_layout=True) # Create the figure that will be holding and formating the axes
        self.axes = {0:self.fig.add_subplot(1,1,1)} # This is holds the axes for the canvas. The default is one axes but can be changed in setSubplots routine
        self.twin_axes = {} # This holds axis for split plots
        self.axesLegends = {0:0} # This Is a solution to tell the canvas weather or not a legend has been enabled for a axes
        super(plot_canvas,self).__init__(self.fig) # Initilize the FigureCanvasQTAgg Class as part of this Class
        self.defaultLabel = "Plot" # This sets what the default label of traces in the legend will be when not specified
        self.traces = {} # This holds trace data so that the canvas has a copy of the data
        self.N_defaults = 0 # This keeps track of howmany plots were created that use the defaultLabel
        #signals
        self.tracesChanged = self.TracesChanged # This is emited whenever the self.traces dictionary get changed 
        self.axesChanged = self.AxesChanged # This is emited whenever the self.axes dictionary gets changed
        #size policy
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) # Qt size polizy stuff
        #Color Theme
        self.theme_d = {"dark":darkTheme,
                        "light":lightTheme}
        self.Facecolor = self.fig.get_facecolor()
        self.Edgecolor = self.fig.get_edgecolor()
        #Right Click Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)

    def showMenu(self,event):
        if(event is None): return
        # Get mouse position as a ratio
        posx = event.x()/self.width()
        posy = 1-event.y()/self.height()
        # Determine Which Axes was clicked
        for k,a in reversed(list(self.axes.items())):
            apos = a.get_position()
            if(posx>apos.x0 and posx<apos.x1):
                if(posy>apos.y0 and posy<apos.y1):
                    selectedAxes = k
                    print("Selected Axes =",k)
                    break
        # If no axes is selected, return
        else:
            print("Error: Axes not found!")
            return            
        # Create a Menu
        menu = QMenu()
        # General
        rescale_action = QAction("Rescale", self)
        menu.addAction(rescale_action)
        
        # Per Plot
        traceActions = {}
        pointerList = []
        for (key,val) in self.traces.items(): 
            if val.axesID != selectedAxes: continue
            pointerList.append(QMenu(f"{val.name}"))
            # Attach Submenu
            menu.addMenu(pointerList[-1])
            pointer = pointerList[-1]
            # Plot Actions
            # Split
            pointerList.append(QAction("Split"))
            traceActions[pointerList[-1]] = (self.splitAxes,(key,))
            pointer.addAction(pointerList[-1])
            # Delete
            pointerList.append(QAction("Delete"))
            traceActions[pointerList[-1]] = (self.removePlot,(key,))
            pointer.addAction(pointerList[-1])
            
        action = menu.exec_(self.mapToGlobal(event))
        if action == rescale_action:
            self.rescale_y()
        elif not traceActions.get(action) is None:
            fn,args = traceActions[action]
            fn(*args)
            self.plot()
    
    def rescale_y(self):
        for i,axes in self.axes.items():
            xlim = axes.get_xlim()
            for trace in self.traces.values():
                maxa = -99e99; mina = 99e99
                if trace.axesID == i:
                    y_sel = trace.y[(trace.x>xlim[0]) & (trace.x<xlim[1])]
                    if mina>y_sel.min(): mina = y_sel.min()
                    if maxa<y_sel.max(): maxa = y_sel.max()
            axes.set_ylim(mina,maxa)
            self.draw()

    def setTheme(self,theme=None,**kwargs):
        typ = type(theme)
        facecolor = self.fig.get_facecolor
        edgecolor = self.fig.get_edgecolor
        if typ == str:
            theme = theme.lower()
            presetTheme = self.theme_d.get(theme)
            if not presetTheme is None:
                presetTheme(self)
                self.draw()
                return
            facecolor = theme
            edgecolor = theme
        if typ == tuple:
            facecolor = theme
            edgecolor = theme
        if typ == dict:
            facecolor = theme.get("facecolor")
            edgecolor = theme.get("edgecolor")
        if theme is None:
            facecolor = kwargs.get("facecolor")
            edgecolor = kwargs.get("edgecolor")
        self.fig.set_facecolor(facecolor)
        self.fig.set_edgecolor(edgecolor)
        self.Facecolor = facecolor
        self.Edgecolor = edgecolor
        for axes in self.axes.values():
            axes.set_facecolor(facecolor)
            # axes.set_edgecolor(edgecolor)
        self.draw()
        pass

    def setSubplots(self,*listOfCords,kwargs=[]):
        # This sets the subplot layout for the window. 
        # listOfCords is a list of matplotlib layout corrdenates
        # kwargs is a list of dictionaries for pass thorugh key word arguments
        #   into Figure().add_subplot(**)
        for axes in self.axes.values():
            axes.remove()
        lnDiff =  len(listOfCords) - len(kwargs) 
        for i in range(lnDiff):
            kwargs.append({})
            
        self.axes.clear()
        self.traces.clear()
        self.N_defaults = 0
        for (i,(x,y,n)),kw in zip(enumerate(listOfCords),kwargs):
            self.axes[i] = self.fig.add_subplot(x,y,n,**kw)
            self.axes[i].set_facecolor(self.Facecolor)
            # self.axes[i].set_edgecolor(self.Edgecolor)
            self.axesLegends[i] = 0
        self.axesChanged.emit()

    def setFigureName(self,name,*args):
        self.fig.suptitle(name)
        self.plot()

    def setXAxesNames(self,name,axesID=0):
        ntyp = type(name)
        atyp = type(axesID)
        if(ntyp == list):
            if(atyp != list):
                print("Loop Name")
            else:
                print("Loop Both")
        else:
            if(atyp != int):
                raise Exception("axesID must be a integer when name is not a list")
            self.axes[axesID].set_xlabel(name)
        self.plot()
        print("WIP")
    
    def setYAxesNames(self,name,axesID=0):
        ntyp = type(name)
        atyp = type(axesID)
        if(ntyp == list):
            if(atyp != list):
                print("Loop Name")
            else:
                print("Loop Both")
        else:
            if(atyp != int):
                raise Exception("axesID must be a integer when name is not a list")
            self.axes[axesID].set_ylabel(name)
        self.plot()
        print("WIP")

    def setAxesNames(self,name,axesID=0):
        ntyp = type(name)
        atyp = type(axesID)
        if(ntyp == list):
            if(atyp != list):
                print("Loop Name")
            else:
                print("Loop Both")
        else:
            if(atyp != int):
                raise Exception("axesID must be a integer when name is not a list")
            self.axes[axesID].set_title(name)
        self.plot()
        print(axesID,name)
        print("WIP")

    def toggleGrid(self,axesID=0):
        self.axes[axesID].grid()
        self.plot()

    def clearAllPlots(self):
        for axes in self.axes.values():
            axes.cla()
        self.traces.clear()
        self.N_defaults = 0

    def splitAxes(self,traceID):
        try:
            trace = self.traces[traceID]
        except:
            raise Exception("Cannot Find trace With Trace ID: "+str(traceID))
        trace.trace.remove()
        if trace.isSplit: return
        counter = 0
        for tr in self.traces.values():
            if tr.axesID == trace.axesID and not tr.isSplit: counter+=1
        if counter <= 1: return # There is only 1 plot here. Splitting does not make sense  
        try:
            tax = self.twin_axes[trace.axesID]
        except:
            tax = self.axes[trace.axesID].twinx()
            self.twin_axes[trace.axesID] = tax 
        trace.trace,*_ = tax.plot(trace.x, trace.y, color="tab:red")
        tax.tick_params(axis='y', labelcolor="tab:red")
        trace.isSplit = True
        self.resetColorCycle(trace.axesID)
        self.plot()

    def resetColorCycle(self,axesID = None):
        colors = rcParams['axes.prop_cycle'].by_key()['color']
        if not axesID is None:
            I = 0
            for i,tr in enumerate(self.traces.values()):
                if tr.axesID == axesID and not tr.isSplit:
                    tr.trace.set_color(colors[I%len(colors)])
                    I+=1
            Colors = colors[I:]
            Colors.extend(colors[:I])
            self.axes[axesID].set_prop_cycle(color=Colors)
        else:
            for axesID in self.axes.keys():
                colors = rcParams['axes.prop_cycle'].by_key()['color']
                I = 0
                for i,tr in enumerate(self.traces.values()):
                    if tr.axesID == axesID and not tr.isSplit:
                        tr.trace.set_color(colors[I%len(colors)])
                        I+=1
                Colors = colors[I:]
                Colors.extend(colors[:I])
                self.axes[axesID].set_prop_cycle(color=colors)

    def updatePlotName(self,oldLabel,newLabel,traceID=None):
        if(not traceID is None):
            self.traces[traceID].name = newLabel
        else:    
            if(self.traces.get(oldLabel) is None):
                raise Exception("No label found")
            trace = self.traces.pop(oldLabel)
            trace.name = newLabel
            self.traces[newLabel] = trace
        self.tracesChanged.emit()

    def removePlot(self,traceID):
        try:
            trace = self.traces.pop(traceID)
        except:
            print("Trace Does Not Exist")
        trace.trace.remove()
        count = 0
        for t in self.traces.values():
            count += t.axesID==trace.axesID
        if(count == 0): self.axes[trace.axesID].set_prop_cycle(None)
        else: self.resetColorCycle(trace.axesID)
        self.axes[trace.axesID].legend(loc="best")
        self.tracesChanged.emit()

    def setPlot(self,xy,y=None,label=None,traceID=None,subPlotID = None,legend=True,args=[],**kwargs):
        if(y is None):
                y = np.copy(xy)
                xy = np.linspace(0,len(y)-1,len(y))
        else:
            pass
        if(label is None): 
            label = self.defaultLabel+"_"+str(self.N_defaults)
            self.N_defaults += 1
        else:
            pass
        if(traceID is None):
            traceID = label
        if(subPlotID is None):
            subPlotID = 0
        if(self.traces.get(traceID) is None):
            newTrace = trace_2d(label)
            self.traces[traceID] = newTrace
            newTrace.x = xy
            newTrace.y = y
            newTrace._name = label
            newTrace.axesID = subPlotID
            newTrace.trace,*_ = self.axes[subPlotID].plot(newTrace.x,newTrace.y,*args,**kwargs)
            newTrace.trace.set_label(newTrace._name)
            if legend: self.axes[subPlotID].legend(loc="best") # <--- This probably needs to be moved to another location
            self.axesLegends[subPlotID] = legend
            newTrace.update()
            self.tracesChanged.emit()
        else:
            trace = self.traces[traceID]
            trace.x = xy
            trace.y = y
            trace.update()
    
    def setPlotFromTraceDict(self,traces):
        traces = copy.copy(traces)
        for key,val in traces.items():
            self.setPlot(val.x,val.y,label=val.name,traceID=key,subPlotID=val.axesID)

    def getAllTraces(self):
        return self.traces

    def getTrace(self,traceID):
        return self.traces[traceID]

    def getAxes(self,axesID):
        try:
            axes = self.axes[axesID]
            return axes
        except Exception as e:
            print("Failed getAxes call witht the following:")
            print("\t",e)

    def plot(self,rescale = True):
        self.N_defaults = 0
        if(rescale):
            for axes in self.axes.values():
                axes.relim()
                axes.autoscale_view()
            for axes in self.twin_axes.values():
                axes.relim()
                axes.autoscale_view()
        redraw = {}
        for trace in self.traces.values():
            if trace.update(): redraw[trace.axesID] = True
        for axesID in redraw.keys():
            print("Calling legend",axesID)
            self.axes[axesID].legend(loc="best")
        self.draw()

class plot_toolbar(QWidget):
    def __init__(self,parent=None):
        super(plot_toolbar,self).__init__(parent)
        self.setMaximumHeight(50)
        self.layout = QGridLayout(self)
        self.toolbar = QToolBar(self)
        self.layout.addWidget(self.toolbar)
        self.actions = []
    def addAction(self,name,shortcut=None):
        newAction = QAction(name,self)
        if(not shortcut is None): newAction.setShortcut(shortcut)
        self.actions.append(newAction)
        self.toolbar.addAction(newAction)
        return newAction

class plot_widget(QWidget):
    class InternalWidget():
        #This just hold variables that all Internal widgets will need
        def __init__(self,*args):
            self.active = False
            self.graphNameToID = {}
            self.graphNameToAxisID = {}
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
            I = Counter()
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
            self.layout.addWidget(self.graphSelectLabel2,I(),1)
            self.layout.addWidget(self.graphSelectBox2,I(),1)
            self.layout.addWidget(self.multiTraceLbl,I(),1)
            self.layout.addWidget(self.addGraphsBtn,I(),1)
            self.layout.addWidget(self.subGraphsBtn,I(),1)
            self.layout.addWidget(self.mulGraphsBtn,I(),1)
            self.layout.addWidget(self.divGraphsBtn,I(),1)
            self.layout.addItem(QSpacerItem(0,0,QSizePolicy.Minimum,QSizePolicy.Expanding),99,1)
        
        def graphSelectionChanged(self,index):
            self.selectedIndex = index
            self.graphSelectLine.setText(self.graphSelectBox.currentText())
        
        def graphLabelChanged(self):
            traceName,traceID,axesID,trace = self.getSelectedGraph()
            self.Parent.canvas.updatePlotName(traceName,self.graphSelectLine.text(),traceID)
            self.Parent.canvas.plot()

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

        def removeTrace(self):
            traceName = self.graphSelectBox.currentText()
            index = self.graphSelectBox.currentIndex()
            if self.selectedIndex > index: self.selectedIndex = 0
            elif self.selectedIndex == index: self.selectedIndex = 0
            try:
                traceID = self.graphNameToID[traceName]
                self.Parent.canvas.removePlot(traceID)
                self.Parent.canvas.plot()
            except Exception as e:
                print(e)
                return

        def getSelectedGraph(self):
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def getSelectedGraph2(self):
            self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
            traceName = self.graphSelectBox2.itemText(self.selectedIndex2)
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
                newX = np.copy(trace.x)
                newY = np.copy(trace.y)
                kernal = np.ones(value)/value
                newY = np.convolve(kernal,newY,mode="same")
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot()

        def flipTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                trace.y = np.flip(trace.y)
            except Exception as e:
                print(e)
                return
            # self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot()

        def derivitaveTrace(self):
            try:
                traceName,traceID,axesID,trace = self.getSelectedGraph()
                newName = "Δ"+traceName
                newX = np.copy(trace.x)
                newY = np.copy(trace.y)
                # kernal = np.ones(value)/value
                newY = newY[1:] - newY[:-1]
                newX = newX[1:] 
            except Exception as e:
                print(e)
                return
            self.Parent.canvas.setPlot(newX,newY,label=newName,subPlotID=axesID)
            self.Parent.canvas.plot()
        
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
            self.Parent.canvas.plot()

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
            self.Parent.canvas.plot()  
    
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
            self.Parent.canvas.plot()
        
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
            self.Parent.canvas.plot()
        
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
            self.Parent.canvas.plot()
        
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
            self.Parent.canvas.plot()

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
            I = Counter()
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
            self.titleLbl = QLabel("- WIP -",self)
            self.titleLbl.setAlignment(Qt.AlignCenter)
            
            self.graphSelectLabel = QLabel("Graph Selection",self)
            self.graphSelectBox = QComboBox(self)
            self.graphSelectBox.currentIndexChanged.connect(self.graphSelectionChanged)
            
            self.graphSelectLine = QLabel("",self)

            self.multiTraceLbl = QLabel("- Multi Trace Math -",self)
            self.multiTraceLbl.setAlignment(Qt.AlignCenter) 

            self.graphSelectLabel2 = QLabel("Graph Selection 2",self)
            self.graphSelectBox2 = QComboBox(self)
            self.graphSelectBox2.currentIndexChanged.connect(self.graphSelectionChanged2)
            
            #Build layout
            I = Counter()
            I.set(1)
            
            self.layout.addWidget(self.titleLbl,I(),1)

            self.layout.addWidget(self.graphSelectLabel,I(),1)
            self.layout.addWidget(self.graphSelectBox,I(),1)
            self.layout.addWidget(self.graphSelectLine,I(),1)
            
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
            self.Parent.canvas.plot()

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
            self.graphSelectBox.setCurrentIndex(self.selectedIndex)
            traceName = self.graphSelectBox.itemText(self.selectedIndex)
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

        def getSelectedGraph2(self):
            self.graphSelectBox2.setCurrentIndex(self.selectedIndex2)
            traceName = self.graphSelectBox2.itemText(self.selectedIndex2)
            traceID = self.graphNameToID[traceName]
            axesID = self.graphNameToAxisID[traceName]
            trace = self.Parent.canvas.getTrace(traceID)
            return traceName,traceID,axesID,trace

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
            I = Counter()
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
            for i,(key,val) in enumerate(traces.items()):
                self.graphNameToID[val.name] = key
                self.graphNameToAxisID[val.name] = val.axesID
                xID = self.xID+str(i)
                yID = self.yID+str(i)
                self.idToGraphName[xID] = val.x
                self.idToGraphName[yID] = val.y
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
            # if min(lenList) != max(lenList) :
            #     Max = max(lenList)
            #     Maxx = np.arange(Max)
            #     for key,val in self.idToGraphName.items():
            #         x = np.linspace(0,len(val)-1,Max)
            #         tmpTable[key] = np.interp(Maxx,x,val)
            # else:
            tmpTable = self.idToGraphName
            print(self.yInterpreterLn.text())
            name = self.graphNameLn.text()
            if name == "": name = "nan"
            try:
                if self.yInterpreterLn.text() != "":
                    y = MathInterpreter.interpretString(self.yInterpreterLn.text(),tmpTable)
                else:
                    return
                if self.xInterpreterLn.text() != "":
                    x = MathInterpreter.interpretString(self.xInterpreterLn.text(),tmpTable)
                else:
                    x = np.arange(len(y))
            except Exception as e:
                print(e)
                return
            if(x.size < y.size): y = y[:x.size]
            if(y.size < x.size): x = x[:y.size]
            self.Parent.canvas.setPlot(x,y,label=name)
            self.Parent.canvas.plot()
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
            I = Counter()
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
            self.Parent.canvas.plot()

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
            for x,y in zip(trace.x,trace.y):
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
                    self.layout.itemAt(i).widget().setParent(None)
            except:
                return
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

    def __init__(self,canvas,parent=None,withToolbar=True):
        super(plot_widget,self).__init__(parent)
        typ = type(canvas)
        if(typ!=plot_canvas): raise Exception("Type "+str(typ)+" is not plot_canvas")
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.layout = QGridLayout(self)
        self.canvas = canvas
        self.navBar = NavigationToolbar2QT(self.canvas,self)

        if(withToolbar):
            self.toolbar = plot_toolbar(self)
            self.setupInteralWidgets()
            self.setupToolbar()
            self.layout.addWidget(self.toolbar,1,1,1,2)

        self.layout.addWidget(self.canvas,2,1)
        self.layout.addWidget(self.navBar,3,1)

    def setupToolbar(self):
        self.toolbar.addAction("Save").triggered.connect(self.dummy)
        self.toolbar.addAction("Copy","Ctrl+c").triggered.connect(self.copyTracesInCanvas)
        self.toolbar.addAction("Paste","Ctrl+v").triggered.connect(self.pasteTracesInCanvas)
        self.toolbar.addAction("Analysis").triggered.connect(self.analysisWidget.activate)#activateAnalysisWidget)
        self.toolbar.addAction("Metrics").triggered.connect(self.metricsWidget.activate)#self.activateMetricWidget)
        self.toolbar.addAction("Statistics").triggered.connect(self.statsWidget.activate)#self.activateStatsWidget)
        self.toolbar.addAction("Math").triggered.connect(self.mathWidget.activate)#self.activateMathWidget)
        self.toolbar.addAction("Values").triggered.connect(self.valuesWidget.activate)#self.activateValuesWidget)
        self.toolbar.addAction("Layout").triggered.connect(self.layoutWidget.activate)#self.activateLayoutWidget)

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

    def pushIntoLayout(self,widget):
        widget.setVisible(True)
        self.holderLayout.addWidget(widget)
        widget.active = True

    def popOutOfLayout(self,widget):
        widget.setVisible(False)
        self.holderLayout.removeWidget(widget)
        widget.active = False

    def updatePlotTraces(self):
        print("Plots Updated")
        self.analysisWidget.rebuildGraphList()
        self.metricsWidget.rebuildGraphList()
        self.statsWidget.rebuildGraphList()
        self.mathWidget.rebuildGraphList()
        self.valuesWidget.rebuildGraphList()
        
    def updateAxesInformation(self):
        print("Axes Changed")
        self.layoutWidget.rebuildGraphList()

    def copyTracesInCanvas(self):
        clip = QGuiApplication.clipboard()
        clip.setText(traceDictToCsv(self.canvas.getAllTraces()))
        
    def pasteTracesInCanvas(self):
        try:
            clip = QGuiApplication.clipboard()
            traces = csvToTraceDict(clip.text())
            self.canvas.setPlotFromTraceDict(traces)
            self.canvas.plot()
        except Exception as e:
            print("Failed to Paste")
            print(e)

    def enableDarkTheme(self,enable=True):
        self.setAutoFillBackground(True)
        if enable:
            self.setPalette(darkPalette())
            self.canvas.setTheme("dark")
        else:
            self.setPalette(lightPalette())
            self.canvas.setTheme("light")

    def dummy(self):
        print("Dummy function called")

#########################################################
##                   Plot Color Mesh                   ##
#########################################################
# ~TODO: v---THIS---v
# Basing this on QPixmap since this gives a bit more preformance 
#   at the price of being more manual to create. hopefully this 
#   will allow even video to be played through this. Though for that
#   it may need to be optimized even further.
#
# !!!! THIS IS NOT WHERE NEAR COMPLETE !!!!
# !!!! USING THIS WILL NOT WORK !!!!

class _painterCanvas(QWidget):
    def __init__(self,parent):
        super(_painterCanvas,self).__init__(parent)
        self.Parent = parent
        self._lineColor = QColor(0,0,0)
        self._backgroundColor = QColor(255,255,255)
        self._showFrame = True
        self._showMinorTicks = True
        self._showMajorTicks = True
        self._showBackground = True
        self._fullWidth = 0
        self._frameWidth = 0
        self._fullHeight = 0
        self._frameHeight = 0
        self._xOffset = 0
        self._yOffset = 0
        self._x = 0
        self._y = 0
        self._spacing = 0
        self._draw = True
        self._calculateFrameSize()

    def enableDraw(self,enable:bool):
        if(enable): self._draw = True
        else: self._draw = False

    def resizeEvent(self,event):
        self._calculateFrameSize()

    def paintEvent(self,event):
        # timer = testTimer()
        # timer.start()
        if(not self._draw): 
            # print(timer.reset())
            return
            
        qp = QPainter()
        qp.begin(self)
        if(self._showFrame):
            self._drawFrame(event, qp)
        if(self._showBackground):
            self._drawBackground(event,qp)
        if(self._showMajorTicks):
            self._drawMajorTicks(event,qp)
        if(self._showMajorTicks):
            self._drawMinorTicks(event,qp)
        qp.end()

        # print(timer.reset())
    def _calculateFrameSize(self):
        self._fullWidth = self.width()-1
        self._fullHeight = self.height()-1
        self._frameWidth = self.width()-1-self._spacing
        self._frameHeight = self.height()-1-self._spacing
        self._xOffset = int(self._spacing/2)
        self._yOffset = int(self._spacing/2)
        self._x = 0
        self._y = 0
    def _drawBackground(self,event,qp):
        qp.setPen(self._backgroundColor)
        qp.fillRect(self._x,self._y,self._xOffset,self._fullHeight,self._backgroundColor)
        qp.fillRect(self._x,self._y,self._fullWidth,self._yOffset,self._backgroundColor)
        qp.fillRect(self._xOffset+self._frameWidth+1,self._y,self._xOffset,self._fullHeight,self._backgroundColor)
        qp.fillRect(self._x,self._yOffset+self._frameHeight+1,self._fullWidth,self._yOffset,self._backgroundColor)
        # qp.eraseRect(self._xOffset,self._yOffset,self._frameWidth,self._frameHeight)
    def _drawFrame(self, event, qp):
        qp.setPen(self._lineColor)
        qp.drawRect(self._xOffset,self._yOffset,self._frameWidth,self._frameHeight)
    def _drawMajorTicks(self, event, qp):
        # Draw the major tick lines
        qp.setPen(self._lineColor)
    def _drawMinorTicks(self,event,qp):
        # Draw the minor Tick Lines
        qp.setPen(self._lineColor)

class _pixmap_wrapper(QWidget):
    """
        Backend wrapper of QLabel and Pixmap

        Idea:
            To have a single QWidget that can be orginized using 
                QLayouts but also auto calculates data to images
                while holding the original data.
            Calculations to include:
                x- Non-Linear Data Interpolation
                x- Auto scaling to min and max values
                x- Values to Color mapping
                x- Auto rescale size
                .
                .
                .
            Formating 
                - Mesh Title
                - Y Label
                - X Label
                - Y Ticks
                - X Ticks
            y
            ^
            *
            *
            *
            *       IMAGE AXES
            *
            *
            *
            *
            * * * * * * * * * * * * -> x
    """
    def __init__(self,parent):
        super(_pixmap_wrapper,self).__init__(parent)
        self.__pixmap = QPixmap(1,1)
        self.__pixmap.fill(QColor(Qt.white))
        # self.__img = QImage()
        self.layout = QGridLayout(self)
        self._spacing = (50,50,50,50)
        self.innerLayout = QGridLayout()
        self.innerLayout.setContentsMargins(*self._spacing)
        self.layout.addLayout(self.innerLayout,0,0)
        self._label = QLabel(self)
        self.innerLayout.addWidget(self._label,0,0)
        self._paintCanvas = _painterCanvas(self)
        self._paintCanvas._spacing = self._spacing[0]*2
        self.layout.addWidget(self._paintCanvas,0,0)
        self._label.setPixmap(self.__pixmap)
        self._z = None
        self._y = None
        self._x = None
        self._Ny = None
        self._Nx = None
        self._img = None
        self._scaleMin = None
        self._scaleMax = None
        self._colorList = list(colorMap.keys())
        self._selectedColorMap = colorMap["jet"]
        self._selectedColor = "jet"
        self._hasUpdated = False
        self._label.setScaledContents( True )
        self._lineColor = QColor(0,0,0)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) # Qt size polizy stuff

    # Getter and Setters for class Properties
    @property
    def x(self)->np.ndarray:
        return self._x
    @x.setter
    def x(self,x):
        typ = type(x)
        if(typ == np.ndarray):
            self._x = x
        elif(typ == list):
            self._x = np.array(x)
        else:
            raise Exception("only accepts numpy array and lists")
        self._hasUpdated = True
    @property
    def y(self)->np.ndarray:
        return self._y
    @y.setter
    def y(self,y):
        typ = type(y)
        if(typ == np.ndarray):
            self._y = y
        elif(typ == list):
            self._y = np.array(y)
        else:
            raise Exception("only accepts numpy array and lists")
        self._hasUpdated = True
    @property
    def z(self)->np.ndarray:
        return self._z
    @z.setter
    def z(self,z):
        typ = type(z)
        if(typ == np.ndarray):
            self._z = z
        elif(typ == list):
            self._z = np.array(z)
        else:
            raise Exception("only accepts numpy array and lists")
        self._hasUpdated = True 
    @property
    def Nx(self):
        return self._Nx
    @Nx.setter
    def Nx(self,Nx):
        try:
            Nx = float(Nx)
        except:
            raise Exception("Minimum Scale Value cannot be converted to a float")
        self._Nx = Nx
        self._hasUpdated = True  
    @property
    def Ny(self):
        return self._Ny
    @Ny.setter
    def Ny(self,Ny):
        try:
            Ny = float(Ny)
        except:
            raise Exception("Minimum Scale Value cannot be converted to a float")
        self._Ny = Ny
        self._hasUpdated = True  
    @property
    def img(self):
        return self._img
    @img.setter
    def img(self,img):
        typ = type(img)
        if(typ == np.ndarray):
            pass #self._Ny = Ny
        elif(typ == list):
            img = np.array(img,dtype="uint8")
        else:
            raise Exception("only accepts numpy array and lists")
        if(img.dtype != "uint8"):
            raise Exception("Image data not the correct type: Input type="+str(img.dtype)+"!='uint8'")
        if(img.ndim != 3):
            raise Exception("Image data not correct diminsions: Input dims="+str(img.ndim)+"!=3")
        if(img.shape[2]!=4):
            raise Exception("Image data is not formated as RGBA")
        self._img = img    

        self._hasUpdated = True
    @property
    def colorList(self):
        return self._colorList
    @property
    def selectedColor(self):
        return self._selectedColor
    @selectedColor.setter
    def selectedColor(self,txt):
        mappingFunction = colorMap.get(txt)
        if mappingFunction is None:
            raise Exception("Color map not found in matplotlib's cmap_d")
            return
        self._selectedColorMap = mappingFunction
        self._selectedColor = txt
    @property
    def scaleMin(self):
        return self._scaleMin
    @scaleMin.setter
    def scaleMin(self,Min):
        try:
            Min = float(Min)
        except:
            raise Exception("Minimum Scale Value cannot be converted to a float")
        self._scaleMin = Min
    @property
    def scaleMax(self):
        return self._scaleMax
    @scaleMax.setter
    def scaleMax(self,Max):
        try:
            Max = float(Max)
        except:
            raise Exception("Maximum scale value cannot be converted to a float")
        self._scaleMax = Max
    @property
    def spacing(self):
        return self._spacing
    @spacing.setter
    def spacing(self,def_top,bottom=None,left=None,right=None):
        if(bottom is None):
            self._spacing = (int(def_top),
                             int(def_top),
                             int(def_top),
                             int(def_top))
        else:
            self._spacing = (int(def_top),
                             int(bottom),
                             int(left),
                             int(right))

    def setFast(self,enable:bool):
        self._paintCanvas.enableDraw(enable)

    def setData(self,xz,y=None,z=None,*args,Nx=None,Ny=None,Min=None,Max=None,interp=False,**kwargs):
        # Check for correct inputs
        if (y is None and z is None) or (not y is None and not z is None) : pass
        else: raise Exception("X and Y data must either both be set or both be unset")
        # Orginize Data
        if (y is None):
            z = xz
            y = np.linspace(0,z.shape[0]-1,z.shape[0])
            x = np.linspace(0,z.shape[1]-1,z.shape[1])
        else :
            x = xz
        # Check and setup resolution
        if Nx is None:
            Nx = z.shape[1]
        if Ny is None:
            Ny = z.shape[0]
        self.Nx = Nx
        self.Ny = Ny
        self.x = x
        self.y = y
        self.z = z
        # Format Data
        if interp: self.interpolateData()
        if Min is None: self.scaleMin = self.z.min()
        else: self.scaleMin = Min
        if Max is None: self.scaleMax = self.z.max()
        else: self.scaleMax = Max
        self.applyColorMap()

    def setImg(self,img):
        """
        Array or list in the format of RGBA8888
        """
        self.img = img

    def interpolateData(self,mode="bilinear"):
        """
        Modes:
            - Bilinear
            - x
            - y
        """
        linX = np.linspace(self.x.min(),self.x.max(),self.Nx)
        linY = np.linspace(self.y.min(),self.y.max(),self.Ny)
        if mode.lower()=="bilinear":
            for i in range(self.z.shape[1]):self.z[i] = np.interp(linX,self.x[i],self.z[i])
            self.z = self.z.transpose() 
            for i in range(self.z.shape[1]):self.z[i] = np.interp(linY,self.x[i],self.z[i])
            self.z = self.z.transpose()
        elif mode.lower()=="x":
            for i in range(self.z.shape[1]):self.z[i] = np.interp(linX,self.x[i],self.z[i])
        elif mode.lower()=="y":
            self.z = self.z.transpose() 
            for i in range(self.z.shape[1]):self.z[i] = np.interp(linY,self.x[i],self.z[i])
            self.z = self.z.transpose()
        else:
            raise Exception("Mode '"+str(mode)+"' not found")

    def applyColorMap(self):
        tmpZ = (self.z-self.scaleMin)
        tmpZ /= self.scaleMax
        tmpZ = tmpZ.clip(0,1)
        tmpZ *= 255
        tmpZ = tmpZ.astype(int)
        self.img = (self._selectedColorMap(tmpZ)*255).astype("uint8")

    def draw(self):
        """
            Draws the RGBA data stored in self.img
        """
        # Determine Image deminsions
        height,width,channel = self.img.shape
        bytesPerLane = channel*width
        # Convert RGBA Data to a QImage
        qimg = QImage(self.img.data,width,height,bytesPerLane,QImage.Format_RGBA8888)
        # Cannot figure out how to display an image without recreating the pixmap everytime...
        # If the pixmap only needs to be created on different sized arrays then this could be a lot faster
        """
        if(self.__pixmap.width() != width or self.__pixmap.height() != height):
            self.__pixmap = QPixmap(qimg)
        else:
            self.__pixmap.fromImage(qimg)
        """
        self.__pixmap = QPixmap(qimg)
        self._label.setPixmap(self.__pixmap)#.scaled(self.width(),self.height()))
        # Queue the QLabel repaint function
        self.update()

class mesh_canvas(QWidget):
    """
    Canvas for color mesh plots:
    
    Idea:
        This class will keep track of color plots and the layouts
            for those color plots. This will also orginize tick marks,
            color scales bars, as well as other standared colorplot 
            visual tools.
    """
    # This Controls the layout
    TracesChanged = pyqtSignal() #Signal for when the trace table has changed
    AxesChanged = pyqtSignal()   #Signal for when the plot window layout has changed
    def __init__(self,parent=None,width=5,height=4,dpi=100):
        super(mesh_canvas,self).__init__(parent)
        self.layout = QGridLayout
        pass

    def setSubplots(self,*listOfCords,kwargs=[]):
        pass

    def setFigureName(self,name,*args):
        pass

    def setXAxesNames(self,name,axesID=0):
        pass
    
    def setYAxesNames(self,name,axesID=0):
        pass

    def setAxesNames(self,name,axesID=0):
        pass

    def clearAllPlots(self):
        pass

    def updatePlotName(self,oldLabel,newLabel,traceID=None):
        pass

    def removePlot(self,traceID):
        pass

    def setPlot(self,xyz,yz=None,z=None,label=None,traceID=None,subPlotID = None,legend=True,**kwargs):
        pass
    
    def setPlotFromTraceDict(self,traces):
        pass

    def getAllTraces(self):
        pass

    def getTrace(self,traceID):
        pass

    def getAxes(self,axesID):
        pass

    def plot(self,rescale = True):
        pass

class colorMesh_widget(QWidget):
    def __init__(self,canvas,parent=None):
        super().__init__(parent)
        self.canvas = canvas

#########################################################
##                       Utils                         ##
#########################################################

def traceDictToCsv(dict,sep="\t"):
    NAMES = []
    DATA = []
    nTraces = len(dict.values())
    maxLength = 0
    
    for key,val in dict.items():
        metaNameX = val.name+"%"+"X"+"%"+str(val.axesID)
        metaNameY = val.name+"%"+"Y"+"%"+str(val.axesID)
        NAMES.append(metaNameX)
        NAMES.append(metaNameY)
        DATA.append(val.x)
        DATA.append(val.y)
    
    fullDat = np.column_stack((NAMES,DATA)).transpose()
    csv = np.array2string(fullDat,separator=sep,max_line_width=255,threshold=1_000_000,formatter={'str_kind': lambda x: x})
    csv = csv.replace('[',"")
    csv = csv.replace(']',"")
    return csv

def csvToTraceDict(csv,sep="\t"):
    if sep != ",":
        csv = csv.replace(",","")
    csv = csv.split('\n')
    Names = csv[0].split(sep)
    Data = csv[1:]
    stringArray = []
    oldLength = 0
    for dat in Data[:]:
        newdat = dat.split(sep)
        if len(newdat) < oldLength: continue
        oldLength = len(newdat)
        stringArray.append(newdat)
    Data = np.array(stringArray,dtype=float).transpose()
    traceDict = {}
    for NAME,DAT in zip(Names,Data): 
        print(NAME)
        name = NAME.split('%')
        trace_name = name.pop(0)
        if traceDict.get(trace_name) is None:
            trace = trace_2d(trace_name)
            traceDict[trace_name] = trace
            fill_other_array = False
        else:
            trace = traceDict[trace_name]
            fill_other_array = True
        trace.name = trace_name
        Nargs = len(name)
        if Nargs>0:
            xy = name.pop(0)
            if xy == "X":
                trace.x = DAT
            else:
                trace.y = DAT
        else:
            trace.y = DAT
        Nargs = len(name)
        if Nargs>0:
            axesID = name.pop(0)
            try:
                trace.axesID = int(axesID)
            except:
                trace.axesID = 0
    for trace in traceDict.values():
        print(trace.name)
        print(trace.y.size)
        print(trace.x.size)
        if trace.x.size == 0:
            trace.x = np.arange(trace.y.size)
        if trace.y.size == 0:
            trace.y = np.zeros(trace.x.size)
    return traceDict

def setTheme(canvas,facecolor,edgecolor,tickcolor):
    canvas.setTheme(facecolor)
    for axes in canvas.axes.values():
        for xline,yline in zip(axes.get_xticklines(),axes.get_yticklines()):
            xline.set_color(tickcolor)
            yline.set_color(tickcolor)
        for xline,yline in zip(axes.get_xticklabels(),axes.get_yticklabels()):
            xline.set_color(tickcolor)
            yline.set_color(tickcolor)
        for xline,yline in zip(axes.get_xgridlines(),axes.get_ygridlines()):
            xline.set_color(tickcolor)
            yline.set_color(tickcolor) 
        for line in axes.spines.values():
            line.set_color(tickcolor)
    for axes in canvas.twin_axes.values():
        for xline,yline in zip(axes.get_xticklines(),axes.get_yticklines()):
            xline.set_color(tickcolor)
            yline.set_color(tickcolor)
        for xline in axes.get_xticklabels():
            xline.set_color(tickcolor)
            # yline.set_color(tickcolor)
        for xline,yline in zip(axes.get_xgridlines(),axes.get_ygridlines()):
            xline.set_color(tickcolor)
            yline.set_color(tickcolor) 
        for line in axes.spines.values():
            line.set_color(tickcolor)

def darkTheme(canvas):
    facecolor = (0.207,0.207,0.207,1)
    edgecolor = facecolor
    tickcolor = (0.95,0.95,0.95,1)
    setTheme(canvas,facecolor,edgecolor,tickcolor)

def lightTheme(canvas):
    facecolor = (1,1,1,1)
    edgecolor = facecolor
    tickcolor = (0,0,0,1)
    canvas.setTheme(facecolor)
    setTheme(canvas,facecolor,edgecolor,tickcolor)

def darkPalette():
    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    return dark_palette

def lightPalette():
    palatte = QWidget().palette()
    return palatte

class Counter:
    def __init__(self):
        self._i = int(0)
    def reset(self):
        self._i = int(0)
    def set(self,val):
        self._i = int(val)
    def __call__(self):
        i = self._i
        self._i+=1
        return i

class testTimer():
    def __init__(self):
        self.startTime = 0
        self.sliceTime = 0
        self.stopTime = 0
    def start(self):
        # time.clock_settime_ns(self.clk_id,0)
        self.startTime = time.perf_counter_ns()
        self.sliceTime = self.startTime
    def getSlice(self):
        t = self.sliceTime
        self.sliceTime = time.perf_counter_ns() 
        return self.sliceTime-t
    def reset(self):
        t = time.perf_counter_ns()-self.startTime
        self.startTime = time.perf_counter_ns()
        self.sliceTime = self.startTime
        return t
    
# ~TODO: Add functions to this
class MathInterpreter():
    """
    Interprets strings of data and returns a dictionary of 
        references and a function that takes thouse references
        and operates on it.
    
    This is geared to work with numpy arrays
    """
    refStart = "{"
    refStop = "}"
    storedFunction = lambda *kwargs: [0]
    exampleString = r"{y2}/({y0}+{y1})-1"
    # Eventually replace all these functions with thier program counterparts
    knownFunctions = {
        "fft"    :   "np.fft.fft",
        "csum"  :   "np.cumsum",
        "max"   :   "np.max",
        "min"   :   "np.min",
        "avg"   :   "np.mean",
        "filter":   "MathInterpreter.conv"
    }

    @staticmethod
    def interpretString(string:str,valTable:dict):
        string.replace(" ","")
        for key,val in valTable.items():
            string = string.replace(
                MathInterpreter.refStart+key+MathInterpreter.refStop,
                "valTable['{0}']".format(key))
        for key,val in MathInterpreter.knownFunctions.items():
            string = string.replace(key,val)
        string = string
        return eval(string)

    @staticmethod
    def conv(a1,a2):
        return np.convolve(a1,a2,mode="same")

#EOF
