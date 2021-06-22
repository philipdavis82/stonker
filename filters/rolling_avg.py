# Import base filter interface
from .__base_filter__ import FilterBase,FilterReturn

import numpy as np
import datetime
Today = datetime.datetime.today

import stonks

new_filter = FilterBase()

new_filter.setParameter("avg-swath-1" , datetime.timedelta(days=3)  )
new_filter.setParameter("avg-swath-2" , datetime.timedelta(days=5)  )
new_filter.setParameter("avg-swath-3" , datetime.timedelta(days=7)  )
new_filter.setParameter("date-range"  , datetime.timedelta(days=14) )

@new_filter.setFilter
def filterfn(target,date,params,*args,**kwargs):
    result = FilterReturn()

    start = date - params['date-range'] 

    hist = stonks.historical(target,start,date)

    kernal = np.ones(3)/3
    orig_avg = ( hist._high + hist._low ) / 2
    avg = np.convolve(orig_avg,kernal,mode='valid')
    avg_time = hist._time[hist._high.size - avg.size :]
    orig_avg = orig_avg[hist._high.size - avg.size :]

    result.plot(avg_time,orig_avg,title='Rolling Average', label = 'Origianl')
    result.plot(avg_time,avg,title='Rolling Average', label = '3 day')

    return result ## Must return result

FILTER = new_filter
# class rolling_average(__FILTER_BASE):
    # def __init__(self,*args,**kwargs):
        # super().__init__(*args,**kwargs)
        
        # 3rd order rolling average function
        # self.setParameter("avg-swath-1" , datetime.timedelta(days=3)  )
        # self.setParameter("avg-swath-2" , datetime.timedelta(days=5)  )
        # self.setParameter("avg-swath-3" , datetime.timedelta(days=7)  ) 
        # The date range to run the average over
        # self.setParameter("date-range", datetime.timedelta(days=14)   ) 

    # def filter(self,target,date=Today(),*args,**kwargs):
        
        # deltaTime = self.getParemeter("date-range")
        # hist = stonks.historical(target,date,date-deltaTime)
        
        
        # kernal = np.ones(3)/3
        # avg = ( hist._high + hist._low ) / 2
        # avg = np.convolve(avg,kernal,mode='valid')
        # avg_time = hist._time[hist._high.size - avg.size :]
        
        