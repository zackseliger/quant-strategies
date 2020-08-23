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
        vol_price = btind.SumN(price*self.data.volume, period=self.p.sumlength) / btind.SumN(self.data.volume+1, period=self.p.sumlength)
        r2 = price + self.data.high - self.data.low
        s2 = price - self.data.high + self.data.low

        rslope = r2(0) - r2(-1)
        sslope = s2(0) - s2(-1)
        diff = vol_price(0) - vol_price(-1)

        resistance = btind.MovingAverageWilder(rslope, period=self.p.avglength)
        support = btind.MovingAverageWilder(sslope, period=self.p.avglength)
        difference = btind.MovingAverageWilder(diff, period=self.p.avglength)

        self.lines.final = (resistance+support+difference*5) / 3
        # self.lines.final = difference
        self.lines.zero = bt.LineNum(0)

class ZPP(bt.Indicator):
    lines = ('buy', 'sell')
    params = (('avglength',12),)

    def __init__(self):
        self.price = (self.data.close+self.data.high+self.data.low) / 3
        self.r2 = btind.MovingAverageSimple(self.price*2-self.data.low, period=self.p.avglength)
        self.s2 = btind.MovingAverageSimple(self.price*2-self.data.high, period=self.p.avglength)

    def next(self):
        self.lines.buy[0] = (self.price > self.s2 and self.price[-1] <= self.s2[-1])
        self.lines.sell[0] = (self.price < self.r2 and self.price[-1] >= self.r2[-1])

class ZackOverMA(bt.Indicator):
    lines = ('momentum', 'slope','zero')
    params = (
        ('avglength', 21),
        ('sumlength', 20),
        ('movav', btind.MovAv.Simple)
    )

    def __init__(self):
        ma = self.p.movav(self.data, period=self.p.avglength)
        over = btind.SumN(self.data > ma, period=self.p.sumlength)
        under = btind.SumN(self.data < ma, period=self.p.sumlength)

        self.lines.momentum = (over - under) / self.p.sumlength
        self.lines.slope = self.lines.momentum(0) - self.lines.momentum(-1)
        self.lines.zero = bt.LineNum(0)

