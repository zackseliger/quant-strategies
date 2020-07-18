import requests
import json
import csv
import os

filenames = os.listdir('stocks/2008')
for filename in filenames:
	print(filename)
	os.rename('stocks/2008/'+filename, 'stocks/2008/'+filename.replace('2008', ''))

# token = "pk_66b3a03297d144039aecafac6a0faacc"
# token = "sk_8b070aa9f4fd49e5989ff8d17ff529e8"
base_url = "https://cloud.iexapis.com/v1/"

tickers = ["UAL", "BA", "COST", "CCL", "TGT"]

for ticker in tickers:
	print(ticker)
	res = requests.get(base_url+"stock/"+ticker+"/chart/1y?token="+token)

	# write data to a file
	f = open('stocks/'+ticker+'.csv', 'w')
	writer = csv.writer(f)
	writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
	stock_data = json.loads(res.text)
	for day in stock_data:
		writer.writerow([day['date'], day['open'], day['high'], day['low'], day['close'], day['volume']])