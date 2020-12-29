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

# stocks = ["INMD","SHOP","CASH",'ARWR','PLMR','ENPH','KL','OLED','PODD','SAFE','PAYS','IIPR','SEDG','RNG','ACIA','ARCE','TDG','STNE','PCTY','CG','INS','RGEN','PAYC','COUP','NOW','RH',
# 	'CZZ','DXCM','TTD','SNBR','GSHD','SMSI','RNR','UPLD','VST','TMHC','LIN','KNSL','CPRT','GLOB','IBP','TWTR','UEIC','MEDP','CLCT','EW','BURL','ADES','PFSI','PAGS','VEEV','BLD','SNX',
# 	'DOCU','IPHI','CHDN',"PLD"]
# for stock in stocks:
# 	print("writing "+stock)
# 	download_stock(stock, "2019-12-23", "2020-12-23")
# 	print("wrote "+stock)
# 	sleep(15)

download_stock("AAPL", "2019-12-23", "2020-12-23")