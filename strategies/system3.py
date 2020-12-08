import backtrader as bt
import backtrader.indicators as btind
from Indicators import *
from stats.stats import Statistics

class System3(bt.Strategy):
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
      d.mfi = MoneyFlowIndex(d, period=14)
      d.volswitch = VolatilitySwitch(d, period=21)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)

      if self.p.log:
        self.logfile = open('system3.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.volswitch, reverse=True)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit indicator
        if (d.aroon.aroondown > 70 and d.aroon.aroondown-d.aroon.aroondown[-1] > 0): # exit indicator
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

      # we want a close-to-neutral RSI
      if (d.mfi-50)**2 > 50:
        continue

      # long signals
      if d.aroon.aroonup > d.aroon.aroondown and d.strength.bears < d.strength.bears[-1]:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize

class System3Test(bt.Strategy):
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
      d.mfi = MoneyFlowIndex(d, period=14)
      d.volswitch = VolatilitySwitch(d, period=21)
      d.strength = AbsoluteStrengthOscillator(d, movav=btind.MovAv.Smoothed)

      if self.p.log:
        self.logfile = open('system3.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

  def next(self):
    orderedstocks = sorted(self.datas, key=lambda stock: stock.volswitch, reverse=True)
    available_cash = self.broker.get_cash()

    # close positions
    for d in self.datas:
      if self.getposition(d).size > 0:
        # exit indicator
        if (d.aroon.aroondown > 70 and d.aroon.aroondown-d.aroon.aroondown[-1] > 0): # exit indicator
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

      # we want a close-to-neutral RSI
      if (d.mfi-50)**2 > 50:
        continue

      # long signals
      if d.aroon.aroonup > d.aroon.aroondown and d.strength.bears < d.strength.bears[-1]:
        self.buy(d, size=buysize)
        d.long = True
        available_cash -= d*buysize