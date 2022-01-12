import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
from Indicators import *
from stats.stats import Statistics
import random
import datetime

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

class AroonLongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.aroon = btind.AroonUpDown(d, period=14)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.aroon.aroondown > d.aroon.aroonup: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.aroon.aroonup > d.aroon.aroondown: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash < buysize*d:
        continue

      # long signals
      if d.aroon.aroonup > d.aroon.aroondown: # volume indicator
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.aroon.aroondown > d.aroon.aroonup: # volume indicator
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class OverMALongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d)
      d.signal = btind.ExponentialMovingAverage(d.overma, period=9)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.overma < d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.overma > d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.overma > d.signal:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.overma < d.signal:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class InverseOverMALongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d)
      d.signal = btind.ExponentialMovingAverage(d.overma, period=9)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.overma > d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.overma < d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.overma < d.signal:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.overma > d.signal:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class AvgVelLongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.avgvel = ZackAverageVelocity(d)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.avgvel < 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.avgvel > 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.avgvel > 0:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.avgvel < 0:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class AvgVelSignalLongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.avgvel = ZackAverageVelocity(d)
      d.signal = btind.ExponentialMovingAverage(d.avgvel, period=50)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.avgvel < d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.avgvel > d.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.avgvel > d.signal:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.avgvel < d.signal:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class MACDLongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.macd = btind.MACD(d)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.macd < d.macd.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.macd > d.macd.signal: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.macd > d.macd.signal:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.macd < d.macd.signal:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class EMALongShort(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.ma = btind.ExponentialMovingAverage(d, period=50)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.volume/stock.volma)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d < d.ma: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d > d.ma: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      buysize = int(self.broker.get_cash() / d / 2)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d > d.ma:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d < d.ma:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class SPYTestStrat(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.ma = btind.ExponentialMovingAverage(d, period=50)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.diff = d.aroon.aroonup(0) - d.aroon.aroondown(0)
      d.atr = btind.AverageTrueRange(d, period=14)
      d.rsi = btind.RSI(d, period=14)
      if d._name == "SPY":
        self.spy = d

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atr/stock)
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.aroon.aroondown > 70 and d.aroon.aroondown > d.aroon.aroondown[-1]: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.aroon.aroonup > 70 and d.aroon.aroonup > d.aroon.aroonup[-1]: # exit indicator
          self.buy(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d > d.ma and d.rsi > self.spy.rsi:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d < d.ma and d.rsi < self.spy.rsi:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class MomentumStrategy(bt.Strategy):
  params = (
    ('positions', 10),
  )

  def __init__(self):
    self.rebalanced = False

    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=20)
      d.sma = btind.MovingAverageSimple(d, period=200)
      d.roc = btind.RateOfChange100(d, period=200)
      d.rsi = btind.RelativeStrengthIndex(d, period=20)

  def next(self):
    curdate = self.datetime.date(ago=0)
    if curdate.weekday() > 2 or self.rebalanced == True:
      if curdate.weekday() > 2:
        self.rebalanced = False
      return
    self.rebalanced = True

    rank = self.getrank
    orderedstocks = sorted(self.datas, key=lambda stock: rank(stock), reverse=True)

    # rebalance
    for d in self.datas:
      # sell stocks
      condSell1 = orderedstocks.index(d)+1 > self.p.positions
      condSell2 = d.sma < d
      if self.getposition(d).size != 0 and (condSell1 or condSell2):
        self.close(d, size=self.getposition(d).size)

      # numbers
      posSize = int(self.broker.get_value() / d / self.p.positions)

      # we can't spend more than all our money
      if self.broker.get_cash() <= 0:
        continue

      # buy stocks
      condBuy1 = d > d.sma
      if condBuy1:
        self.order_target_size(d, posSize)
        
  def getrank(self, stock):
    return stock.roc - abs(stock.rsi-50)

class VolumeSignalStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.volsig = ZackVolumeSignal(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond2 = (d.volsig.down > d.volsig.up and d.volsig.down[-1] <= d.volsig.up[-1])
        if cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.volsig.up > d.volsig.down:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class VolumeSignalStDevStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.volsig = ZackVolumeSignalStdDev(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond2 = (d.volsig.down > d.volsig.up and d.volsig.down[-1] <= d.volsig.up[-1])
        if cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.volsig.up > d.volsig.down:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class MT5AcceleratorStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.mtAcc = MT5Accelerator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.mtAcc < 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.mtAcc > 0:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class PFEStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.pfe = PolarizedFractalEfficiency(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.pfe < 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.pfe > 0:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

class DMIStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.dmi = btind.DirectionalMovementIndex(d, period=14, movav=btind.MovAv.Hull)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.dmi.minusDI > d.dmi.plusDI: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.dmi.plusDI > d.dmi.minusDI:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class AroonStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroonup = btind.AroonUp(d, period=25)
      d.aroondown = btind.AroonDown(d, period=25)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.aroondown > 70 and d.aroondown > d.aroondown[-1]: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.aroonup > 70:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class RSIStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.rsi < 70 and d.rsi[-1] >= 70: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.rsi > 30:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class SecondRSIStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.adx = btind.AverageDirectionalMovementIndex(d, period=5)
      d.rsi = MoneyFlowIndex(d, period=2)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.close > d.high[-1]: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.rsi < 15 and d.adx > 35:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class GeneratedStrategy2(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.schaff = SchaffTrend(d)
      d.sma = btind.MovingAverageSimple(d)

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.schaff)

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.aroon.aroondown - d.sma < 19 - d.aroon.aroonup: # exit indicator
          self.close(d, size=self.getposition(d).size)

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if self.broker.get_cash() < buysize*d:
        continue

      # long signals
      if True:
        self.buy(d, size=buysize)

class MixedStrategy1(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.volsig = ZackVolumeSignal(d)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.volsig.down > d.volsig.up and d.volsig.down > d.volsig.down[-1])
        cond2 = (d.rsi < 70 and d.rsi[-1] > 70)
        if cond1 or cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*5
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class MixedStrategy2(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.volsig = ZackVolumeSignal(d)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.volsig.down > d.volsig.up and d.volsig.down > d.volsig.down[-1])
        cond2 = (d.rsi < 70 and d.rsi[-1] > 70)
        if cond1 or cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*4
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class BearishEngulfingStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = d.close > d.high[-1]
        if cond1:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*4
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      cond1 = d.close < d.open
      cond2 = d.close[-1] > d.open[-1]
      cond3 = d.open > d.close[-1]
      cond4 = d.close < d.open[-1]
      if cond1 and cond2 and cond3 and cond4:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class BBandsStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.bbands = btind.BollingerBands(d, period=20, devfactor=2.0, movav=btind.MovAv.Exponential)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        if d > d.bbands.mid or d < d.stoploss:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*4
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d < d.bbands.bot:
        self.buy(d, size=buysize)
        d.stoploss = d - stoploss_diff
        available_cash -= d*buysize

class CanslimStrategy(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = ATRP(d)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.volsig = ZackVolumeSignal(d)

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atr/stock, reverse=True)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.volsig.down > d.volsig.down[-1] and d.volsig.down > d.volsig.up)
        cond2 = d < d.stoploss
        cond3 = (d.rsi < 70 and d.rsi[-1] > 70 and d.rsi[-2] > 70 and d.rsi[-3] > 70)
        if cond1 or cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*4
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      cond1 = d.rsi < 70
      cond2 = d.volsig.up > d.volsig.up[-1] and d.volsig.up > d.volsig.down
      if cond2:
        self.buy(d, size=buysize)
        d.stoploss = d - stoploss_diff
        available_cash -= d*buysize

class CanslimStrategyTest(bt.Strategy):
  params = (
    ('interday', False),
    ('crypto', False)
  )

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = ATRP(d)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.volsig = ZackVolumeSignal(d)
      d.ma = btind.MovAv.Exponential(d, period=20)
      self.numpos = 0

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atr/stock, reverse=True)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.volsig.down > d.volsig.down[-1] and d.volsig.down > d.volsig.up)
        cond2 = d < d.stoploss
        cond3 = (d.rsi < 70 and d.rsi[-1] > 70 and d.rsi[-2] > 70 and d.rsi[-3] > 70)
        if cond1 or cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # calculate averages
    avgrsi = 0
    for d in self.datas:
      avgrsi += d.rsi
    avgrsi /= len(self.datas)

    # open positions
    for d in orderedstocks:
      # useful numbers
      risk = 0.01*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      if self.p.interday == True:
        risk = 0.01*self.broker.get_value()
        stoploss_diff = d.atr[0]*4
      buysize = int(risk / stoploss_diff)
      if self.p.crypto == True:
        buysize = risk / stoploss_diff

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      cond1 = d.atrp < 0
      cond2 = d.volsig.up > d.volsig.up[-1] and d.volsig.up > d.volsig.down
      cond3 = d.rsi > avgrsi
      cond4 = (d.high+d.low+d.close)/3 > d.ma
      if cond2 and cond1 and cond4:
        self.buy(d, size=buysize)
        d.stoploss = d - stoploss_diff
        available_cash -= d*buysize

class AbsStrengthStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = AbsoluteStrengthOscillator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.strength.bears > d.strength.bulls and d.strength.bears[-1] <= d.strength.bulls[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.bulls > d.strength.bears and d.strength.bulls[-1] <= d.strength.bears[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class VortexStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = Vortex(d, period=7)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.strength.VID > d.strength.VIU and d.strength.VID[-1] <= d.strength.VIU[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.VIU > d.strength.VID and d.strength.VIU[-1] <= d.strength.VID[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class RVIStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = RVI(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.strength.sig > d.strength.rvi and d.strength.sig[-1] <= d.strength.rvi[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.rvi > d.strength.sig and d.strength.rvi[-1] <= d.strength.sig[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class RVIStrategy2(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = RVI(d)
      d.atr = btind.AverageTrueRange(d, period=14)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.low <= d.stop_point:
          self.close(d, size=self.getposition(d).size, price=d.stop_point)
          available_cash += d*self.getposition(d).size
        elif d.high >= d.profit_point:
          self.close(d, size=self.getposition(d).size, price=d.profit_point)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.rvi > d.strength.sig and d.strength.rvi[-1] <= d.strength.sig[-1]:
        d.stop_point = d.close-d.atr*2
        d.profit_point = d.close+d.atr*3
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class HLCTrendStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = HLCTrend(d, close_period=2, low_period=8, high_period=27)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.strength.down > d.strength.up and d.strength.down[-1] <= d.strength.up[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.up > d.strength.down and d.strength.up[-1] <= d.strength.down[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize


class ZackLargestCandleStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.strength = ZackLargestCandle(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.strength.down > d.strength.up and d.strength.down[-1] <= d.strength.up[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.up > d.strength.down and d.strength.up[-1] <= d.strength.down[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class DidiIndexStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.didi = DidiIndex(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.didi.down > d.didi.up and d.didi.down[-1] <= d.didi.up[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.didi.up > d.didi.down and d.didi.up[-1] <= d.didi.down[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class MADiffStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.diff = MADiff(d, short=6, long=19, movav=btind.MovAv.Exponential)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if (d.diff.sig < 0 and d.diff.sig[-1] >= 0): # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      buysize = int(0.1*self.broker.get_value() / d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.diff.sig > 0 and d.diff.sig[-1] <= 0:
        self.buy(d, size=buysize)
        available_cash -= d*buysize