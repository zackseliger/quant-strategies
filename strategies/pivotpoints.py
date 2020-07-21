import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class PivotPointsStrat(bt.Strategy):
  params = (
    ('avglength', 5),
    ('sumlength', 5),
    ('adxlength', 5),
    ('malength', 21)
  )

  def __init__(self):
    for d in self.datas:
      d.pivotpoints = ZackPivotPoints(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.adx = btind.AverageDirectionalMovementIndex(d, period=self.p.adxlength)
      d.sma = btind.MovingAverageSimple(d, period=self.p.malength)
      d.smaslope = d.sma(0) - d.sma(-1)
      d.adx = btind.AverageDirectionalMovementIndex(d, period=self.p.adxlength)
      d.quality = AboveMAAccum(d, avglength=self.p.malength)

    self.logfile = open('log.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)+"\n")

  def next(self):
    # get top 'quality' stocks
    qualitystocks = sorted(self.datas, key=lambda stock: stock.quality.slope, reverse=True)
    qualitystocks = qualitystocks[0:int(0.5*len(qualitystocks))]

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if (d.pivotpoints[0] < 0 and d.pivotpoints[-1] >= 0):
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")
 
    # see if we want to buy
    available_cash = self.broker.get_cash()
    for d in qualitystocks:
      buysize = int(self.broker.get_value() / 240*d.adx / d)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value() / d)
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

# self.adx[i] > 30
# self.smaslope[i] > -0.05 and self.smaslope[i] < 0.1
# stop loss at -1.5x ATR and TP at 1xATR
      if d.smaslope > -0.05 and d.pivotpoints[0] > 0 and d.pivotpoints[-1] <= 0:
        self.buy(d, size=buysize)
        available_cash -= d*buysize
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")