class ZackVolumeSignal(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('avgvollength', 12),
        ('period', 12),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        avgvol = btind.ExponentialMovingAverage(self.data.volume, period=self.p.avgvollength)
        priceUp = btind.If(self.data.volume(0)>avgvol(0), btind.If(self.data(0)>self.data(-1), (self.data(0)-self.data(-1))/self.data(0), 0), 0)
        priceDown = btind.If(self.data.volume(0)>avgvol(0), btind.If(self.data(0)<self.data(-1), (self.data(-1)-self.data(0))/self.data(0), 0), 0)
        self.lines.up = self.p.movav(priceUp, period=self.p.period)
        self.lines.down = self.p.movav(priceDown, period=self.p.period)

class ZackPrevHigh(bt.Indicator):
    lines = ('top', 'bot', 'midway')
    params = (
        ('period', 50),
    )
    plotinfo=dict(subplot=False)

    def __init__(self):
        self.lines.top = btind.Highest(self.data, period=self.p.period)
        self.lines.bot = btind.Lowest(self.data, period=self.p.period)
        self.lines.midway = (self.lines.top(0) + self.lines.bot(0)) / 2

class AboveMAAccum(bt.Indicator):
    lines = ('accum', 'slope')
    params = (
        ('avglength', 21),
        ('sumlength', 50)
    )

    def __init__(self):
        ma = btind.MovingAverageSimple(self.data, period=self.p.avglength)
        # self.lines.accum = btind.Accum((self.data - ma) / ma)
        self.lines.accum = btind.SumN((self.data-ma) / ma, period=self.p.sumlength)
        self.lines.slope = self.accum(0) - self.accum(-1)

class BHErgodic(bt.Indicator):
    lines = ('erg', 'signal')
    params = (
        ('rPeriod', 2),
        ('sPeriod', 10),
        ('uPeriod', 5),
        ('triggerPeriod', 3)
    )

    def __init__(self):
        delta = self.data-self.data(-1)
        delta2 = abs(self.data-self.data(-1))

        rma = btind.ExponentialMovingAverage(delta, period=self.p.rPeriod)
        rma2 = btind.ExponentialMovingAverage(delta2, period=self.p.rPeriod)
        sma = btind.ExponentialMovingAverage(rma, period=self.p.sPeriod)
        sma2 = btind.ExponentialMovingAverage(rma2, period=self.p.sPeriod)
        uma = btind.ExponentialMovingAverage(sma, period=self.p.uPeriod)
        uma2 = btind.ExponentialMovingAverage(sma2, period=self.p.uPeriod)

        self.lines.erg = btind.If(uma2 > 0, 100*uma / uma2, 0)
        self.lines.signal = btind.ExponentialMovingAverage(self.lines.erg, period=self.p.triggerPeriod)

class ZackMADiff(bt.Indicator):
    lines = ('res',)
    params = (
        ('period', 12),
    )

    def __init__(self):
        ema = btind.ExponentialMovingAverage(self.data, period=self.p.period)
        sma = btind.MovingAverageSimple(self.data, period=self.p.period)

        self.lines.res = (ema*ema-sma*sma) / (self.data)

class ZackAverageVelocity(bt.Indicator):
    lines = ('vel',)
    params = (
        ('period', 50),
    )

    def __init__(self):
        vel = self.data(0) - self.data(-1)
        self.lines.vel = btind.SumN(vel/self.p.period, period=self.p.period)

class RexOscillator(bt.Indicator):
    lines = ('rex', 'signal')
    params = (
        ('period', 14),
        ('signalPeriod', 14),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        tvb = 3*self.data.close - (self.data.low+self.data.open+self.data.high)
        self.lines.rex = self.p.movav(tvb, period=self.p.period)
        self.lines.signal = self.p.movav(self.lines.rex, period=self.p.signalPeriod)

class AbsoluteStrengthOscillator(bt.Indicator):
    lines = ('bulls', 'bears')
    params = (
        ('lookback', 6),
        ('period', 2),
        ('smoothPeriod', 9),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        smallest = btind.Lowest(self.data, period=self.p.lookback)
        largest = btind.Highest(self.data, period=self.p.lookback)
        bulls = self.data(0) - smallest
        bears = largest - self.data(0)

        avgBulls = self.p.movav(bulls, period=self.p.period)
        avgBears = self.p.movav(bears, period=self.p.period)

        self.lines.bulls = self.p.movav(avgBulls, period=self.p.smoothPeriod)
        self.lines.bears = self.p.movav(avgBears, period=self.p.smoothPeriod)

class SchaffTrend(bt.Indicator):
    lines = ('trend',)
    params = (
        ('fastPeriod', 23),
        ('slowPeriod', 50),
        ('kPeriod', 10),
        ('dPeriod', 3),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        macd = self.p.movav(self.data, period=self.p.fastPeriod) - self.p.movav(self.data, period=self.p.slowPeriod)
        high = btind.Highest(self.data, period=self.p.kPeriod)
        low = btind.Lowest(self.data, period=self.p.kPeriod)
        fastk1= btind.If(high-low > 0, (self.data(0)-low) / (high-low) * 100, 0)
        fastd1 = self.p.movav(fastk1, period=self.p.dPeriod)

        high2 = btind.Highest(fastd1, period=self.p.kPeriod)
        low2 = btind.Lowest(fastd1, period=self.p.kPeriod)
        fastk2 = btind.If(high2-low2 > 0, (fastd1(0)-low2) / (high2-low2) * 100, 0)
        self.lines.trend = self.p.movav(fastk2, period=self.p.dPeriod)