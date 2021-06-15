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
from .plot_utils import *

class plot_canvas(FigureCanvasQTAgg):
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
        super(plot_canvas,self).__init__(self.fig) # Initilize the FigureCanvasQTAgg Class as part of this Class
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
        self.theme_d = {"dark":darkTheme,
                        "light":lightTheme}
        self.Facecolor = self.fig.get_facecolor()
        self.Edgecolor = self.fig.get_edgecolor()
        #Right Click Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)
        self.installEventFilter(self)
        self.key_combo = []
        self.keyPressLookup = FN_MAPPING_1D
        self.keyPressLookup[KC_make(K.a,K.shift)] = self.annotateAll
        self.keyPressLookup[KC_make(K.a,K.ctl)]   = self.annotateAll

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
            KeyActions_1d.storeXValues(self,selectedAxes)
        elif action == setx_action:
            KeyActions_1d.setXValues(self,selectedAxes)
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
            newTrace = trace_2d(label)
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

# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************
# ****************************************************************************************

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

class plot_widget(QWidget):
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
            I = Counter()
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
            I = Counter()
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
        super(plot_widget,self).__init__(parent)
        typ = type(canvas)
        if(typ!=plot_canvas): raise Exception("Type "+str(typ)+" is not plot_canvas")
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
        clip.setText(traceDictToCsv(self.canvas.getAllTraces()))
        
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
            self.setPalette(darkPalette())
            self.canvas.setTheme("dark")
        else:
            self.setPalette(lightPalette())
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
        
        
