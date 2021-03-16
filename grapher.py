import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle

if __name__ == "__main__":
	# setup strategy
	cerebro = bt.Cerebro()
	# cerebro.addstrategy(TestStrategy2, recordstats=True)
	cerebro.addindicator(VPN)

	# get stocks
	dirs = ['stocks/growth2018']
	files = []
	for dir in dirs:
		filenames = listdir(dir)
		for i in range(len(filenames)):
			filenames[i] = dir+"/"+filenames[i]
		files += filenames
	shuffle(files)

	# add stocks as data
	for filename in files:
		if random() < 1:
			cerebro.adddata(btfeeds.GenericCSVData(
				dataname=filename,
				dtformat=('%Y-%m-%d'),

				datetime=0,
				open=1,
				high=2,
				low=3,
				close=4,
				volume=6
			))

	# run strategies
	start_cash = 10000000
	cerebro.broker.setcash(start_cash)
	results = cerebro.run()
	# put stuff in csv
	results[0].statsfile.to_csv('test_data.csv')