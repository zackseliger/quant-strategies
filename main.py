from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle

strategies = [VolSZOStrat, PivotPointsStrat, BuyAndHoldAll, BuyAndHoldSPY]

print("sharpe ratio, avg_annual_returns / maxdrawdown")
for strat in strategies:
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strat)

    cerebro.addanalyzer(bt.analyzers.AnnualReturn)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, annualize=True, riskfreerate=0.01)

    # add data
    dir = 'stocks/2016'
    dirs = listdir(dir)
    shuffle(dirs)
    for filename in dirs:
        if random() < 1:
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