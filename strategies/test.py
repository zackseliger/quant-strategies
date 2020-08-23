import backtrader as bt
import backtrader.indicators as btind
from Indicators import *
from stats.stats import Statistics

class TestStrategy(bt.Strategy):
  params = (
    ('fastperiod', 5),
    ('slowperiod', 10),
    ('log', False),
    ('recordstats', False)
  )

  # def stop(self):
  #   pnl = round(self.broker.getvalue() - 10000,2)
  #   print("param: {} final pnl: {}".format(self.p.test, pnl))

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.dmi = btind.DirectionalMovementIndex(d, period=14)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)

      d.atr = btind.AverageTrueRange(d, period=14)

    if self.p.log:
      self.logfile = open('teststrat.txt', 'w')

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
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atr/stock, reverse=True)
    available_cash = self.broker.get_cash()

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0: # if we have a position
        if d.dmi.minusDI > d.dmi.plusDI: # exit indicator
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
      if self.p.recordstats: buysize = int(2000/d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      if d.volsig.up > d.volsig.down:
        if d.dmi.plusDI > d.dmi.minusDI:
          self.buy(d, size=buysize)
          available_cash -= d*buysize
          # info for stoploss
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

class LongShort(bt.Strategy):
  params = (
    ('log', False),
    ('recordstats', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.baseline = btind.ExponentialMovingAverage(d, period=21)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)
      d.volma = btind.MovingAverageSimple(d.volume, period=12)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.rex = RexOscillator(d, period=14)
      d.volszo = VolSZO(d, szolength=2, sumlength=7)
      d.schaff = SchaffTrend(d)
      d.madiff = ZackMADiff(d, period=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.pivot = ZackPivotPoints(d, avglength=5, sumlength=5)
      d.trix = btind.Trix(period=14)

      d.atr = btind.AverageTrueRange(d, period=14)

    if self.p.log:
      self.logfile = open('longshort.txt', 'w')

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
    orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d < d.baseline or d.trix < 0 or (d.volszo < 0 and d.volszo<d.volszo[-1]) or d.volsig.down > d.volsig.up: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)
      if self.getposition(d).size < 0: # manage shorts
        if d > d.baseline or d.trix > 0 or (d.volszo > 0 and d.volszo>d.volszo[-1]) or d.volsig.up > d.volsig.down: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)
      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.volsig.up > d.volsig.down and d.schaff > 50 and d.volma > d.volma[-1]: # volume indicator
        if d.aroon.aroonup > d.aroon.aroondown and d.madiff > d.madiff[-1]: # confirmation
          self.buy(d, size=buysize)
          d.long = True
          available_cash -= d*buysize
          # stoploss
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

      # short signals
      if d.volsig.up < d.volsig.down and d.schaff < 50 and d.volma > d.volma[-1]: # volume indicator
        if d.aroon.aroonup < d.aroon.aroondown and d.madiff < d.madiff[-1]: # confirmation
          self.sell(d, size=buysize)
          d.long = False
          available_cash -= d*buysize
          # stoploss
          d.stoploss = self.buy(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

class LongShort2(bt.Strategy):
  params = (
    ('log', False),
    ('recordstats', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.baseline = btind.ExponentialMovingAverage(d, period=21)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)
      d.volma = btind.MovingAverageSimple(d.volume, period=12)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.rex = RexOscillator(d, period=14)
      d.volszo = VolSZO(d, szolength=2, sumlength=7)
      d.schaff = SchaffTrend(d)
      d.madiff = ZackMADiff(d, period=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.pivot = ZackPivotPoints(d, avglength=5, sumlength=5)
      d.trix = btind.Trix(period=14)

      d.atr = btind.AverageTrueRange(d, period=14)

    if self.p.log:
      self.logfile = open('longshort2.txt', 'w')

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
    orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d < d.baseline or d.trix < 0 or (d.volszo < 0 and d.volszo<d.volszo[-1]) or d.volsig.down > d.volsig.up: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)
      if self.getposition(d).size < 0: # manage shorts
        if d > d.baseline or d.trix > 0 or (d.volszo > 0 and d.volszo>d.volszo[-1]) or d.volsig.up > d.volsig.down: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
          self.cancel(d.stoploss)

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)
      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.volsig.up > d.volsig.down and d.schaff > 50 and d.volma > d.volma[-1]: # volume indicator
        if d.aroon.aroonup > d.aroon.aroondown and d.madiff > d.madiff[-1]: # confirmation
          self.buy(d, size=buysize)
          d.long = True
          available_cash -= d*buysize
          # stoploss
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

      # short signals
      if d.volsig.up < d.volsig.down and d.schaff < 50 and d.volma > d.volma[-1]: # volume indicator
        if d.aroon.aroonup < d.aroon.aroondown and d.madiff < d.madiff[-1]: # confirmation
          self.sell(d, size=buysize)
          d.long = False
          available_cash -= d*buysize
          # stoploss
          d.stoploss = self.buy(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)