import backtrader as bt
import backtrader.indicators as btind
from Indicators import *
from stats.stats import Statistics

class System2(bt.Strategy):
  params = (
      ('log', False),
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroon = btind.AroonUpDown(d, period=25)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)
      d.volsig = ZackVolumeSignal(d)
      d.volOsc = VolumeOsc(d, fastPeriod=14, slowPeriod=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

      if self.p.log:
        self.logfile = open('system2.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.aroon.aroondown > 70 and d.aroon.aroondown-d.aroon.aroondown[-1] > 0)
        cond2 = (d.volsig.down > d.volsig.up and d.volsig.down[-1] <= d.volsig.up[-1])
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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # we want volatility
      if d.volOsc > d.volOsc[-1]:
        continue

      # long signals
      if d.volsig.up > d.volsig.down or d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class System2Test(bt.Strategy):
  params = (
      ('log', False),
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroon = btind.AroonUpDown(d, period=25)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)
      d.volsig = ZackVolumeSignal(d)
      d.volOsc = VolumeOsc(d, fastPeriod=14, slowPeriod=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

      if self.p.log:
        self.logfile = open('system2test.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.aroon.aroondown > 70 and d.aroon.aroondown-d.aroon.aroondown[-1] > 0)
        cond2 = (d.volsig.down > d.volsig.up and d.volsig.down[-1] <= d.volsig.up[-1])
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
      buysize = int(risk / stoploss_diff)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # we want volatility
      if d.volOsc > d.volOsc[-1]:
        continue

      # long signals
      if d.volsig.up > d.volsig.down or d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class System2Test2(bt.Strategy):
  params = (
      ('log', False),
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)
      d.volswitch = VolatilitySwitch(d, period=21)
      d.pfe = PolarizedFractalEfficiency(d)
      d.minmax = ZackMinMax(d, period=20)

      if self.p.log:
        self.logfile = open('system2test2.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.minmax/stock)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.pfe < 0 or d < d.minmax.mid or (d.strength.bears > d.strength.bulls and d.strength.bears[-1] <= d.strength.bulls[-1]): # exit indicator
          self.close(d, size=self.getposition(d).size)
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

      # we want volatility
      if d.volswitch < 0.5:
        continue

      # long signals
      if d.pfe > 0 and d-d.minmax.mid > 0 and d-d.minmax.mid < d.atr:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

class System2Crypto(bt.Strategy):
  params = (
      ('log', False),
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.aroon = btind.AroonUpDown(d, period=25)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)
      d.volsig = ZackVolumeSignal(d)
      d.volOsc = VolumeOsc(d, fastPeriod=14, slowPeriod=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

      if self.p.log:
        self.logfile = open('system2crypto.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: (stock.rsi-50)**2)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit conditions
        cond1 = (d.aroon.aroondown > 70 and d.aroon.aroondown-d.aroon.aroondown[-1] > 0)
        cond2 = (d.volsig.down > d.volsig.up and d.volsig.down[-1] <= d.volsig.up[-1])
        if cond1 or cond2:
          self.close(d, size=self.getposition(d).size)
          available_cash += d*self.getposition(d).size

    # open positions
    for d in orderedstocks:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*3
      buysize = round(risk / stoploss_diff, 5)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      # we want volatility
      if d.volOsc > d.volOsc[-1]:
        continue

      # long signals
      if d.volsig.up > d.volsig.down or d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize