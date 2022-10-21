"""
## Cornell Trading Competition : Derivatives Case Strategy ##

We have provided you with very basic skeleton code for you to implement your
strategy. The strategy will need to have *at least* two functions. One to read
the options data row-by-row, read_data, and one function that trades,
make_trades.

The Strategy is expected to work by rows: It reads the data for the rows of
market data corresponding for 1 minute, with all the different options being
traded at the time, with read_data() and the executes trades with make_trades().

Please do not modify the existing functions signature and make sure to actually
implement them as we will be using them in the grading of your submission.

This file, along with any other files necessary for the strategy to work, will
need to be submitted so make sure to add comments and make your code easy to
read/understand.

Plagarism is strictly banned and will result in your team being withdrawn from
the case. By writing your names below you agree to follow the code of conduct.

Please provide the name & emails of your team members:
    * Student Name (student@email.com)
    * ...

Best of Luck!
"""

import math
from scipy.integrate import quad
import numpy as np
import pandas

class Strategy:

    options = {}
    money = 100000
    data = {}
    portfolio = {}

    """
    read_data:
        Function that is responsible for providing the strategy with market data.

    args:
        row_vals - An array of array of strings that represents the different
        values in the rows of the raw csv file of the same format as the raw csv
        file provided to you. The outer array will correspond to an array of
        rows.

    returns:
        Nothing
    """

    def read_data(self, row_vals):
        self.data.clear()
        for row in row_vals:
            self.data[f"{row[4]}_{row[3]}"] = {"strike": float(row[4]), "expiration": row[3], "date": row[1], "bidSize": int(row[11]), "bid": float(row[12]), "askSize": int(row[13]), "ask": float(row[14]), "underlying ask": float(row[16])}

    """
    make_trades:
        Function that tells the exchange whether, and at what quantity, the
        strategy wants to buy or sell, go long or short, the option.

    args:
        None

    returns:
        An array of triples (str(strike_expiry date), sell, buy) where sell, buy
        are float values that give how much quantity of contract options you
        want to sell and buy at bid & ask prices respectively and the strike
        price and expiry date to differentiate the option. Strike price is a
        numeric value and expiry date is a string and of the same format as in
        the raw csv file. Sell & buy may not be higher than ask & bid size at
        the given time. The value should be 0 for buy or sell if you want no
        activity on that side.

        You can buy/sell underlying stock by the same as above but rather than 
        the first element be str(strike)+str(expiry date) we have the word
        'underlying'
    """

    def expectedMove(self, spot, volatility, ttm):
        return spot * volatility * ttm**0.5

    def impliedVolatility(self, spot, strike, interest, time, actual):
        minCost = 0
        minV = 0
        for v in range(5, 105, 5):
            v = v/100
            cost = actual - self.blackScholes(spot, strike, interest, v, time)
            if (v == 5):
                minCost = cost
                minV = v
            else:
                if cost < minCost:
                    minCost = cost
                    minV = v
        return minV

    def blackScholes(self, spot, strike, interest, volatility, time):
        d1 = self.d1(spot, strike, interest, volatility, time)
        return self.cdf(d1) * strike - self.cdf(self.d2(volatility, time, d1)) * strike * 2.78**(-interest * time)

    def cdf(self, d):
        def integrand(x):
            return np.e**(-0.5*(x**2))
        
        stuff = 1/((2*3.14156)**0.5)
        return stuff * quad(integrand, np.NINF, d)[0]
    
    def d1(self, spot, strike, interest, volatility, time):
        if time == 0:
            time = 0.002
        return (math.log(spot/strike)/math.log(2.71828182845904) + (interest + (volatility**2)/2)*time)/(volatility*time**0.5)

    def d2(self, volatility, time, d1):
        return d1 - volatility * time**0.5

    def make_trades(self):
        trades = []
        for key, value in self.data.items():
            date = value.get("date")
            expiration = value.get("expiration")
            strike = value.get("strike")
            uAsk = value.get("underlying ask")

            ttm = (int(expiration[0:4]) - int(date[0:4])) + (int(expiration[5:7]) - int(date[5:7]))/12 + (int(expiration[8:10]) - int(date[8:10]))/365
            volatility = self.impliedVolatility(uAsk, strike, 0.025, ttm, value.get("ask"))

            expectedMove = self.expectedMove(uAsk, volatility, ttm)
            # if expectedMove + uAsk > 2*strike:
            if value.get("bidSize") > value.get("askSize"):
                amount = 1.1**(expectedMove + uAsk - strike)
                amount = min(amount, value.get("askSize"), self.money/value.get("ask"))
                trades.append((key, 0, amount))
                if key not in self.portfolio:
                    self.portfolio[key] = amount
                else:
                    self.portfolio[key] += amount
                self.money -= amount * value.get("ask")
            
            else: 
                if key in self.portfolio:
                    amount = 1.1**(expectedMove + uAsk - strike)
                    amount = min(amount, value.get("bidSize"), self.portfolio[key])
                    trades.append((key, amount, 0))
                    self.portfolio[key] -= amount
                    self.money += amount * value.get("bid")
        return trades

        # spot, strike, time, cost = self.read_data()
        # volatiltiy = self.impliedVolatility()
