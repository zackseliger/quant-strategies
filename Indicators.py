import backtrader as bt
import backtrader.indicators as btind
import backtrader.functions as btfunc

class SentimentZoneOscillator(bt.Indicator):
    lines = ('szo',)
    params = (('length',14),)

    def __init__(self):
        price_diff = self.data - self.data(-1)
        sign = (price_diff>0)*2-1
        sign = 100 * sign/self.params.length
        self.lines.szo = btind.TripleExponentialMovingAverage(sign, period=self.params.length)

class VolumeMovingAverage(bt.Indicator):
    lines = ('movav',)
    params = (('period', 21),)

    plotinfo = dict(
        subplot=False
    )

    def __init__(self):
        price = (self.data.close+self.data.high+self.data.low) / 3
        vol_sum = btind.SumN(self.data.volume, period=self.p.period)
        self.lines.movav = btind.SumN(price*self.data.volume, period=self.p.period) / vol_sum

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

class ZackOverMA2(bt.Indicator):
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

        self.lines.momentum = btind.SumN((self.data - ma) / self.data, period=self.p.sumlength)
        self.lines.slope = self.lines.momentum(0) - self.lines.momentum(-1)
        self.lines.zero = bt.LineNum(0)

class ZackVolumeSignalOld(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('volperiod', 12),
        ('period', 12),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        avgvol = btind.ExponentialMovingAverage(self.data.volume, period=self.p.volperiod)
        priceUp = btind.If(self.data.volume(0)>avgvol(0), btind.If(self.data(0)>self.data(-1), (self.data(0)-self.data(-1))/self.data(0), 0), 0)
        priceDown = btind.If(self.data.volume(0)>avgvol(0), btind.If(self.data(0)<self.data(-1), (self.data(-1)-self.data(0))/self.data(0), 0), 0)
        self.lines.up = self.p.movav(priceUp, period=self.p.period)
        self.lines.down = self.p.movav(priceDown, period=self.p.period)

class ZackVolumeSignal(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('volperiod', 12),
        ('period', 12),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        avgvol = btind.ExponentialMovingAverage(self.data.volume, period=self.p.volperiod)
        stdev = btind.StdDev(self.data.volume, period=self.p.period-1)
        priceUp = btind.If(self.data.volume(0)>avgvol(0)+stdev(-1), btind.If(self.data(0)>self.data(-1), (self.data(0)-self.data(-1))/self.data(0), 0), 0)
        priceDown = btind.If(self.data.volume(0)>avgvol(0)+stdev(-1), btind.If(self.data(0)<self.data(-1), (self.data(-1)-self.data(0))/self.data(0), 0), 0)
        self.lines.up = self.p.movav(priceUp, period=self.p.period)
        self.lines.down = self.p.movav(priceDown, period=self.p.period)

class ZackVolumeSignalStdDev(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('period', 12),
        ('movav', btind.MovAv.Exponential),
        ('smoothPeriod', 3)
    )

    def __init__(self):
        stdev = btind.StdDev(self.data.volume, period=self.p.period)
        price = self.data.close

        priceUp = btind.If(stdev(0)>stdev(-1), btind.If(price(0)>price(-1), (price(0)-price(-1))/price(0), 0), 0)
        priceDown = btind.If(stdev(0)>stdev(-1), btind.If(price(0)<price(-1), (price(-1)-price(0))/price(0), 0), 0)
        upSmoothed = self.p.movav(priceUp, period=self.p.period)
        downSmoothed = self.p.movav(priceDown, period=self.p.period)
        self.lines.up = self.p.movav(upSmoothed, period=self.p.smoothPeriod)
        self.lines.down = self.p.movav(downSmoothed, period=self.p.smoothPeriod)

class MT5Accelerator(bt.Indicator):
    lines = ('acc',)
    params = (
        ('fastPeriod', 5),
        ('slowPeriod', 34),
        ('lookback', 5),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        fastMA = self.p.movav(self.data, period=self.p.fastPeriod)
        slowMA = self.p.movav(self.data, period=self.p.slowPeriod)
        diff = fastMA - slowMA
        diffSum = btind.SumN(diff, period=self.p.lookback)
        self.lines.acc = diff - diffSum/self.p.lookback

class ZackMinMax(bt.Indicator):
    lines = ('mid', 'top', 'bot')
    params = (
        ('period', 20),
    )
    plotinfo=dict(subplot=False)

    def __init__(self):
        self.lines.top = btind.Highest(self.data.high, period=self.p.period)
        self.lines.bot = btind.Lowest(self.data.low, period=self.p.period)
        self.lines.mid = (self.lines.top(0) + self.lines.bot(0)) / 2

class MinMaxPercentage(bt.Indicator):
    lines = ('percent',)
    params = (
        ('period', 20),
    )

    def __init__(self):
        minmax = ZackMinMax(self.data, period=self.p.period)
        self.lines.percent = (self.data - minmax.bot) / (minmax.top - minmax.bot) * 100

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
        ('triggerPeriod', 3),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        delta = self.data-self.data(-1)
        delta2 = abs(self.data-self.data(-1))

        rma = self.p.movav(delta, period=self.p.rPeriod)
        rma2 = self.p.movav(delta2, period=self.p.rPeriod)
        sma = self.p.movav(rma, period=self.p.sPeriod)
        sma2 = self.p.movav(rma2, period=self.p.sPeriod)
        uma = self.p.movav(sma, period=self.p.uPeriod)
        uma2 = self.p.movav(sma2, period=self.p.uPeriod)

        self.lines.erg = btind.If(uma2 > 0, 100*uma / uma2, 0)
        self.lines.signal = self.p.movav(self.lines.erg, period=self.p.triggerPeriod)

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
        highest = btind.Highest(self.data, period=self.p.lookback)
        bulls = (self.data(0) - smallest) / self.data(0)
        bears = (highest - self.data(0)) / self.data(0)

        avgBulls = self.p.movav(bulls, period=self.p.period)
        avgBears = self.p.movav(bears, period=self.p.period)

        self.lines.bulls = self.p.movav(avgBulls, period=self.p.smoothPeriod)
        self.lines.bears = self.p.movav(avgBears, period=self.p.smoothPeriod)

class Vortex(bt.Indicator):
    lines = ('VIU', 'VID')
    params = (
        ('period', 14),
    )

    def __init__(self):
        viu = btind.SumN(abs(self.data.high - self.data.low(-1)), period=self.p.period)
        vid = btind.SumN(abs(self.data.low - self.data.high(-1)), period=self.p.period)
        str = btind.SumN(btind.AverageTrueRange(self.data, period=1), period=self.p.period)
        self.lines.VIU = viu / str
        self.lines.VID = vid / str

# fixed-length moving average
class SWMA(bt.Indicator):
    lines = ('ma',)

    def __init__(self):
        self.lines.ma = self.data(0)*1/6 + self.data(-1)*2/6 + self.data(-2)*2/6 + self.data(-3)*1/6

class RVI(bt.Indicator):
    lines = ('rvi', 'sig')
    params = (
        ('period', 10),
    )

    def __init__(self):
        self.lines.rvi = btind.SumN(SWMA(self.data.close-self.data.open), period=self.p.period) / btind.SumN(SWMA(self.data.high-self.data.low), period=self.p.period)
        self.lines.sig = SWMA(self.lines.rvi)

class WIMA(bt.Indicator):
    lines = ('ma',)
    params = (
        ('period', 14),
    )

    # def __init__(self):
    #     self.lines.ma = (self.data + self.lines.ma(-1) * (self.p.period-1)) / self.p.period

    def nextstart(self):
        self.lines.ma[0] = sum(self.data.get(size=self.p.period)) / self.p.period

    def next(self):
        self.lines.ma[0] = (self.data + self.lines.ma[-1] * (self.p.period-1)) / self.p.period

class QQE(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('rsi_period', 8),
        ('rsi_smoothing_period', 1),
        ('atr_period', 14),
        ('fast_mult', 3),
        ('slow_mult', 4.236)
    )

    def __init__(self):
        rsi_ema = btind.MovAv.Exponential(btind.RSI(self.data, period=self.p.rsi_period), period=self.p.rsi_smoothing_period)

        TH = btind.If(rsi_ema(-1) > rsi_ema, rsi_ema(-1), rsi_ema)
        TL = btind.IF(rsi_ema(-1) < rsi_ema, rsi_ema(-1), rsi_ema)
        TR = TH - TL

        atr_rsi = WIMA(TR, period=self.p.atr_period) # should be WIMA
        smoothed_atr_rsi = WIMA(atr_rsi, period=self.p.atr_period) # should be WIMA

        delta_fast_atr_rsi = smoothed_atr_rsi * self.p.fast_mult

        newshortband = rsi_ema + delta_fast_atr_rsi
        newlongband = rsi_ema - delta_fast_atr_rsi

        # longband = btind.If(rsi_ema(-1) > longband) # can't reasonably continue...

class HLCTrend(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('close_period', 5),
        ('low_period', 13),
        ('high_period', 34),
        ('movav', btind.MovAv.Exponential),
    )

    def __init__(self):
        emac = self.p.movav(self.data.close, period=self.p.close_period)
        emal = self.p.movav(self.data.low, period=self.p.low_period)
        emah = self.p.movav(self.data.high, period=self.p.high_period)

        self.lines.up = emac - emah
        self.lines.down = emal - emac

class ZackLargestCandle(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('lookback', 10),
        ('period', 10),
        ('smoothingPeriod', 2),
        ('movav', btind.MovAv.Exponential),
    )

    def __init__(self):
        upCandles = btind.If(self.data.close > self.data.open, (self.data.close - self.data.open) / self.data.open, 0)
        downCandles = btind.If(self.data.close < self.data.open, (self.data.open - self.data.close) / self.data.open, 0)

        hUpCandle = btind.Highest(upCandles, period=self.p.lookback)
        hDownCandle = btind.Highest(downCandles, period=self.p.lookback)

        up1 = self.p.movav(upCandles, period=self.p.period) / btind.If(hDownCandle == 0, 0.01, hDownCandle)
        down1 = self.p.movav(downCandles, period=self.p.period) / btind.If(hUpCandle == 0, 0.01, hUpCandle)

        self.lines.up = self.p.movav(up1, period=self.p.smoothingPeriod)
        self.lines.down = self.p.movav(down1, period=self.p.smoothingPeriod)

class DidiIndex(bt.Indicator):
    lines = ('up', 'down')
    params = (
        ('short', 3),
        ('mid', 8),
        ('long', 30),
        ('movav', btind.MovAv.Exponential),
    )

    def __init__(self):
        self.lines.up = self.p.movav(self.data.close, period=self.p.short) - self.p.movav(self.data.close, period=self.p.mid)
        self.lines.down = self.p.movav(self.data.close, period=self.p.long) - self.p.movav(self.data.close, period=self.p.mid)

class MADiff(bt.Indicator):
    lines = ('sig',)
    params = (
        ('short', 3),
        ('long', 8),
        ('movav', btind.MovAv.Exponential),
    )

    def __init__(self):
        self.lines.sig = self.p.movav(self.data.close, period=self.p.short) - self.p.movav(self.data.close, period=self.p.long)

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

class Effort(bt.Indicator):
    lines = ('effort',)
    params = (
        ('period', 14),
    )

    def __init__(self):
        price = btind.MovingAverageSimple(self.data, period=self.p.period)
        roc = 100 * (price(0) / price(-self.p.period)-1)
        maxvol = btind.Highest(self.data.volume, period=self.p.period)
        self.lines.effort = roc / maxvol

class VolumeWeightedAveragePrice(bt.Indicator):
    plotinfo = dict(subplot=False)
    params = (('period', 30), )

    alias = ('VWAP', 'VolumeWeightedAveragePrice',)
    lines = ('VWAP',)
    plotlines = dict(VWAP=dict(alpha=0.50, linestyle='-.', linewidth=2.0))

    def __init__(self):
        # Before super to ensure mixins (right-hand side in subclassing)
        # can see the assignment operation and operate on the line
        cumvol = bt.ind.SumN(self.data.volume, period = self.p.period)
        typprice = ((self.data.close + self.data.high + self.data.low)/3) * self.data.volume
        cumtypprice = bt.ind.SumN(typprice, period=self.p.period)
        self.lines[0] = cumtypprice / cumvol

        super(VolumeWeightedAveragePrice, self).__init__()


class VolatilitySwitch(bt.Indicator):
    lines = ('switch', 'vol')
    params = (
        ('period', 21),
        ('smoothPeriod', 2)
    )

    def __init__(self):
        smoothFactor = btind.MovingAverageSimple(self.data, period=self.p.smoothPeriod)
        dailyReturn = (self.data(0)-self.data(-1)) / smoothFactor
        self.lines.vol = btind.StandardDeviation(dailyReturn, period=self.p.period)

    def next(self):
        res = 0
        for i in range(self.p.period):
            if self.lines.vol[0] >= self.lines.vol[-i]:
                res += 1

        self.lines.switch[0] = res / self.p.period

class VolatilitySwitchMod(bt.Indicator):
    lines = ('switch', 'vol')
    params = (
        ('period', 21),
        ('dailyperiod', 10),
        ('movav', btind.MovAv.Smoothed)
    )

    def __init__(self):
        dailyReturn = (self.data(0)-self.data(-1)) / ((self.data(0)+self.data(-1)) / 2)
        ma = self.p.movav(dailyReturn, period=self.p.dailyperiod)
        self.lines.vol = btind.StandardDeviation(ma, period=self.p.period)

    def next(self):
        res = 0
        for i in range(self.p.period):
            if self.lines.vol[0] >= self.lines.vol[-i]:
                res += 1

        self.lines.switch[0] = res / self.p.period

class PercentChange(bt.Indicator):
    lines = ('change',)
    params = (
        ('period', 14),
    )

    def __init__(self):
        self.lines.change = 100 * (self.data(0) / self.data(-self.p.period) - 1)

class ChaikinVolatility(bt.Indicator):
    lines = ('cv',)
    params = (
        ('rocperiod', 10),
        ('period', 10)
    )

    def __init__(self):
        diff = self.data.high(0) - self.data.low(0)
        avg = btind.MovingAverageSimple(diff, period=self.p.period)

        self.lines.cv = btind.If(avg(-self.p.rocperiod) == 0, 100, (avg(0) - avg(-self.p.rocperiod)) / avg(-self.p.rocperiod) * 100)

class HeikenAshiDiff(bt.Indicator):
    lines = ('diff','ha_open','ha_close')
    params = (
        ('period', 5),
    )
    _nextforce = True

    def __init__(self):
        self.l.ha_close = ha_close = (self.data.open + self.data.close + self.data.high + self.data.low) / 4.0
        self.l.ha_open = ha_open = (self.l.ha_open(-1) + ha_close(-1)) / 2.0
        diff = ha_close(0) - ha_open(0)
        self.lines.diff = btind.MovingAverageSimple(diff, period=5)

    def prenext(self):
        # seed recursive value
        self.lines.ha_open[0] = (self.data.open[0] + self.data.close[0]) / 2.0

class DMIStoch(bt.Indicator):
    lines = ('stoch',)
    params = (
        ('period', 10),
        ('sumperiod', 3)
    )

    def __init__(self):
        dmi = btind.DirectionalMovementIndex(self.data, period=self.p.period)
        osc = dmi.plusDI - dmi.minusDI
        hh = btind.Highest(osc, period=self.p.sumperiod)
        ll = btind.Lowest(osc, period=self.p.sumperiod)

        self.lines.stoch = btind.SumN(osc - ll, period=self.p.sumperiod) / btind.SumN(hh - ll, period=self.p.sumperiod) * 100

class ZackVolatility(bt.Indicator):
    lines = ('vol', 'ma')
    params = (
        ('period', 21),
        ('movav', btind.MovAv.Exponential)
    )

    def __init__(self):
        self.lines.vol = btind.StandardDeviation(self.data, period=self.p.period)
        self.lines.ma = self.p.movav(self.lines.vol, period=self.p.period*2)

class MoneyFlowIndex(bt.Indicator):
    lines = ('mfi',)
    params = (
        ('period', 14),
        ('movav', btind.MovAv.Smoothed)
    )

    def __init__(self):
        price = (self.data.high + self.data.low + self.data.close) / 3
        pricema = self.p.movav(price, period=self.p.period)
        posmf = btind.If(price(0) > price(-1), price*self.data.volume, 0)
        negmf = btind.If(price(0) < price(-1), price*self.data.volume, 0)
        mfi = bt.DivByZero(btind.SumN(posmf, period=self.p.period), btind.SumN(negmf, period=self.p.period))
        self.lines.mfi = 100 - 100 / (1 + mfi)

class RelativeStrengthIndex(bt.Indicator):
    lines = ('rsi',)
    params = (
        ('period', 14),
        ('movav', btind.MovAv.Smoothed)
    )

    def __init__(self):
        price = (self.data.high + self.data.low + self.data.close) / 3
        pricema = self.p.movav(price, period=self.p.period)
        posrs = btind.If(price(0) > price(-1), price, 0)
        negrs = btind.If(price(0) < price(-1), price, 0)
        rsi = bt.DivByZero(btind.SumN(posrs, period=self.p.period), btind.SumN(negrs, period=self.p.period))
        self.lines.rsi = 100 - 100 / (1 + rsi)

class PolarizedFractalEfficiency(bt.Indicator):
    lines = ('pfe',)
    params = (
        ('slowPeriod', 10),
        ('fastPeriod', 1),
        ('scaleFactor', 1),
        ('period', 5),
        ('movav', btind.MovAv.Smoothed)
    )

    def __init__(self):
        longRoc = 100 * (self.data(0) / self.data(-self.p.slowPeriod)-1)
        shortRoc = 100 * (self.data(0) / self.data(-self.p.fastPeriod)-1)
        Z = btind.DivByZero(pow(longRoc(0) * longRoc(0) + 100, 0.5), pow(shortRoc(0) * shortRoc(0), 0.5) + self.p.scaleFactor)
        B = btind.If(self.data(0) > self.data(-self.p.slowPeriod), 100*Z(0), -100*Z(0))
        self.lines.pfe = self.p.movav(B, period=self.p.period)

class Juice(bt.Indicator):
    lines = ('juice',)
    params = (
        ('fastPeriod', 6),
        ('slowPeriod', 14),
        ('period', 5),
        ('movav', btind.MovAv.Smoothed),
        ('volatility', 0.02)
    )

    def __init__(self):
        val = (self.p.movav(self.data, period=self.p.fastPeriod) - self.p.movav(self.data, period=self.p.slowPeriod)) / self.data(0)
        avg = self.p.movav(val, period=self.p.period)
        self.lines.juice = abs(avg) - self.p.volatility

class VolumeOsc(bt.Indicator):
    lines = ('osc',)
    params = (
        ('fastPeriod', 14),
        ('slowPeriod', 28),
        ('movav', btind.MovAv.Simple),
    )

    def __init__(self):
        fast = self.p.movav(self.data.volume, period=self.p.fastPeriod)
        slow = self.p.movav(self.data.volume, period=self.p.slowPeriod)
        self.lines.osc = (fast - slow) / slow

class AroonDown(bt.Indicator):
    lines = ('down',)
    params = (
        ('period', 14),
    )

    def __init__(self):
        lidx = btind.FindFirstIndexLowest(self.data.low, period=self.p.period)
        self.lines.down = (self.p.period - 1 - lidx) * 100 / (self.p.period - 1)#(100.0 / self.p.period) * (self.p.period - llidx)

class MarketMeannessIndicator(bt.Indicator):
    lines = ('mmi',)
    params = (
        ('period', 200),
        ('movav', btind.MovAv.Hull)
    )

    def __init__(self):
        m = (btind.Highest(self.data.high, period=self.p.period)+btind.Lowest(self.data.low, period=self.p.period)) / 2
        nhh = btind.If(self.data>m, btind.If(self.data>self.data(-1), 1, 0), 0)
        nll = btind.If(self.data<m, btind.If(self.data<self.data(-1), 1, 0), 0)
        nh = btind.SumN(nhh, period=self.p.period)
        nl = btind.SumN(nll, period=self.p.period)
        mmi = 100*(nl+nh)/(self.p.period-1)

        self.lines.mmi = self.p.movav(mmi, period=self.p.period)

class VPN(bt.Indicator):
    lines = ('up','down')
    params = (
        ('period', 20),
        ('movav', btind.MovAv.Exponential),
    )

    def __init__(self):
        atr = btind.AverageTrueRange(self.data, period=self.p.period)
        price = (self.data.high+self.data.low+self.data.close) / 3
        up = btind.If(price(0) > price(-1)+atr*0.1, self.data.volume(0), 0)
        down = btind.If(price(0) < price(-1)-atr*0.1, self.data.volume(0), 0)

        totalVol = btind.SumN(self.data.volume, period=self.p.period)

        self.lines.up = self.p.movav(up, period=self.p.period) / totalVol
        self.lines.down = self.p.movav(down, period=self.p.period) / totalVol

class ATRP(bt.Indicator):
    lines = ('diff',)
    params = (
        ('slowperiod', 20),
        ('fastperiod', 5),
        ('movav', btind.MovAv.Smoothed),
    )

    def __init__(self):
        slow = self.p.movav(btind.TrueRange(self.data)/self.data.close, period=self.p.slowperiod)
        fast = self.p.movav(btind.TrueRange(self.data)/self.data.close, period=self.p.fastperiod)
        self.lines.diff = fast - slow