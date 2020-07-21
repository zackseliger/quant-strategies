import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class VolSZOStratOne(bt.Strategy):
  params = (
    ('szolength',5),
    ('sumlength',12),
    ('signal_percent',95),
    ('adxperiod',7),
    ('malength',50)
  )

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED "+str(order.executed.price)+"\n")

  def __init__(self):
    self.sma = []
    self.adx = []
    self.volszo = []
    self.logfile = open('log.txt', 'w')

    for d in self.datas:
      self.adx.append(btind.AverageDirectionalMovementIndex(d, period=self.p.adxperiod))
      self.volszo.append(VolSZO(d, szolength=self.p.szolength, sumlength=self.p.sumlength, signal_percent=self.p.signal_percent))

  def next(self):

    i = 0
    for d in self.datas:
      if self.getposition(d).size > 0 and self.volszo[i].szo[0] <= self.volszo[i].buy[0] and self.volszo[i].szo[-1] > self.volszo[i].buy[-1]:
        self.sell(d, size=self.getposition(d).size)
        self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(d.close[0])+"\n")

    i = 0
    for d in self.datas:
      buysize = int(self.broker.get_cash() / 120*self.adx[i] / d)
      if self.adx[i] > 25 and self.volszo[i].szo[0] <= self.volszo[i].sell[0] and self.volszo[i].szo[-1] > self.volszo[i].sell[-1]:
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(d.close[0])+"\n")

      i += 1

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
    # get top 10 adx stocks
    # top10adx = sorted(self.datas, key=lambda stock: stock.adx, reverse=True)[:10]
    qualitystocks = sorted(self.datas, key=lambda stock: stock.quality.slope, reverse=True)
    qualitystocks = qualitystocks[0:int(0.5*len(qualitystocks))]

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if (d.pivotpoints[0] < 0 and d.pivotpoints[-1] >= 0):
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")
 
    # see if we want to buy
    for d in qualitystocks:
      buysize = int(self.broker.get_value() / 240*d.adx / d)
      if buysize == 0: buysize = 1
# self.adx[i] > 30
# self.smaslope[i] > -0.05 and self.smaslope[i] < 0.1
# stop loss at -1.5x ATR and TP at 1xATR
      if d.smaslope > -0.05 and d.pivotpoints[0] > 0 and d.pivotpoints[-1] <= 0:
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")

class OverMAStrat(bt.Strategy):
  params = (
    ('avglength', 15),
    ('sumlength', 50),
    ('atrperiod', 50),
    ('pivotavglength', 10),
    ('pivotsumlength', 5),
    ('mabullpoint', 0.1)
  )

  # def stop(self):
  #   pnl = round(self.broker.getvalue() - 10000,2)
  #   print("param: {} final pnl: {}".format(self.p.test, pnl))

  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.atr = btind.AverageTrueRange(d, period=self.p.atrperiod)
      d.atrp = d.atr/d # atr as a % of stock price
      d.ma = btind.MovingAverageSimple(d, period=self.p.avglength)
      d.maslope = d.ma(0) - d.ma(-1)
      d.avgvolume = btind.MovingAverageSimple(d.volume, period=self.p.avglength)
      d.pivot = ZackPivotPoints(avglength=self.p.pivotavglength, sumlength=self.p.pivotsumlength)

      self.logfile = open('log.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)+"\n") 

  def next(self):
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp)

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.pivot < 0 and d.pivot[-1] < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")
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

      if d.pivot > 0 and d.maslope > 0: # trend indicators
        if d.overma - d.overma[-1] > 0 and d.overma < self.p.mabullpoint: # main indicator
          self.buy(d, size=buysize)
          available_cash -= d*buysize
          self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")
          # put in stoploss
          # d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d-d.atr)

