import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *
from stats.stats import Statistics

class MACrossoverStrat(bt.Strategy):
  params = (
    ('fastlength', 5),
    ('slowlength', 10),
    ('log', False),
    ('recordstats', False)
  )

  def log(self, message):
    if self.p.log:
      self.logfile.write(message+"\n")

  def __init__(self):
    for d in self.datas:
      d.overma = ZackOverMA(d, avglength=15, sumlength=50)
      d.fastma = btind.ExponentialMovingAverage(d, period=self.p.fastlength)
      d.slowma = btind.ExponentialMovingAverage(d, period=self.p.slowlength)
      d.atr = btind.AverageTrueRange(d, period=14)
      d.atrp = d.atr/d

    if self.p.log:
      self.logfile = open('ma_crossover_strat.txt', 'w')

    if self.p.recordstats:
      self.statsfile = Statistics()

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if not order.isbuy():
        self.log(str(self.data.datetime.date(0))+" SELL "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2))+" P/L: $"+str(order.executed.pnl))
      else:
        self.log(str(self.data.datetime.date(0))+" BUY "+order.data._name+" "+str(order.size)+" "+str(round(order.executed.price,2)))

      # for doing stats
      if self.p.recordstats:
        d = order.data
        if order.isbuy():
          self.statsfile.newpoint(ticker=d._name, atrp=d.atrp[-1])
        else:
          point = self.statsfile.getpoint('ticker', order.data._name)
          self.statsfile.completepoint(point, pnl=order.executed.pnl)

  def next(self):
    # orderedstocks = sorted(self.datas, key=lambda stock: stock.lowerma[0]-stock.lowerma[-1], reverse=True)
    orderedstocks = sorted(self.datas, key=lambda stock: stock.atrp, reverse=True)

    # sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if d.fastma < d.slowma: # exit indicator
          self.sell(d, size=self.getposition(d).size)
          # self.cancel(d.stoploss)

    # buy
    available_cash = self.broker.get_cash()
    for d in self.datas:
      if self.getposition(d).size > 0:
        continue

      buysize = int(0.5*self.broker.get_value()*d.atrp)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value()/d)
      if self.p.recordstats: buysize = int(2000/d) # FOR TESTING TEMP!!!!!!!!!!!!!
      # we can't spend more than all our money
      if available_cash/d < buysize:
        if available_cash > d:
          buysize = int(available_cash/d)
        else:
          continue

      if d.fastma > d.slowma and d.fastma[-1] <= d.slowma[-1]:
        self.buy(d, size=buysize)
        available_cash -= d*buysize