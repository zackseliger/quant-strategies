import backtrader as bt
import backtrader
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from strategies import *

cerebro = bt.Cerebro()
cerebro.broker = bt.brokers.BackBroker(slip_perc=0.005)
cerebro.broker.setcommission(commission=0.001)
cerebro.addindicator(MT5Accelerator)
cerebro.addindicator(AbsoluteStrengthOscillator)

cerebro.adddata(btfeeds.GenericCSVData(
	dataname='stocks/2016/MSFT.csv',
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