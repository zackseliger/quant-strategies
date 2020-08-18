from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle

strategies = [TestStrategy, TestStrategy2, BuyAndHoldAll]

# pre-pick stocks
dir = 'stocks/2016'
stocks = []
files = listdir(dir)
shuffle(files)
for filename in files:
    if random() < 0.05:
        stocks.append(filename)
# stocks = ['DIA.csv', 'DIA.csv', 'DIA.csv', 'DIA.csv', 'DIA.csv', 'SPY.csv', 'SPY.csv', 'SPY.csv', 'SPY.csv', 'SPY.csv']

print("sharpe ratio, avg_annual_returns / maxdrawdown")
for strat in strategies:
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
    sharpe_ratio = results.analyzers[2].get_analysis()['sharperatio']
    if sharpe_ratio is None: sharpe_ratio = 0
    returns = results.analyzers[0].rets
    avg_returns = sum(returns)/len(returns)
    maxdrawdown = results.analyzers[1].get_analysis()['max'].drawdown/100
    if maxdrawdown == 0: maxdrawdown = 0.0001
    print(
        str(round(sharpe_ratio,2)) + ", " +
        str(round(avg_returns,2)) + " / " +
        str(round(maxdrawdown,2)) + " = " +
        str(round(avg_returns/maxdrawdown,2))
    )

    # cerebro.plot()