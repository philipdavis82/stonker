
import os,sys
from urllib import request
import json

HOMEPATH = os.path.split(os.path.abspath(__file__))[0]
TICKERPATH = "https://raw.githubusercontent.com/plotly/dash-stock-tickers-demo-app/master/tickers.csv"

def getTickerJson(filename):
    with open(os.path.join(HOMEPATH,filename),'r') as file:
        tjson = json.loads(file.read())
    return tjson

def saveTickerJson(filename,tjson):
    with open(os.path.join(HOMEPATH,filename),'w') as file:
        json.dump(tjson,file,indent=2)

def updateTickers(filename = "tickers.json"):
    with request.urlopen(TICKERPATH) as response:
        csv = str(response.read().decode('utf-8'))
    tjson = getTickerJson(filename)
    # print(csv)
    csv = csv.replace("\"","")
    csv = csv.split("\n")
    csv_dict = {}
    for line in csv:
        if line.strip() == "": continue
        line = line.split(",")
        csv_dict[line[0]] = {"ticker":line[1]}
    tjson["stocks"] = csv_dict
    saveTickerJson(filename,tjson)

def getStockTickers(filename = "tickers.json"):
    with open(os.path.join(HOMEPATH,filename),'r') as file:
        tjson = json.loads(file.read())
    return tjson["stocks"]

def getCryptoTickers(filename = "tickers.json"):
    with open(os.path.join(HOMEPATH,filename),'r') as file:
        tjson = json.loads(file.read())
    return tjson["crypto"]

def getStockTickerInfo(ticker):
    tjson = getTickerJson("tickers.json")
    info = tjson['stocks'][ticker]
    return info
    
def setStockTickerInfo(ticker,key,val):
    tjson = getTickerJson("tickers.json")
    tjson['stocks'][ticker][key] = val
    saveTickerJson("tickers.json",tjson)
    
if __name__ == "__main__":
    updateTickers()