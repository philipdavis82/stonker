# This is ment to be an interface script that allows users to grab data
# without having worry about where it comes from. 
#
# The idea is that when a user asks for historical stock information
# this will look at the possible sources and then choose from the best
# source. The order is as follows...
#   1. local database       (Not Implemented)
#   2. Paid API             (Not Implemented)
#   3. Yahoo Web Scrapper   
#   4. Google Web Scrapper  (Not Implemented)
# 
# Quaries should also be able to be made though this interface 
#
#...Note* If this file becomes too large then split into a directory of files.

from . import database
from . import web


def historical(ticker, start, end):
    pass