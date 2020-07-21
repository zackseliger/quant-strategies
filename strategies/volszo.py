import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc
from Indicators import *

class VolSZOStrat(bt.Strategy):
  params = (
    ('szolength',5),
    ('sumlength',12),
    ('signal_percent',95),
    ('adxperiod',7),
    ('malength',50)
  )

  def notify_order(self, order):
    if order.status in [order.Completed]:
      if order.isbuy():
        self.logfile.write(str(self.data.datetime.date(0))+" BUY EXECUTED "+str(order.executed.price)+"\n")
      else:
        self.logfile.write(str(self.data.datetime.date(0))+" SELL EXECUTED "+str(order.executed.price)+"\n")

  def __init__(self):
    self.sma = []
    self.adx = []
    self.volszo = []
    self.logfile = open('log.txt', 'w')

    for d in self.datas:
      d.adx = btind.AverageDirectionalMovementIndex(d, period=self.p.adxperiod)
      d.volszo = VolSZO(d, szolength=self.p.szolength, sumlength=self.p.sumlength, signal_percent=self.p.signal_percent)

  def next(self):
    # sell things
    for d in self.datas:
      if self.getposition(d).size > 0 and d.volszo.szo <= d.volszo.buy and d.volszo.szo[-1] > d.volszo.buy[-1]:
        self.sell(d, size=self.getposition(d).size)
        self.logfile.write(str(d.datetime.date(0)) + " SELL " + d._name + " " + str(d[0])+"\n")

    # buy things
    for d in self.datas:
      buysize = int(self.broker.get_cash() / 120*d.adx / d)
      # position can't be larger than 10% of our account
      if d*buysize > 0.1*self.broker.get_value():
        buysize = int(0.1*self.broker.get_value() / d)

      if d.adx > 25 and d.volszo.szo[0] <= d.volszo.sell[0] and d.volszo.szo[-1] > d.volszo.sell[-1]:
        self.buy(d, size=buysize)
        self.logfile.write(str(d.datetime.date(0)) + " BUY " + d._name + " " + str(d[0])+"\n")
