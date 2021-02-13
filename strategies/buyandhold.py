import backtrader as bt

class BuyAndHoldAll(bt.Strategy):
  def start(self):
    self.val_start = self.broker.get_cash()

  def nextstart(self):
    for d in self.datas:
      size = int(self.broker.get_cash() / d / len(self.datas))
      self.buy(d, size=size)

class BuyAllThenSell(bt.Strategy):
  def start(self):
    self.val_start = self.broker.get_cash()

  def nextstart(self):
    for d in self.datas:
      size = int(self.broker.get_cash() / d / len(self.datas))
      self.buy(d, size=size)

  def next(self):
    try:
      self.datas[0].datetime.date(2)
    except:
      # it's the 2nd to last day, sell
      for d in self.datas:
        self.close(d)

class BuyAndHoldSPY(bt.Strategy):
  def nextstart(self):
    for d in self.datas:
      if d._name == "SPY":
        size = int(self.broker.get_cash() / d)
        self.buy(d, size=size)