import requests
import json
from datetime import datetime

# requests.get(baseRESTURL+"/0/public/OHLC?pair="+pair.replace('/','').lower()+"&interval="+str(interval))
interval = "60" # in minutes

def download_pair(pair):
	# get stock data from kraken
	req_url = 'https://api.kraken.com/0/public/OHLC?pair={}&interval={}'.format(pair.replace("/","").lower(), interval)
	r = requests.get(req_url)
	r = r.json()['result']
	results = r[list(r.keys())[0]]

	# open the file we're going to write to
	f = open("temp/"+pair.replace("/","").lower()+".csv", "w")
	f.write("Date,Open,High,Low,Close,Adj Close,Volume\n")

	for datapoint in results:
		time = float(datapoint[0])
		o = float(datapoint[1])
		h = float(datapoint[2])
		l = float(datapoint[3])
		c = float(datapoint[4])
		v = float(datapoint[6])
		formatted_date = datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S")

		line = "{},{},{},{},{},{},{}\n".format(formatted_date, o, h, l, c, c, v)
		f.write(line)

	f.close()

pairs = [
	"ADA/USD", "BCH/USD", "DASH/USD", "DOT/USD", "ETC/USD", "OMG/USD", "NANO/USD", "WAVES/USD", "QTUM/USD",
	"ETH/USD", "GNO/USD", "KAVA/USD", "KEEP/USD", "LINK/USD", "XBT/USD", "XDG/USD", "XRP/USD", "LTC/USD",
	"XMR/USD"
	]

for pair in pairs:
	download_pair(pair)