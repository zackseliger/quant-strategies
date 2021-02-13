import backtrader as bt
import backtrader.indicators as btind
from Indicators import *

class System3(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrStdDev = btind.StdDev(d.atr, period=14)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit indicator
        if (d.strength.bears > d.strength.bulls):
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

      # long signals
      if d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize

class System3Test(bt.Strategy):
  def __init__(self):
    for d in self.datas:
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrStdDev = btind.StdDev(d.atr, period=14)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.strength = AbsoluteStrengthOscillator(d)

  def next(self):
    orderedstocks = self.datas
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit indicator
        cond2 = (d.strength.bears > d.strength.bulls)
        if cond2: # exit indicator
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

      # long signals
      if d.strength.bulls > d.strength.bears:
        self.buy(d, size=buysize)
        available_cash -= d*buysize