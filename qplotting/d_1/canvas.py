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
# from matplotlib.cm import cmap_d as colorMap
from matplotlib.pyplot import rcParams 
from matplotlib.transforms import BboxTransformTo,Bbox

#Common 3rd Party Libs
import numpy as np

#utils
# from .plot_utils import *
from .trace import Trace
from . import utils

class PlotCanvas(FigureCanvasQTAgg):
    TracesChanged = pyqtSignal() #Signal for when the trace table has changed
    AxesChanged = pyqtSignal()   #Signal for when the plot window layout has changed
    # KeyPressed = pyqtSignal(int)
    def __init__(self,parent=None,width=5,height=4,dpi=100):
        self.VERSION = 1.0
        self.isGridOn = False
        self.legendLoc = "best"#"bottom right"#"best"
        self.legendKwargs = {
            # "mode" : "expand",
            # "bbox_transform" : BboxTransformTo(Bbox(np.array([[0,0],[width,height]]))),
        }
        self.fig = Figure(figsize=(width,height),dpi=dpi,tight_layout=True) # Create the figure that will be holding and formating the axes
        self.axes = {0:self.fig.add_subplot(1,1,1)} # This is holds the axes for the canvas. The default is one axes but can be changed in setSubplots routine
        self.twin_axes = {} # This holds axis for split plots
        self.axesLegends = {0:0} # This Is a solution to tell the canvas weather or not a legend has been enabled for a axes
        super(PlotCanvas,self).__init__(self.fig) # Initilize the FigureCanvasQTAgg Class as part of this Class
        self.defaultLabel = "Plot" # This sets what the default label of traces in the legend will be when not specified
        self.traces = {} # This holds trace data so that the canvas has a copy of the data
        self.N_defaults = 0 # This keeps track of howmany plots were created that use the defaultLabel
        
        #Operation Mapping
        self.op_mapping = {}

        #signals
        self.tracesChanged = self.TracesChanged # This is emited whenever the self.traces dictionary get changed 
        self.axesChanged = self.AxesChanged # This is emited whenever the self.axes dictionary gets changed
        #size policy
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) # Qt size polizy stuff
        #Color Theme
        self.theme_d = {"dark":utils.darkTheme,
                        "light":utils.lightTheme}
        self.Facecolor = self.fig.get_facecolor()
        self.Edgecolor = self.fig.get_edgecolor()
        #Right Click Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)
        self.installEventFilter(self)
        self.key_combo = []
        self.keyPressLookup = utils.FN_MAPPING_1D
        self.keyPressLookup[utils.KC_make(utils.K.a,utils.K.shift)] = self.annotateAll
        self.keyPressLookup[utils.KC_make(utils.K.a,utils.K.ctl)]   = self.annotateAll

        self.buildOpMap()
    
    #
    # Operational Parser
    #

    def buildOpMap(self):
        self.op_mapping["pushDown"] = self.pushDownTrace
        self.op_mapping["pushUp"] = self.pushUpTrace
        self.op_mapping["remove"] = self.removePlot
        self.op_mapping["xbounds"] = self.setXLim
        self.op_mapping["fitY"] = self.rescale_y
        pass
    
    def parseOpStr(self,opsStr):
        ops = opsStr.split(">")
        for op in ops:
            if op.count(":"): 
                fn,args = op.split(":")
                args = args.split("&")    
                try:
                    args = [ eval(arg) for arg in args ]
                except:
                    print(f"Failed to parse arguments {args}")
                    return
            else:
                fn=op.strip()
                args=[]
            fn = self.op_mapping[fn]
            fn(*args)
    
    #
    # Events
    #

    def eventFilter(self, object, event):
        # print(event)
        # Must reset key combo when focus is gained since key combo 
        #   can store old values is focus is changed while holding a key
        if event.type() == 31:
            self.mouseWheelEvent(event)
        if event.type() == QEvent.WindowActivate:
            self.key_combo = []
        return False

    def getAxisFromMouse(self,event):
        posx = event.x()/self.width()
        posy = 1-event.y()/self.height()
        # Determine Which Axes was clicked
        selectedAxes = None
        for k,a in reversed(list(self.axes.items())):
            apos = a.get_position()
            if(posx>apos.x0 and posx<apos.x1):
                if(posy>apos.y0 and posy<apos.y1):
                    selectedAxes = k
                    # print("Selected Axes =",k)
                    break
        return selectedAxes
        
    def mouseWheelEvent(self,event):
        pass
        # print("Phase:",event.phase())
        # print("Inverted:",event.inverted())
        # print("pos:",event.pos())
        # print("pixel:",event.pixelDelta())
        # print("angle:",event.angleDelta())
        # print("x:",event.x())
        # print("y:",event.y())
        
    def mousePressEvent(self,event):
        if (event.button() == Qt.MiddleButton and self.key_combo.count(K.ctl)) or \
            (event.button() == Qt.MiddleButton and self.key_combo.count(K.shift)):
            self.rescale_all(self.getAxisFromMouse(event))  
        elif event.button() == Qt.MiddleButton:
            self.rescale_y(self.getAxisFromMouse(event))
        super().mousePressEvent(event)
 
    def keyPressEvent(self, event):
        # To connect functions look at plot_utils
        super().keyPressEvent(event)
        if(event.isAutoRepeat()): return
        if self.key_combo.count(event.key()): return
        self.key_combo.append(str(event.key()))
        self.key_combo.sort()
        fn = self.keyPressLookup.get(''.join(self.key_combo))
        if not fn is None:
            try: fn(self,None)
            except Exception as e: print(e)
    
    def keyReleaseEvent(self,event):
        # Removes key from key list
        super().keyReleaseEvent(event)
        if(event.isAutoRepeat()): return
        if self.key_combo.count(str(event.key())) == 0: return
        self.key_combo.remove(str(event.key()))
        
    def showMenu(self,event):
        if(event is None): return
        # Get mouse position as a ratio
        selectedAxes = self.getAxisFromMouse(event)
        # If no axes is selected, return
        if selectedAxes is None:
            print("Error: Axes not found!")
            return            
        # Create a Menu
        menu = QMenu()
        # General
        scale_menu = QMenu("Scaling")
        rescale_all_action = QAction("All", self)
        scale_menu.addAction(rescale_all_action)
        rescale_action = QAction("Fit Y", self)
        scale_menu.addAction(rescale_action)
        getx_action = QAction("Copy X Scale", self)
        scale_menu.addAction(getx_action)
        setx_action = QAction("Paste X Scale", self)
        scale_menu.addAction(setx_action)
        menu.addMenu(scale_menu)
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
            pointerList.append(QAction("Annotate"))
            traceActions[pointerList[-1]] = (self.annotateTrace,(key,))
            """
            traceActions{
                <pointer for action> : tuple<std::function,tuple<str,*void>>
            }
            """
            pointer.addAction(pointerList[-1])
            # Split
            pointerList.append(QAction("Split"))
            traceActions[pointerList[-1]] = (self.splitAxes,(key,))
            pointer.addAction(pointerList[-1])
            # Push Up
            pointerList.append(QAction("Push Up"))
            traceActions[pointerList[-1]] = (self.pushUpTrace,(key,))
            pointer.addAction(pointerList[-1])
            # Push Down
            pointerList.append(QAction("Push Down"))
            traceActions[pointerList[-1]] = (self.pushDownTrace,(key,))
            pointer.addAction(pointerList[-1])
            # Delete
            pointerList.append(QAction("Delete"))
            traceActions[pointerList[-1]] = (self.removePlot,(key,))
            pointer.addAction(pointerList[-1])

        # Get Choosen Action
        action = menu.exec_(self.mapToGlobal(event))
        # Process Axes Wide Actions
        if action == rescale_action:
            self.rescale_y(selectedAxes)
        elif action == rescale_all_action:
            self.rescale_all(selectedAxes)
        elif action == getx_action:
            utils.KeyActions_1d.storeXValues(self,selectedAxes)
        elif action == setx_action:
            utils.KeyActions_1d.setXValues(self,selectedAxes)
        # Process Trace Specific Actions
        elif not traceActions.get(action) is None:
            fn,args = traceActions[action]
            # fn(*args)
            try: fn(*args)
            except Exception as e: print(e)
            try: self.plot(rescale=False)
            except Exception as e: Warning(f"Failed to Plot after contect menu option with the following \n\t{e}")
    
    #
    # Operations
    #

    def annotateTrace(self,traceID):
        trace = self.traces[traceID]
        trace.annotate = 1^trace.annotate
        ax = self.axes[trace.axesID]
        if trace.annotate:
            trace.cid = ax.callbacks.connect("xlim_changed",self.plotcallback)
        else:
            try:
                ax.callbacks.disconnect(trace.cid)
            except Exception as e:
                print(e)
        self.plot(rescale=False)
        pass

    def annotateAll(self,*args):
        for trace in self.traces.values():
            # print(trace)
            # trace = self.traces[traceID]
            trace.annotate = 1^trace.annotate
            ax = self.axes[trace.axesID]
            if trace.annotate:
                trace.cid = ax.callbacks.connect("xlim_changed",self.plotcallback)
            else:
                try:
                    ax.callbacks.disconnect(trace.cid)
                except Exception as e:
                    print(e)
        self.plot(rescale=False)
        pass

    def plotcallback(self,*args):
        # print("Plotting")
        self.plot(rescale=False)

    def getXLim(self,axisID = None):
        # print("getxlim")
        if not axisID is None: return self.axes[axisID].get_xlim()
        else:
            xlims = []
            for axes in self.axes.values():
                xlims.append(axes.get_xlim())
            return xlims

    def setXLim(self,lims,axesID = None):
        print(lims,axesID)
        if not axesID is None: self.axes[axesID].set_xbound(*lims)#self.axes[axesID].set_xlim(*lims)
        else:
            if not type(lims) is list:
                lims = [lims]
            if len(lims) == 1:
                for axes in self.axes.values(): axes.set_xbound(*lims[0])
            else:
                for lim,axes in zip(lims,self.axes.values()): axes.set_xbound(*lim)
        self.plot(rescale=False)    
        
    def getYLim(self,axisID = None):
        if not axisID is None: return self.axes[axisID].get_ylim()
        else:
            ylims = []
            for axes in self.axes.values():
                ylims.append(axes.get_ylim())
            return ylims

    def rescale_y(self,axesID=None):
        if(axesID is None):
            for i,axes in self.axes.items():
                xlim = axes.get_xlim()
                maxa = -1e255; mina = 1e255
                for trace in self.traces.values():
                    if(trace.x.size <= 0): continue
                    if trace.axesID == i:
                        y_sel = trace.y[(trace.x>xlim[0]) & (trace.x<xlim[1])]
                        if y_sel.size <= 0: y_sel = np.interp(xlim,trace.x,trace.y)
                        if mina>y_sel.min(): mina = y_sel.min()
                        if maxa<y_sel.max(): maxa = y_sel.max()
                tol = (maxa-mina)*0.05
                axes.set_ybound(mina-tol,maxa+tol)
        else:
            axes = self.axes[axesID]
            xlim = axes.get_xlim()
            maxa = -1e255; mina = 1e255
            for trace in self.traces.values():
                if(trace.x.size <= 0): continue
                if trace.axesID == axesID:
                    y_sel = trace.y[(trace.x>xlim[0]) & (trace.x<xlim[1])]
                    if y_sel.size <= 0: y_sel = np.interp(xlim,trace.x,trace.y)
                    if mina>y_sel.min(): mina = y_sel.min()
                    if maxa<y_sel.max(): maxa = y_sel.max()
            tol = (maxa-mina)*0.05
            axes.set_ybound(mina-tol,maxa+tol)

        self.plot(rescale = False)

    def rescale_all(self,axisID=None):
        if axisID is None:
            return
        axes = self.axes[axisID]
        minax,maxax = 1e255,-1e255
        minay,maxay = 1e255,-1e255
        for trace in self.traces.values():
            if trace.axesID == axisID:
                if trace.x.min()<minax: minax = trace.x.min()
                if trace.x.max()>maxax: maxax = trace.x.max()
                if trace.y.min()<minay: minay = trace.y.min()
                if trace.y.max()>maxay: maxay = trace.y.max()
        tol = (maxax-minax)*0.05
        axes.set_xbound(minax-tol,maxax+tol)
        tol = (maxay-minay)*0.05
        axes.set_ybound(minay-tol,maxay+tol)
        self.plot(rescale=False)

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

    def toggleGrid(self,axesID=None):
        self.isGridOn = not self.isGridOn
        if axesID is None:
            for axes in self.axes.values():
                axes.grid()
        else:
            self.axes[axesID].grid()
        self.plot()

    def clearAllPlots(self):
        for axes in self.axes.values():
            axes.cla()
        self.traces.clear()
        self.N_defaults = 0

    def splitAxes(self,traceID):
        print("Disabling Split Axes Until A Clean Method is Made")
        return
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

    def pushDownTrace(self,traceID):
        if type(traceID) is int:
            if self.traces.get(traceID) is None: 
                traceID = list(self.traces.keys())[traceID]
        try:
            trace = self.traces[traceID]
        except:
            raise Exception("Cannot Find trace With Trace ID: "+str(traceID))
        # trace.trace.remove()
        axesID = trace.axesID+1
        
        nAxes = len(self.axes)+1
        nAxes = min([axesID+1,nAxes])
        trace.axesID = axesID
        

        listOfCords = []
        for i in range(nAxes):
            listOfCords.append((nAxes,1,i+1))
        
        # print(listOfCords)

        for axes in self.axes.values():
            try: axes.remove()
            except: ... 
        self.axes = {}
        for i,(x,y,n) in enumerate(listOfCords):
            self.axes[i] = self.fig.add_subplot(x,y,n)
            self.axes[i].set_facecolor(self.Facecolor)
            if(self.isGridOn): self.axes[i].grid()
            self.axesLegends[i] = 0

        # d = {trace.name:trace}
        traces = self.traces
        self.traces = {}
        self.setPlotFromTraceDict(traces)
        self.plot()
        self.axesChanged.emit()
    
    def pushUpTrace(self,traceID):
        if type(traceID) is int:
            if self.traces.get(traceID) is None: 
                traceID = list(self.traces.keys())[traceID]
        try:
            trace = self.traces[traceID]
        except:
            raise Exception("Cannot Find trace With Trace ID: "+str(traceID))
        
        axesID = trace.axesID-1
        if axesID < 0: return
        trace.axesID = axesID

        nAxes = len(self.axes)
        mAxes = 0
        # Check for the maximum Axes Value used.
        for t in self.traces.values():
            mAxes = max((t.axesID+1,mAxes))
        # Set the Minimum Axes needed by the plot tool
        
        nAxes = min([mAxes,nAxes])
        
        

        listOfCords = []
        for i in range(nAxes):
            listOfCords.append((nAxes,1,i+1))
        
        # print(listOfCords)

        for axes in self.axes.values():
            try: axes.remove()
            except: ...
        self.axes = {}
        for i,(x,y,n) in enumerate(listOfCords):
            self.axes[i] = self.fig.add_subplot(x,y,n)
            self.axes[i].set_facecolor(self.Facecolor)
            if(self.isGridOn): self.axes[i].grid()
            self.axesLegends[i] = 0

        traces = self.traces
        self.traces = {}
        self.setPlotFromTraceDict(traces)
        self.plot(rescale = False)
        self.axesChanged.emit()
        
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
        if type(traceID) is int:
            if self.traces.get(traceID) is None: 
                traceID = list(self.traces.keys())[traceID]
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
        self.axes[trace.axesID].legend(loc=self.legendLoc,**self.legendKwargs)
        del trace
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
            newTrace = Trace(label)
            self.traces[traceID] = newTrace
            newTrace.x = xy
            newTrace.y = y
            newTrace._name = label
            newTrace.axesID = subPlotID
            if newTrace._isDate:
                newTrace.trace,*_ = self.axes[subPlotID].plot_date(newTrace.x,newTrace.y,fmt='-',*args,**kwargs)
            else:
                newTrace.trace,*_ = self.axes[subPlotID].plot(newTrace.x,newTrace.y,*args,**kwargs)
            newTrace.trace.set_label(newTrace._name)
            if legend: self.axes[subPlotID].legend(loc=self.legendLoc,**self.legendKwargs) # <--- This probably needs to be moved to another location
            self.axesLegends[subPlotID] = legend
            newTrace.update()
            self.tracesChanged.emit()
        else:
            trace = self.traces[traceID]
            trace.x = xy
            trace.y = y
            trace.update()
        # print(self.traces)
    
    def setPlotFromTraceDict(self,traces):
        traces = copy.copy(traces)
        for key,val in traces.items():
            try:
                self.setPlot(val.x,val.y,label=val.name,traceID=key,subPlotID=val.axesID)
            except Exception as e:
                print(e)
    
    def getAllTraces(self):
        return self.traces

    def getTrace(self,traceID):
        return self.traces[traceID]

    def getAxes(self,axesID):
        try:
            axes = self.axes[axesID]
            return axes
        except Exception as e:
            print("Failed getAxes call with the following:")
            print("\t",e)

    def save(self,filename,width=None,height=None):
        if((not width is None) and (not height is None)):
            self.fig.set_size_inches(width/100,height/100)
        self.draw()
        self.fig.savefig(filename)

    def redraw(self):
        self.repaint()
        pass
        
    def plot(self,rescale = True):
        self.N_defaults = 0
        # print("Plotting")
        if(rescale):
            for axes in self.axes.values():
                axes.relim()
                axes.autoscale_view()
            for axes in self.twin_axes.values():
                axes.relim()
                axes.autoscale_view()
        redraw = {}
        for trace in self.traces.values():
            if trace.annotate:
                trace.updateAnnotations(self.axes[trace.axesID],self.getXLim(trace.axesID))
            if trace.annotate == False and not trace._annotations is None:
                trace.removeAnnotations(self.axes[trace.axesID])
            if trace.update(): redraw[trace.axesID] = True
        for axesID in redraw.keys():
            print("Calling legend",axesID)
            self.axes[axesID].legend(loc=self.legendLoc,**self.legendKwargs)
        try:
            self.draw()
        except Exception as e:
            print("Failed To Plot with following: ")
            print(e)
