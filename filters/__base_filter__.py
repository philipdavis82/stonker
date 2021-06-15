"""
ideas for a filter?

what is a filter in this context?
    - Computes some information for a specific time series data 
        - the x axis in some time domain information
        - the y axis is some amplitude information
    - The filter then can take supportave data that could partain to the main data
        - this is any type of data
            - Time series 
            - scalar values
            - ....
        - this can be delivered in a key value mapping.
    - Since this the common source of information that the filter has is stock time series
      then the filter should be able to request that time series information.
    - The filter should also be able to be asynchronous... 
        - This means that it doesn't have to be but if it is it isn't detrimental. 
    - The filter must be able to be iterated over.
        - This iterator will return the time and values 
          produced by the filters inputs
    - The filters time values should be in a common time format
        - TODO: Determine this time format

Filter Return:
    - The main filter call must return a dictionary
      the dictionary is able to hold a magnitude of
      of output types. These types are as follows

      - "plot"
        - tell the main gui to display verious plots
          this is is a list of dictionaires that can
          contain a number of keys that determine the
          type of each plot.
          x,a       is a line plot
          x,y,a,    is a color mesh
          x,y,z,a,  is a 3d plot 
        - possible keys
            - "x" : x coordinate
            - "y" : y coordinate
            - "z" : z coordinate
            - "a" : amplitude at point (x,y,z)
      
      - "buy"
        - A single value that describes a buy metric 
      - "hold"
        - A single value that describes a hold metric
      - "sell"
        - A single value that describes a sell metric
    - *Note* buy+hold+sell == 1 
      
      - "confidance"
        - A single value that describes the confidance that 
          the filter has on the above buy,hold,sell metrics.

    - These results are this way so that it is able to be 
      packaged up into a json format for possible future 
      web or app implementations 

Example:
{
    "plot":
    {
        [
            {
                "title" : "filter results"
                "input" : 
                {
                    "x" : [1,2,3,4]
                    "a" : [5,5,4,3]
                }
                "ouput" : 
                {
                    "x" : [1,2,3,4]
                    "a" : [0,0,-1,-1]
                }
            },
            {
                "title" : "metrics"
                "buy" : 
                {
                    "x" : [1,2,3,4]
                    "a" : [0.4,0.4,0.1,0.1]
                }
                "sell" : 
                {
                    "x" : [1,2,3,4]
                    "a" : [0.6,0.6,0.9,0.9]
                }
            }
        ]
    },
    "buy"  : 0.1 ,
    "hold" : 0.0 ,
    "sell" : 0.9 ,

    "confidance" : 0.5 ,
}  

This is just a possiblity and could more could possibly be 
added to the arguments returned.
"""

# Base Filter Class
# All filters should derive from this class.

class __FILTER_BASE():
    def __init__(self,target_name,*args,**kwargs):
        self.__iter = None
        self.__target_name = target_name
        pass

    def __iter__(self):
        if self.__iter is None: raise Exception("Iterator Not Implemented")
        return self.__iter # If self._iter is not set then 

    def setItterable(self,itterable):
        self.__iter = itterable

    def filter(self,start_date,end_date):
        raise Exception("Filter Method Not Implemented")

__FILTER_TEMPLATE = lambda **kwargs: \
f"""
# Import base filter interface
from .__base_filter__ import __FILTER_BASE

import datetime.datetime as datetime

class {kwargs["filter_name"]}(__FILTER_BASE):
    def __init__(self,target_name,*args,**kwargs):
        super().__init__(target_name,*args,**kwargs):

        #setup filter 

        # If this is or has an itterable then set it
        self.setItterable(self) # Assuimg that the class it self is an itterable 

    def filter(self,start_date,end_date):
        # This is where the meat of the filter method goes. 
        # This can get called in creation or during the itteration
        # This should return a tuple of x and y values.
        x = datetime.today()    # This can also be an array
        y = 1                   # This can also be an array
        return (x,y)

"""

if __name__ == "__main__":
    raise Exception("No testing implemented")
