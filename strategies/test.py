import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
from Indicators import *
from stats.stats import Statistics
import random

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

class DMIStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      dmi = btind.DirectionalMovementIndex(d, period=10)
      d.dmi = dmi.plusDI - dmi.minusDI
      d.extreme = DMIStoch(d, period=10, sumperiod=5)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.volswitch = VolatilitySwitch(d, period=21)

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.atr/stock)
    # orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0: # manage longs
        if d.dmi < 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size
      if self.getposition(d).size < 0: # manage shorts
        if d.dmi > 0: # exit indicator
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size != 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # we want volatility
      if d.volswitch < 0.5:
        continue

      # long signals
      if d.extreme[-1] < 30 and d.extreme >= 30 and d.dmi > 0:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

      # short signals
      if d.extreme[-1] > 70 and d.extreme <= 70 and d.dmi < 0:
        self.sell(d, size=buysize)
        d.long = False
        available_cash -= d*buysize

class Momentum(bt.Strategy):
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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.volsig.up > d.volsig.down:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class AbsStrengthStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)

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
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class PFEStrategy(bt.Strategy):
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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.pfe > 0:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

class GenericAroonStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroonup = btind.AroonUp(d, period=25)
      d.aroondown = btind.AroonDown(d, period=25)
      d.volOsc = VolumeOsc(d, fastPeriod=14, slowPeriod=21)

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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.aroonup > 70:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class VolOscStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroonup = btind.AroonUp(d, period=25)
      d.aroondown = btind.AroonDown(d, period=25)
      d.volOsc = VolumeOsc(d, fastPeriod=14, slowPeriod=21)

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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.aroonup > 70 and d.volOsc > 0:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class VolatilitySwitchStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroonup = btind.AroonUp(d, period=25)
      d.aroondown = btind.AroonDown(d, period=25)
      d.volswitch = VolatilitySwitch(d)

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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.aroonup > 70 and d.volswitch > 0.5:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class RSIStrategy(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroonup = btind.AroonUp(d, period=25)
      d.aroondown = btind.AroonDown(d, period=25)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # long signals
      if d.aroonup > 70 and (d.rsi-50)**2 < 200:
        self.buy(d, size=buysize)
        available_cash -= d*buysize