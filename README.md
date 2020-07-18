# Quant Strategies
This package contains some quant indicators and strategies.
Custom indicators are in Indicators.py and Strategies are found in Strategies.py.

## Writing Indicators and Strategies
Indicators and strategies go in their respective files. tester.py should be used to see the graph of a strategy and make sure it works for one stock before adding more.

If you're making an indicator and wouldn't like to run a strategy, you should comment out the final lines in tester.py that calculate the sharpe ratio and RoMaD to avoid a crash.

Most strategies currently written output all trades to log.txt.

## Dataset
The main dataset used is 1/1/2016-1/1/2020 OCHLV data from Yahoo Finance for several outperforming stocks (GOOG, AMZN, MSFT) and many stocks that were delisted from the S&P 500 and underperformed afterwords.

For the backtest in main.py, Roughly 70% of tickers are chosen randomly and fed to the strategy in a random order.

## Measuring Strategy Quality
When backtesting a strategy, the Sharpe ratio and [RoMaD](https://www.investopedia.com/terms/r/return-over-maximum-drawdown-romad.asp) are used. The numbers to beat are 0.94 and 0.65 respectively, which are the numbers for buying and holding the S&P 500 during 2016-2020.

## Requirements
Backtrader >= 1.9.76.123