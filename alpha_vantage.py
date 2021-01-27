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
	r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol={}&apikey={}'.format(ticker, AV_KEY))
	data = json.loads(r.text)['Time Series (Daily)']

	# open the file we're going to write to
	f = open("temp/"+ticker+".csv", "w")
	f.write("Date,Open,High,Low,Close,Adj Close,Volume\n")
	curr_date = datetime.strptime(start_date, "%Y-%m-%d")

	# write the data
	while curr_date.strftime("%Y-%m-%d") != end_date:
		try:
			info = data[curr_date.strftime("%Y-%m-%d")]
			line = "{},{},{},{},{},{},{}\n".format(curr_date.strftime("%Y-%m-%d"), info['1. open'], info['2. high'], info['3. low'], info['4. close'], info['5. adjusted close'], info['6. volume'])
			f.write(line)
		except:
			pass

		curr_date += timedelta(days=1)

	f.close()

stocks = [
	"CTAS", "DISH", "FWLT", "HOLX", "JBHT", "LOGI", "PDCO", "CMCSA", "ILMN",
	"AKAM", "CSCO", "TXN", "COST", "AMGN", "AZN", "SBUX", "AMD", "AMAT",
	"INTU", "ISRG", "DLTR", "QGEN", "GILD", "LRCX", "NTES", "FISV", "ATVI",
	"CSX", "ADP", "FFIV", "EQIX", "URBN", "ADI", "ILMN", "REGN", "VOD",
	"MNST", "KLAC", "CSTH", "EA"
]
for stock in stocks:
	print("writing "+stock)
	download_stock(stock, "2002-01-01", "2020-12-23")
	print("wrote "+stock)
	sleep(15)
