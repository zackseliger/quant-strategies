import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class PivotPointsStrat(bt.Strategy):
  params = (
    ('avglength', 5),
    ('sumlength', 5),
    ('atrlength', 14),
    ('malength', 21),
    ('qualitysumlength', 20),
    ('qualityavglength', 21),
    ('log', False)
  )

  # def stop(self):
  #   pnl = round(self.broker.getvalue() - 10000,2)
  #   print("param: {} final pnl: {}".format(self.p.test, pnl))

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.pivotpoints = ZackPivotPoints(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.sma = btind.MovingAverageSimple(d, period=self.p.malength)
      d.smaslope = d.sma(0) - d.sma(-1)
      d.atr = btind.AverageTrueRange(d, period=self.p.atrlength)
      d.quality = AboveMAAccum(d, avglength=self.p.qualityavglength, sumlength=self.p.qualitysumlength)

    if self.p.log:
      self.logfile = open('pivotpoints.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.log(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.log(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)+"\n")

  def next(self):
    # get top 'quality' stocks
    qualitystocks = sorted(self.datas, key=lambda stock: stock.quality, reverse=True)
    # qualitystocks = qualitystocks[0:int(0.5*len(qualitystocks))]

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if (d.pivotpoints[0] < 0 and d.pivotpoints[-1] >= 0):
          self.sell(d, size=self.getposition(d).size)
          self.log(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")
 
    # see if we want to buy
    available_cash = self.broker.get_cash()
    for d in qualitystocks:
      buysize = int(self.broker.get_value() / d.atr[0] / d)
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
        self.log(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")