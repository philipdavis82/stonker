#PyQt5 Lib
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import time
import numpy as np
from . import trace


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
            trace = trace.trace(trace_name)
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
