import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
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
      d.baseline = btind.MovingAverageSimple(d, period=20)
      d.bbands = btind.BollingerBands(d, period=20)
      d.prevhigh = ZackPrevHigh(d, period=10)
      d.bandma_top = btind.MovingAverageSimple(d.prevhigh.top, period=10)
      d.bandma_bot = btind.MovingAverageSimple(d.prevhigh.bot, period=10)
      d.pivot = ZackPivotPoints(d)

      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = d.atr/d

    if self.p.log:
      self.logfile = open('teststrat.txt', 'w')

    if self.p.recordstats:
      self.statsfile = Statistics()

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

      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

      # for doing stats
      if self.p.recordstats:
        d = order.data
        if order.isbuy():
          self.statsfile.newpoint(ticker=d._name, date=str(self.data.datetime.date(0)), atrp=d.atrp[-1])
        else:
          point = self.statsfile.getpoint('ticker', order.data._name)
          self.statsfile.completepoint(point, pnl=order.executed.pnl)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.lowerma[0]-stock.lowerma[-1], reverse=True)
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.atrp, reverse=True)

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0 and d.tookprofit == True: # if we have a position and we hit our first takeprofit
        if d.pivot < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.cancel(d.stoploss)

    # buy
    available_cash = self.broker.get_cash()
    for d in self.datas:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*2
      takeprofit_diff = d.atr[0]*1

      # buysize = int(0.1*self.broker.get_value())
      buysize = int(risk / stoploss_diff)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value()/d)

      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

      if d > d.baseline: # baseline
        if d.bbands.top[0] < d.bbands.top[-1] and d.bbands.bot[0] > d.bbands.bot[-1]: # decreasing volatility
          if d.bandma_top[0] - d.bandma_top[-1] > 0 and d.bandma_bot[0] - d.bandma_bot[-1] > 0: # higher highs higher lows
            self.buy(d, size=buysize)
            available_cash -= d*buysize

            # info for stoplosses, takeprofits, etc
            d.buyprice = d.close[0]
            d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d.close[0]-stoploss_diff)
            d.takeprofit = self.sell(d, size=int(buysize/2), exectype=bt.Order.Limit, price=d.close[0]+takeprofit_diff)
            d.tookprofit = False

class TestStrategy2(bt.Strategy):
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
      d.baseline = btind.MovingAverageSimple(d, period=20)
      d.bbands = btind.BollingerBands(d, period=20)
      d.prevhigh = ZackPrevHigh(d, period=10)
      d.bandma_top = btind.MovingAverageSimple(d.prevhigh.top, period=10)
      d.bandma_bot = btind.MovingAverageSimple(d.prevhigh.bot, period=10)
      d.pivot = ZackPivotPoints(d)

      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = d.atr/d

    if self.p.log:
      self.logfile = open('teststrat.txt', 'w')

    if self.p.recordstats:
      self.statsfile = Statistics()

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

      # logging
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

      # for doing stats
      if self.p.recordstats:
        d = order.data
        if order.isbuy():
          self.statsfile.newpoint(ticker=d._name, date=str(self.data.datetime.date(0)), atrp=d.atrp[-1])
        else:
          point = self.statsfile.getpoint('ticker', order.data._name)
          self.statsfile.completepoint(point, pnl=order.executed.pnl)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.lowerma[0]-stock.lowerma[-1], reverse=True)
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp, reverse=True)

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0 and d.tookprofit == True: # if we have a position and we hit our first takeprofit
        if d.pivot < 0: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          self.cancel(d.stoploss)

    # buy
    available_cash = self.broker.get_cash()
    for d in atrporder:
      if self.getposition(d).size > 0:
        continue

      # useful numbers
      risk = 0.02*self.broker.get_value()
      stoploss_diff = d.atr[0]*2
      takeprofit_diff = d.atr[0]*1

      # buysize = int(0.1*self.broker.get_value())
      buysize = int(risk / stoploss_diff)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value()/d)

      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

      if d > d.baseline: # baseline
        if d.bbands.top[0] < d.bbands.top[-1] and d.bbands.bot[0] > d.bbands.bot[-1]: # decreasing volatility
          if d.bandma_top[0] - d.bandma_top[-1] > 0 and d.bandma_bot[0] - d.bandma_bot[-1] > 0: # higher highs higher lows
            self.buy(d, size=buysize)
            available_cash -= d*buysize

            # info for stoplosses, takeprofits, etc
            d.buyprice = d.close[0]
            d.stoploss = self.sell(d, size=buysize, exectype=bt.Order.Stop, price=d.close[0]-stoploss_diff)
            d.takeprofit = self.sell(d, size=int(buysize/2), exectype=bt.Order.Limit, price=d.close[0]+takeprofit_diff)
            d.tookprofit = False

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
    atrporder = sorted(self.datas, key=lambda stock: stock.atrp, reverse=True)

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
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value()/d)
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