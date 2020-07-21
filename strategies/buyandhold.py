import backtrader as bt

class BuyAndHoldAll(bt.Strategy):
  def start(self):
    self.val_start = self.broker.get_cash()

  def nextstart(self):
    for d in self.datas:
      size = int(self.broker.get_cash() / d / len(self.datas))
      self.buy(d, size=size)

class BuyAndHoldSPY(bt.Strategy):
  def nextstart(self):
    for d in self.datas:
      if d._name == "SPY":
        size = int(self.broker.get_cash() / d)
        self.buy(d, size=size)