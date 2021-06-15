from pandas_datareader import data as pdr
import yfinance as yf

yf.pdr_override()

import pandas as pd 
import datetime

try:    from . import historical as hist
except:        import historical as hist

def date_to_string(date):
    datetype = type(date)
    if   datetype == datetime.datetime:
        date = "-".join([str(date.year),str(date.month),str(date.day)])
    elif datetype == str: pass
    else: raise Exception("Unknown Type")
    
    return date

def historical(ticker,start,end):
    assert type(ticker) == str
    start = date_to_string(start)
    end   = date_to_string(end)
    data = pdr.get_data_yahoo(ticker,start=start,end=end)
    if data.empty: return None
    return hist.Historical.fromDataFrame(data)

if __name__ == "__main__":
    # tickers = gt.getStockTickers()

    # ticker_list = gt.get_tickers()
    # for t in ticker_list:
        # print(t)
    # ticker_list = ["DJIA", "DOW", "LB", "EXPE", "PXD", "MCHP", "CRM", "JEC" , "NRG", "HFC", "NOW"]
    # today = date.today()
    ticker = "dow"
    start_date = "2017-01-01"
    end_date = "2019-11-30"
    d = historical(ticker,start_date,end_date)
    
    # files = []
    # def getData(ticker):
        # data = pdr.get_data_yahoo(ticker,start=start_date,end=today)
        # dataname = ticker+"_"+str(today)
        # files.append(dataname)
    #     print(data)
    # for ticker in ticker_list:
    #     getData(ticker)