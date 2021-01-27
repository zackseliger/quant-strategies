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
	r = requests.get('https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&market=USD&symbol={}&apikey={}'.format(ticker, AV_KEY))
	data = json.loads(r.text)['Time Series (Digital Currency Daily)']

	# open the file we're going to write to
	f = open("temp/"+ticker+".csv", "w")
	f.write("Date,Open,High,Low,Close,Adj Close,Volume,Market Cap\n")
	curr_date = datetime.strptime(start_date, "%Y-%m-%d")

	# write the data
	while curr_date.strftime("%Y-%m-%d") != end_date:
		try:
			info = data[curr_date.strftime("%Y-%m-%d")]
			line = "{},{},{},{},{},{},{},{}\n".format(curr_date.strftime("%Y-%m-%d"), info['1a. open (USD)'], info['2a. high (USD)'], info['3a. low (USD)'], info['4a. close (USD)'], info['4a. close (USD)'], info['5. volume'], info['6. market cap (USD)'])
			f.write(line)
		except:
			pass

		curr_date += timedelta(days=1)

	f.close()

stocks = [
	"DOGE"
]
for stock in stocks:
	print("writing "+stock)
	download_stock(stock, "2019-09-01", "2020-12-23")
	print("wrote "+stock)
	sleep(15)
