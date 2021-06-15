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
class Trace():
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
