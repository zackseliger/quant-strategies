import backtrader as bt
import backtrader.indicators as btind
from Indicators import *
from stats.stats import Statistics

class System1(bt.Strategy):
  params = (
    ('log', False),
    ('recordstats', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d, avglength=15, sumlength=50)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.madiff = ZackMADiff(d, period=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

      d.atr = btind.AverageTrueRange(d, period=14)

    if self.p.log:
      self.logfile = open('system1.txt', 'w')

    if self.p.recordstats:
      self.statsfile = Statistics()

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

      # for doing stats
      if self.p.recordstats:
        d = order.data
        if order.isbuy():
          self.statsfile.newpoint(ticker=d._name, date=str(self.data.datetime.date(0)), atr=d.atr[-1])
        else:
          point = self.statsfile.getpoint('ticker', order.data._name)
          self.statsfile.completepoint(point, pnl=order.executed.pnl)

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    available_cash = self.broker.get_cash()

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0: # if we have a position
        if (d.aroon.aroondown > 70 and d.aroon.aroondown>d.aroon.aroondown[-1]) or d.overma-d.overma[-1] < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)

    # buy
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)
      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      if d.overma-d.overma[-1] >= 0 and d.overma > -0.5: # trend indicator
        if d.volsig.up > d.volsig.down: # trend indicator #2
          if d.madiff[0]-d.madiff[-1] > 0: # final indicator
            self.buy(d, size=buysize)
            available_cash -= d*buysize
            # stoploss
            d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

class System1Test(bt.Strategy):
  params = (
    ('log', False),
    ('recordstats', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d, avglength=15, sumlength=50)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.madiff = ZackMADiff(d, period=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

      d.atr = btind.AverageTrueRange(d, period=14)

    if self.p.log:
      self.logfile = open('system1.txt', 'w')

    if self.p.recordstats:
      self.statsfile = Statistics()

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

      # for doing stats
      if self.p.recordstats:
        d = order.data
        if order.isbuy():
          self.statsfile.newpoint(ticker=d._name, date=str(self.data.datetime.date(0)), atr=d.atr[-1])
        else:
          point = self.statsfile.getpoint('ticker', order.data._name)
          self.statsfile.completepoint(point, pnl=order.executed.pnl)

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    available_cash = self.broker.get_cash()

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0: # if we have a position
        if (d.aroon.aroondown > 70 and d.aroon.aroondown>d.aroon.aroondown[-1]) or d.overma-d.overma[-1] < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)

    # buy
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)
      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      if d.overma-d.overma[-1] >= 0 and d.overma > -0.5: # trend indicator
        if d.volsig.up > d.volsig.down: # trend indicator #2
          if d.madiff[0]-d.madiff[-1] > 0: # final indicator
            self.buy(d, size=buysize)
            available_cash -= d*buysize
            # stoploss
            d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)