import requests
import json

from dotenv import load_dotenv
import os
load_dotenv()
POLYGON_KEY = os.getenv("POLYGON_KEY")

# r = requests.get("https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2019-01-01/2020-01-01?adjusted=true&apiKey="+POLYGON_KEY)
r = requests.get("https://api.polygon.io/v2/reference/financials/SPLK?type=QA&limit=20&apiKey="+POLYGON_KEY)
data = json.loads(r.text)

keys = data['results'][0].keys()
f = open("test.csv", "w")

# setting up legend
for key in keys:
	f.write(key+",")
f.write('\n')

# the actual data
for report in data['results']:
	for key in keys:
		f.write(str(report[key])+",")
	f.write('\n')

f.close()
