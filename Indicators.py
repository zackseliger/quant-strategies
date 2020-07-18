import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc

class SentimentZoneOscillator(bt.Indicator):
    lines = ('szo',)
    params = (('length',14),)

    def __init__(self):
        # price = getattr(self.data, self.params.price)
        price_diff = self.data - self.data(-1)
        sign = (price_diff>0)*2-1
        sign = 100 * sign/self.params.length
        self.lines.szo = btind.TripleExponentialMovingAverage(sign, period=self.params.length)

class VolSZO(bt.Indicator):
    lines = ('szo', 'buy', 'sell',)
    params = (('szolength',2), ('sumlength',12), ('signal_percent',95))

    def __init__(self):
        price = (self.data.close+self.data.high+self.data.low) / 3
        vol_sum = btind.SumN(self.data.volume, period=self.params.sumlength)
        vol_weighted_price = btind.SumN(price*self.data.volume, period=self.params.sumlength)

        self.lines.szo = SentimentZoneOscillator(vol_weighted_price/vol_sum, length=self.params.szolength)
        self.lines.buy = btfunc.Max(self.p.signal_percent/self.params.szolength,0)
        self.lines.sell = btfunc.Min(-self.p.signal_percent/self.params.szolength,0)

class ZackPivotPoints(bt.Indicator):
    lines = ('final', 'zero')
    params = (('avglength',5), ('sumlength',5))

    def __init__(self):
        price = (self.data.close+self.data.high+self.data.low) / 3
        vol_price = btind.SumN(price*self.data.volume, period=self.p.sumlength) / btind.SumN(self.data.volume, period=self.p.sumlength)
        r2 = price + self.data.high - self.data.low
        s2 = price - self.data.high + self.data.low

        rslope = r2(0) - r2(-1)
        sslope = s2(0) - s2(-1)
        diff = vol_price(0) - vol_price(-1)

        resistance = btind.MovingAverageWilder(rslope, period=self.p.avglength)
        support = btind.MovingAverageWilder(sslope, period=self.p.avglength)
        difference = btind.MovingAverageWilder(diff, period=self.p.avglength)

        self.lines.final = (resistance+support+difference) / 3
        # self.lines.final = difference
        self.lines.zero = bt.LineNum(0)

class ZackOverMA(bt.Indicator):
    lines = ('momentum', 'slope','zero')
    params = (
        ('avglength', 21),
        ('sumlength', 20)
    )

    def __init__(self):
        ma = btind.MovingAverageSimple(self.data, period=self.p.avglength)
        over = btind.SumN(self.data > ma, period=self.p.sumlength)
        under = btind.SumN(self.data < ma, period=self.p.sumlength)

        self.lines.momentum = (over - under) / self.p.sumlength
        self.lines.slope = self.lines.momentum(0) - self.lines.momentum(-1)
        self.lines.zero = bt.LineNum(0)

class AboveMAAccum(bt.Indicator):
    lines = ('accum', 'slope')
    params = (
        ('avglength', 21),
    )

    def __init__(self):
        ma = btind.MovingAverageSimple(self.data, period=self.p.avglength)
        self.lines.accum = btind.Accum((self.data - ma) / ma)
        self.lines.slope = self.accum(0) - self.accum(-1)