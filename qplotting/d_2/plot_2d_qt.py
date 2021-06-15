
#Std Lib
import copy
import time

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

#utils
# from .plot_utils import *

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

class pixmap_wrapper(QWidget):
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
        super(pixmap_wrapper,self).__init__(parent)
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
