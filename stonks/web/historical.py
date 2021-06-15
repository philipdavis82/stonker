
import numpy as np

class Historical:
    def __init__(self,time,open,high,low,close,volume):
        self._time   = time
        self._open   = open
        self._high   = high
        self._low    = low
        self._close  = close
        self._volume = volume
    
    @staticmethod
    def fromDataFrame(df):
        time    = np.array( df.index   )
        open    = np.array( df["Open"]   )
        high    = np.array( df["High"]   )
        low     = np.array( df["Low"]    )
        close   = np.array( df["Close"]  )
        volume  = np.array( df["Volume"] )

        return Historical(time,open,high,low,close,volume)
