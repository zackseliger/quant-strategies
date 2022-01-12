import backtrader as bt
import backtrader
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from strategies import *

cerebro = bt.Cerebro()
cerebro.broker = bt.brokers.BackBroker(slip_perc=0.005)
cerebro.broker.setcommission(commission=0.001)
# cerebro.addstrategy(System2)
cerebro.addindicator(DidiIndex)

cerebro.adddata(btfeeds.GenericCSVData(
	dataname='stocks/growth2019/FSLY.csv',
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

cerebro.run()
cerebro.plot()