import requests
import json
from datetime import datetime, timedelta
from time import sleep

from dotenv import load_dotenv
import os
load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_KEY")
AV_KEY = os.getenv("AV_KEY")

def download_stock(ticker, start_date, end_date):
	# get stock data from alphavantage
	interval = "30min"
	r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&interval={}&outputsize=full&symbol={}&apikey={}'.format(interval, ticker, AV_KEY))
	data = json.loads(r.text)['Time Series ({})'.format(interval)]

	# open the file we're going to write to
	f = open("temp/"+ticker+".csv", "w")
	f.write("Date,Open,High,Low,Close,Adj Close,Volume\n")
	curr_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")

	# write the data
	while curr_date.strftime("%Y-%m-%d %H:%M:%S") != end_date:
		try:
			info = data[curr_date.strftime("%Y-%m-%d %H:%M:%S")]
			line = "{},{},{},{},{},{},{}\n".format(curr_date.strftime("%Y-%m-%d %H:%M:%S"), info['1. open'], info['2. high'], info['3. low'], info['4. close'], info['4. close'], info['5. volume'])
			f.write(line)
		except:
			pass

		curr_date += timedelta(minutes=30) # NEED TO ADJUST ACCORDING TO TIMEFRAME

	f.close()

stocks = [
	"SNAP", "PINS", "PLTR", "SQ", "FTCH", "CRM", "NVTA", "CRSP", "TDOC",
	"CRWD", "DOCU", "SE", "CLSK", "OKTA", "X", "WFC", "KTB", "NET", "ENPH",
	"ESTC", "MDB", "BLK", "CAT"
]
for stock in stocks:
	print("writing "+stock)
	download_stock(stock, "2020-12-22 00:00:00", "2021-02-01 20:00:00")
	print("wrote "+stock)
	sleep(15)