class TestStrat(bt.Strategy):
  params = (
    ('aroonperiod', 25),
    ('atrperiod', 14),
    ('adxperiod', 14)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=self.p.atrperiod)
      d.aroon = btind.AroonUpDown(d, period=self.p.aroonperiod)
      d.adx = btind.AverageDirectionalMovementIndex(d, period=self.p.adxperiod)
      d.pivotpoints = VolSZO(d, szolength=2, sumlength=12)

      self.logfile = open('log.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)+"\n") 
  #     for d in self.datas:
        # if order == d.stoploss:
        #   print("stopped out")
        # if order == d.takeprofit:
        #   print("taking profit")
        #   # cancel previous stoploss and set new one
        #   self.cancel(d.stoploss)
        #   # d.stoploss = self.sell(d, size=self.getposition(d).size, price=d.takeprofitprice)

  def next(self):
    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit indicator
        if d.pivotpoints[0] < d.pivotpoints.sell and d.pivotpoints[-1] >= d.pivotpoints.sell:
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")
          self.cancel(d.stoploss)
          self.cancel(d.takeprofit)

    # see if we want to buy
    for d in self.datas:
      if self.getposition(d).size > 0:
        continue

      # buysize = int(self.broker.get_value()*0.9 / d)
      buysize = int(0.02*self.broker.get_value()/(d.atr*5))
      # volume indicator
      if d.adx > 20:
        # trend confirmation
        if d.aroon.aroonup > d.aroon.aroondown and d.aroon.aroonup[-1] <= d.aroon.aroondown[-1]:
        # if d.pivotpoints[0] > 0 and d.pivotpoints[-1] <= 0:
          self.buy(d, size=buysize)
          self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")
          # set stoploss and take profit
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d-d.atr*5)
          d.takeprofit = self.sell(d, size=int(buysize/2), exectype=bt.Order.Limit, price=d+d.atr*5)
          d.takeprofitprice = d+d.atr*5

class MomentumStrat(bt.Strategy):
  params = (
      ('avglength', 21),
      ('sumlength', 20)
    )

  def __init__(self):
    for d in self.datas:
      d.madiff = ZackOverMA(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.ma = btind.MovingAverageSimple(d, period=self.p.avglength)
      d.maslope = d.ma(0) - d.ma(-1)

    self.logfile = open('log.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED "+str(order.executed.price)+"\n")

  def next(self):
    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if (d.madiff[0] < 1 and d.madiff[-1] == 1) or (d.madiff[0] < 1 and d.madiff.slope[0] < 0):
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")

    buysize = int(self.broker.get_value() / 30 / d)
    # see if we want to buy
    for d in self.datas:
      if d.madiff.slope[0] > 0 and d.madiff.slope[-1] <= 0 and d.madiff[0] < 0.1:
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")


class YearDiffBuyStrat(bt.Strategy):
  def __init__(self):
    # self.year_diff = []
    for d in self.datas:
      d.year_diff = (d(0) - d(-200)) / d(0)

    self.logfile = open('log.txt', 'w')

  def next(self):
    stocks = sorted(self.datas, key=lambda stock: stock.year_diff, reverse=True)
    top10 = stocks[:10]

    # sell if we have a position not in the top 10
    i = 0
    for d in self.datas:
      if self.getposition(d).size > 0 and d not in top10:
        self.sell(d, size=self.getposition(d).size)
        self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")

    # buy from the top 10 if we have any cash
    i = 0
    cash_to_value = self.broker.get_cash() / self.broker.get_value()
    for d in self.datas:
      if cash_to_value >= 0.1 and self.getposition(d).size == 0 and d in top10:
        buysize = int(self.broker.get_value()*0.1 / d)
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")

class BuyAndHoldMulti(bt.Strategy):
  def start(self):
    self.val_start = self.broker.get_cash()

  def nextstart(self):
    for d in self.datas:
      size = int(self.broker.get_cash() / d / len(self.datas))
      self.buy(d, size=size)

class BuyAndHoldSPY(bt.Strategy):
  def nextstart(self):
    for d in self.datas:
      if d._name == "SPY":
        size = int(self.broker.get_cash() / d)
        self.buy(d, size=size)