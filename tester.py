from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from strategies import *
from Indicators import *

cerebro = bt.Cerebro()

# cerebro.addindicator(btind.MovingAverageSimple, period=50)
cerebro.addstrategy(TestStrategy)
cerebro.addanalyzer(bt.analyzers.AnnualReturn)
cerebro.addanalyzer(bt.analyzers.DrawDown)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, annualize=True, riskfreerate=0.01)

cerebro.adddata(btfeeds.GenericCSVData(
      dataname='stocks/2008/SPY.csv',
      dtformat=('%Y-%m-%d'),

      datetime=0,
      open=1,
      high=2,
      low=3,
      close=4,
      volume=6,
  ))

results = cerebro.run()[0]
# sharpe_ratio = results.analyzers[2].get_analysis()['sharperatio']
# returns = results.analyzers[0].rets
# avg_returns = sum(returns)/len(returns)
# maxdrawdown = results.analyzers[1].get_analysis()['max'].drawdown / 100
# if maxdrawdown == 0: maxdrawdown = 0.0001
# print(
#     str(round(sharpe_ratio,2)) + ", " +
#     str(round(avg_returns,2)) + " / " +
#     str(round(maxdrawdown,2)) + " = " +
#     str(round(avg_returns/maxdrawdown,2))
# )

cerebro.plot()