import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class OverMAStrat(bt.Strategy):
  params = (
    ('avglength', 15),
    ('sumlength', 50),
    ('atrperiod', 50),
    ('pivotavglength', 10),
    ('pivotsumlength', 5),
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
      d.overma = ZackOverMA(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.atr = btind.AverageTrueRange(d, period=self.p.atrperiod)
      d.atrp = d.atr/d # atr as a % of stock price
      d.ma = btind.MovingAverageSimple(d, period=self.p.avglength)
      d.maslope = d.ma(0) - d.ma(-1)
      d.avgvolume = btind.MovingAverageSimple(d.volume, period=self.p.avglength)
      d.pivot = ZackPivotPoints(d, avglength=self.p.pivotavglength, sumlength=self.p.pivotsumlength)

      if self.p.log:
        self.logfile = open('overma.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)) 

  def next(self):
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp)

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.pivot < 0 and d.pivot[-1] < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.log(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0]))
          # self.cancel(d.stoploss)

    # see if we want to buy
    available_cash = self.broker.get_cash()
    for d in atrporder:
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

      if d.pivot[0] > 0 and d.pivot[-1] < 0 and d.maslope > 0: # trend indicators
        if d.overma - d.overma[-1] > 0 and d.overma < 0.1: # main indicator
          self.buy(d, size=buysize)
          available_cash -= d*buysize
          self.log(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0]))
          # put in stoploss
          # d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d-d.atr)

class OverMAStratTest(bt.Strategy):
  params = (
    ('avglength', 15),
    ('sumlength', 50),
    ('atrperiod', 50),
    ('pivotavglength', 10),
    ('pivotsumlength', 5),
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
      d.overma = ZackOverMA(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.atr = btind.AverageTrueRange(d, period=self.p.atrperiod)
      d.atrp = d.atr/d # atr as a % of stock price
      d.ma = btind.MovingAverageSimple(d, period=self.p.avglength)
      d.maslope = d.ma(0) - d.ma(-1)
      d.avgvolume = btind.MovingAverageSimple(d.volume, period=self.p.avglength)
      d.pivot = ZackPivotPoints(d, avglength=self.p.pivotavglength, sumlength=self.p.pivotsumlength)
      d.pivot2 = ZPP(d, avglength=9)

      if self.p.log:
        self.logfile = open('overma.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)) 

  def next(self):
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp)

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.pivot2.sell > 0 and d.overma[0] - d.overma[-1] < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.log(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0]))
          self.cancel(d.stoploss)

    # see if we want to buy
    available_cash = self.broker.get_cash()
    for d in atrporder:
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

      if d.pivot[0] > 0 and d.maslope > 0: # trend indicators
        if d.overma - d.overma[-1] > 0 and d.overma < 0.1: # main indicator
          self.buy(d, size=buysize)
          available_cash -= d*buysize
          self.log(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0]))
          # put in stoploss
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d-d.atr*2)