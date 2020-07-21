import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class MomentumStrat(bt.Strategy):
  params = (
      ('avglength', 21),
      ('sumlength', 20)
    )

  def __init__(self):
    for d in self.datas:
      d.madiff = ZackOverMA(d, avglength=self.p.avglength, sumlength=self.p.sumlength)
      d.ma = btind.MovingAverageSimple(d, period=self.p.avglength)
      d.maslope = d.ma(0) - d.ma(-1)

    self.logfile = open('log.txt', 'w')

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED "+str(order.executed.price)+"\n")

  def next(self):
    # see if we want to sell
    for d in self.datas:
      if self.getposition(d).size > 0:
        if (d.madiff[0] < 1 and d.madiff[-1] == 1) or (d.madiff[0] < 1 and d.madiff.slope[0] < 0):
          self.sell(d, size=self.getposition(d).size)
          self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(self.getposition(d).size) + " " + str(d.close[0])+"\n")

    buysize = int(self.broker.get_value() / 30 / d)
    # see if we want to buy
    for d in self.datas:
      if d.madiff.slope[0] > 0 and d.madiff.slope[-1] <= 0 and d.madiff[0] < 0.1:
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(buysize) + " " + str(d.close[0])+"\n")