import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class TestStrategy(bt.Strategy):
  params = (
    ('fastlength', 5),
    ('slowlength', 10),
    ('log', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d, avglength=15, sumlength=50)
      d.fastma = btind.ExponentialMovingAverage(d, period=self.p.fastlength)
      d.slowma = btind.ExponentialMovingAverage(d, period=self.p.slowlength)
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = d.atr/d

    if self.p.log:
        self.logfile = open('teststrat.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl))

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.lowerma[0]-stock.lowerma[-1], reverse=True)
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atrp, reverse=True)

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.fastma < d.slowma and d.overma[0] <= d.overma[-1]: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.log(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0]))
          # self.cancel(d.stoploss)

    # buy
    available_cash = self.broker.get_cash()
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      buysize = int(0.5*self.broker.get_value()*d.atrp)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value()/d)
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

      if d.fastma > d.slowma and d.fastma[-1] <= d.slowma and d.overma >= d.overma[-1] and d.overma < 0.1:
        self.buy(d, size=buysize)
        available_cash -= d*buysize
        self.log(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0]))