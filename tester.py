import backtrader as bt
import backtrader
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from strategies import *

cerebro = bt.Cerebro()
cerebro.addstrategy(System2)

cerebro.adddata(btfeeds.GenericCSVData(
	dataname='stocks/2016/BAC.csv',
	dtformat=('%Y-%m-%d'),

	datetime=0,
	open=1,
	high=2,
	low=3,
	close=4,
	volume=6
))

cerebro.run()
cerebro.plot()