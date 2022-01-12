from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from os import listdir
from random import random, shuffle
from datetime import datetime

strategies = [AbsStrengthStrategy, RVIStrategy, RVIStrategy2, BuyAllThenSell]

# pre-pick stocks
dir = 'stocks/growth2018'
stocks = []
files = listdir(dir)
shuffle(files)
for filename in files:
    if random() < 0.5:
        stocks.append(filename)

print("sharpe ratio, avg_annual_returns / maxdrawdown")
i = 0
for strat in strategies:
    cerebro = bt.Cerebro()
    cerebro.broker = bt.brokers.BackBroker(slip_perc=0.01)
    # cerebro.broker.setcommission(commission=0.0016)
    cerebro.addstrategy(strat)

    cerebro.addanalyzer(bt.analyzers.AnnualReturn)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, annualize=True, riskfreerate=0.01)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    # add data
    for filename in stocks:
        cerebro.adddata(btfeeds.GenericCSVData(
            dataname=dir+'/'+filename,
            # timeframe=bt.TimeFrame.Minutes, compression=30,
            # dtformat=('%Y-%m-%d %H:%M:%S'),
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

    ta = results.analyzers[3].get_analysis()
    if "won" in ta:
        h1 = ['Total Trades', 'Total Won', 'Total Lost', 'Strike Rate', 'RRR', 'Average P/L', 'Overall P/L']
        closed = ta.total.closed if ta.total.closed > 0 else 1
        lost_pnl = ta.lost.pnl.average if ta.lost.pnl.average != 0 else 1
        r1 = [ta.total.total, ta.won.total, ta.lost.total, round((ta.won.total/closed)*100,2), round(abs(ta.won.pnl.average/lost_pnl), 2), round(ta.pnl.net.average, 2), round(ta.pnl.net.total,2)]
        print(("{:<15}"*(len(h1)+1)).format('',*h1))
        print(("{:<15}"*(len(h1)+1)).format('',*r1))
    else:
        print(("{:<15}"*2).format('',"Trade Analysis Unavailable"))

    # write equity curve to csv
    # numDays = len(results.observers[0].value)
    # arr = results.observers[0].value.get(0,numDays)
    # f = open("thing"+str(i)+".csv", 'w')
    # for price in arr:
    #     f.write("{}\n".format(price))
    # f.close()
    # i += 1

    # cerebro.plot()