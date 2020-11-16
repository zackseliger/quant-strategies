from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle

strategies = [InverseOverMALongShort, VolSigLongShort, SMALongShort, EMALongShort, BuyAndHoldAll]

# pre-pick stocks
dir = 'stocks/2016'
stocks = []
files = listdir(dir)
shuffle(files)
for filename in files:
    if random() < 0.02:
        stocks.append(filename)

print("stocks: "+str(stocks))

print("sharpe ratio, avg_annual_returns / maxdrawdown")
for strat in strategies:
	cagrs = []
	maxdrawdowns = []
	romads = []
	sharpes = []

	for filename in stocks:
			cerebro = bt.Cerebro()
			cerebro.addstrategy(strat)

			cerebro.addanalyzer(bt.analyzers.AnnualReturn)
			cerebro.addanalyzer(bt.analyzers.DrawDown)
			cerebro.addanalyzer(bt.analyzers.SharpeRatio, annualize=True, riskfreerate=0.01)

			# add data
			for filename in stocks:
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

			# run stretegy and get stats
			results = cerebro.run()[0]
			sharpes.append( results.analyzers[2].get_analysis()['sharperatio'] )
			if sharpes[-1] is None: sharpes[-1] = 0
			returns = results.analyzers[0].rets
			cagrs.append( sum(returns)/len(returns) )
			maxdrawdowns.append ( results.analyzers[1].get_analysis()['max'].drawdown/100 )
			if maxdrawdowns[-1] == 0: maxdrawdowns[-1] = 0.0001
			romads.append ( cagrs[-1] / maxdrawdowns[-1] )

	print(
	    str(round(sum(sharpes)/len(sharpes),2)) + ", " +
	    str(round(sum(cagrs)/len(cagrs),2)) + " / " +
	    str(round(sum(maxdrawdowns)/len(maxdrawdowns),2)) + " = " +
	    str(round(sum(cagrs)/len(cagrs) / sum(maxdrawdowns)/len(maxdrawdowns),2))
	)