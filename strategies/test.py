import backtrader as bt
import backtrader.indicators as btind
from Indicators import *
from stats.stats import Statistics

class TestStrategy(bt.Strategy):
  params = (
    ('fastperiod', 5),
    ('slowperiod', 10),
    ('log', True),
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
      d.overma = ZackOverMA(d, avglength=15, sumlength=50)
      d.volsig = ZackVolumeSignal(d, avgvollength=12, period=7)
      d.aroon = btind.AroonUpDown(d, period=14)
      d.madiff = ZackMADiff(d, period=21)
      d.rsi = btind.RelativeStrengthIndex(d, period=14)

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
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.lowerma[0]-stock.lowerma[-1], reverse=True)
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
      if self.p.recordstats: buysize = int(2000/d)

      # we can't spend more than all our money
      if available_cash/d < buysize:
        continue

      if d.overma-d.overma[-1] >= 0 and d.overma > -0.5: # trend indicators
        if d.volsig.up > d.volsig.down: # trend indicator #2
          if d.madiff-d.madiff[-1] > 0: # final indicator
            self.buy(d, size=buysize)
            available_cash -= d*buysize
            # info for stoploss
            d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.StopTrail, trailamount=stoploss_diff)

class TestStrategy2(bt.Strategy):
  params = (
    ('fastperiod', 5),
    ('slowperiod', 10),
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
      self.logfile = open('teststrat2.txt', 'w')

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
          self.statsfile.newpoint(ticker=d._name, date=str(self.data.datetime.date(0)), atr=d.atr[-1], avgvel=d.baseline[-1], avgvelsquared=d.baseline[-1]**2, volup=d.volsig.up[-1], volupslope=d.volsig.up[-1]-d.volsig.up[-2])
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

class OverMATest(bt.Strategy):
  params = (
    ('avglength', 15),
    ('sumlength', 50),
    ('atrperiod', 14),
    ('pivotavglength', 5),
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
      d.pivot2 = ZPP(d, avglength=9)

      if self.p.log:
        self.logfile = open('overma.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      # takeprofit and moving stoploss up
      if order == order.data.takeprofit:
        self.cancel(order.data.stoploss)
        order.data.stoploss = self.sell(order.data, exectype=bt.Order.Stop, size=self.getposition(order.data).size, price=order.data.buyprice)
        order.data.tookprofit = True
      # stoploss and resetting
      elif order == order.data.stoploss:
        self.cancel(order.data.takeprofit)
        order.data.tookprofit = False

      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL EXECUTED P/L: $"+str(order.executed.pnl)) 

  def next(self):
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp)

    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0 and d.tookprofit == True:
        if d.pivot2.sell > 0 and d.overma[0] < d.overma[-1]: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.log(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0]))
          self.cancel(d.stoploss)

    # see if we want to buy
    available_cash = self.broker.get_cash()
    for d in atrporder:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*2
      takeprofit_diff = d.atr[0]*1

      buysize = int(risk / stoploss_diff)
      # position can't be larger than 10% of our account
      # if d*buysize > 0.1*self.broker.get_value():
      #   buysize = int(0.1*self.broker.get_value()/d)
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

      if d.maslope > 0: # trend indicators
        if d.overma - d.overma[-1] > 0: # main indicator
          self.buy(d, size=buysize)
          available_cash -= d*buysize
          self.log(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0]))
          # put in stoploss
          d.buyprice = d.close[0]
          d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d.close[0]-stoploss_diff)
          d.takeprofit = self.sell(d, size=int(buysize/2), exectype=bt.Order.Limit, price=d.close[0]+takeprofit_diff)
          d.tookprofit = False