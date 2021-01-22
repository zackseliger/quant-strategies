from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle

if __name__ == "__main__":
	# setup strategy
	strategy = Momentum
	cerebro = bt.Cerebro(optreturn=False, stdstats=False)
	cerebro.optstrategy(strategy, test=range(5,35,5))

	# get stocks
	dir = 'stocks/2008'
	dirs = listdir(dir)
	shuffle(dirs)
	for filename in dirs:
		if random() < 0.5:
			cerebro.adddata(btfeeds.GenericCSVData(
					dataname=dir+'/'+filename,
					dtformat=('%Y-%m-%d'),

					datetime=0,
					open=1,
					high=2,
					low=3,
					close=4,
					volume=6
			))

	# run strategies
	start_cash = 10000
	cerebro.broker.setcash(start_cash)
	cerebro.broker.setcommission(commission=0.0) 
	opt_runs = cerebro.run()
	# get results (this doesn't work bc of a bug in backtester)
	final_results_list = []
	for run in opt_runs:
		for strategy in run:
			value = strategy.broker.get_value()
			pnl = round(value - start_cash, 2)
			period = strategy.params.test
			final_results_list.append([period,pnl])
	# Sort Results List
	by_period = sorted(final_results_list, key=lambda x: x[0])
	by_pnl = sorted(final_results_list, key=lambda x: x[1], reverse=True)
	# print results in order
	print("Results ordered by period")
	for period_data in by_period:
		print(str(period_data[0]) + ": " + str(period_data[1]))
	print("Results ordered by pnl")
	for pnl_data in by_pnl:
		print(str(pnl_data[0]) + ": " + str(pnl_data[1]))