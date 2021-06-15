#PyQt5 Lib
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import numpy as np


import datetime

import matplotlib.dates as dates

# Graph Annotation should resize as less points are on the screen
DEFAULT_ANNOTATION_SIZE_MAP = {
    0:  15,
    1:  18,
    2:  15,
    3:  14,
    4:  13,
    5:  13,
    6:  13,
    7:  12,
    8:  12,
    9:  12,
    10: 11,
    11: 11,
    12: 11,
    13: 10,
    14: 10,
    15: 10,
    16: 10,
    17: 9,
    18: 9,
    19: 9,
    20: 9,
}

#Common info Types
class trace_2d():
    def __init__(self,name):
        self._x = np.array([])
        self._y = np.array([])
        self._name = ""
        self._trace = None
        self._axesID = None
        self._isDate = False
        self._hasUpdated = False
        self._infoHasUpdated = False
        self._isSplit = False
        self._annotate = False
        self._annotations = None
        self._annotationTextSize = DEFAULT_ANNOTATION_SIZE_MAP
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
        if type(self._x[0]) is datetime.datetime \
            or \
           type(self._x[0]) is np.datetime64:
            self._isDate = True
            self._x = np.array( [ dates.date2num(X) for X in self._x ] )
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
    @property
    def annotate(self):
        return self._annotate
    @annotate.setter
    def annotate(self,enable):
        try:enable=bool(enable)
        except:raise Exception("Failed to convert annotate enable to a bool")
        self._annotate = enable
        self._hasUpdated = True
    def updateAnnotations(self,ax,lims):
        """
        This takes a matplotlib axes class and addes annotations 
            for this trace. This also requires the x limits of the graph
        """
        # Remove all annotations from the graph when updating. 
        #   TODO: Only remove annotation outside the limits...
        #         This would have to be accounted for in later steps  
        if not self._annotations is None:
            self.removeAnnotations(ax) 
        # After the annotations are removed, make the list empty
        self._annotations = []
        # Modify the limits
        #    Reduce the right most limit by 10% of the total difference
        tol = (lims[1] - lims[0])*0.1
        lims = (lims[0],lims[1]-tol) # This helps with the tight layout trying to resize the plot for everything to fit.
        # Get the amount of points inside the limits
        #   TODO: Get these points only once and use them later
        npoints = self._x[(self._x>lims[0]) & (self._x<lims[1])].size
        if  npoints > 20:
            # If there are more points on the graph than 20 then dont draw any annotations
            self._annotations = None
            # print("Too Many Values to Annotate")
            return
        # Get the text size of the annotations based on how many points are in the limits.
        annotationSize = self._annotationTextSize.get(npoints)
        
        if annotationSize is None: annotationSize = 8
        for x,y in zip(self._x[(self._x>lims[0]) & (self._x<lims[1])],self._y[(self._x>lims[0]) & (self._x<lims[1])]):
            an = ax.annotate(f"y = {y:5f}\nx = {x:5f}",xy=(x,y),backgroundcolor=(1,1,1,0.5),size=annotationSize,family='monospace')
            self._annotations.append(an)
    def removeAnnotations(self,ax):
        if self._annotations is None:
            self._annotate = False
            return
        for i in reversed(range(len(self._annotations))):
            a = self._annotations.pop(i)
            try:
                a.remove()
            except Exception as e:
                print(e)
        self._annotations = None
        return
    def update(self):
        redrawLegend = False
        if self._trace is None: 
            print("Trace info is None.. This shouldn't happen")
            return
        if self._hasUpdated:
            self._trace.set_data(self.x,self.y)
            if self._annotate:
                self._trace.set_marker("o")
            else:
                self._trace.set_marker("")
        if self._infoHasUpdated:
            print("New Name",self._name)
            self._trace.set_label(self._name)
            redrawLegend = True
        self._hasUpdated = False
        self._infoHasUpdated = False
        return redrawLegend

#Common Functions
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
    csv = np.array2string(fullDat,separator=sep,max_line_width=10_000,threshold=100_000_000,formatter={'str_kind': lambda x: x})
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
    
# ~TODO: Add more functions to this
#   - log10 -> Needs to check for values out of range
#   - common filters for the filter function 
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
        "fft"   :   "np.fft.fft",
        "csum"  :   "np.cumsum",
        "max"   :   "np.max",
        "min"   :   "np.min",
        "avg"   :   "np.mean",
        "filter":   "MathInterpreter.conv",
        "matmul":   "np.matmul",
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

# List of key values as strings
class K():
    x       = "88"
    ctl     = "16777249"
    shift   = "16777248"
    a       = "65"

# Key actions as functions, 
#   In Class to reduce functions in namespace
class KeyActions_1d():

    @staticmethod
    def storeXValues(self,axesID = None,*args):
        clip = QGuiApplication.clipboard()
        clip.setText(str(self.getXLim(axesID)))
        print("Copied the new x lims",clip.text())
    
    @staticmethod
    def setXValues(self,axesID = None,*args):
        clip = QGuiApplication.clipboard()
        clip = clip.text()
        if(len(clip)>1000): return
        try:
            xlims = eval(clip)
        except Exception as e:
            print(e)
            return
        try:
            self.setXLim(xlims,axesID)
        except Exception as e:
            print(e)
            return
# Creates the key combo
def KC_make(*args):
    combo = list(args)
    combo.sort()
    
    combo = ''.join(combo)
    return combo

# 1d plot function map for key combos
FN_MAPPING_1D = {
    KC_make(    K.ctl , K.x               ):    KeyActions_1d.storeXValues,
    KC_make(    K.ctl , K.shift , K.x    ):     KeyActions_1d.setXValues,
    }
