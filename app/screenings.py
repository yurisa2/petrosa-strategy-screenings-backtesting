import logging

from app import datacon


def inside_bar_buy(candles, timeframe, periods=126):

    dat = candles
    
    dat = dat.sort_index(ascending=True)

    if len(dat) < periods:
        logging.info('Error: insufficient data')
        

    close = float(list(dat['Close'])[-1])
    low = float(list(dat['Low'])[-1])
    high = float(list(dat['High'])[-1])

    ema8 = dat["Close"].ewm(span=8, adjust=True, min_periods=7).mean()
    ema80 = dat["Close"].ewm(span=80, adjust=True, min_periods=79).mean()

    ema8 = ema8.iloc[-1]
    ema80 = ema80.iloc[-1]
    
    last_high = dat.High.iloc[-1]
    prior_to_last_high = dat.High.iloc[-2]
    
    last_low = dat.Low.iloc[-1]
    prior_to_last_low = dat.Low.iloc[-2]


    if (close > ema8
            and close > ema80
            and last_high < prior_to_last_high
            and last_low > prior_to_last_low
        ):

        return datacon.screening_output(ticker=dat.ticker.iloc[-1],
                                        timeframe=timeframe,
                                        pet_datetime=dat.index[-1],
                                        entry_value=high,
                                        disruption_value=high,
                                        stop_loss=low,
                                        take_profit=high +
                                        ((high - low) * 2),
                                        direction='UPPER')
    else:
        return {}


def inside_bar_sell(candles, timeframe, periods=126):

    dat = candles
    
    dat = dat.sort_index(ascending=True)

    if len(dat) < periods:
        logging.info('Error: insufficient data')
        

    close = float(list(dat['Close'])[-1])
    low = float(list(dat['Low'])[-1])
    high = float(list(dat['High'])[-1])

    ema8 = dat["Close"].ewm(span=8, adjust=True, min_periods=7).mean()
    ema80 = dat["Close"].ewm(span=80, adjust=True, min_periods=79).mean()

    ema8 = ema8.iloc[-1]
    ema80 = ema80.iloc[-1]
    
    
    if (close < ema8
        and float(close) < float(ema80)
        and high < float(dat.High.iloc[-2])
        and float(low) > float(dat.Low.iloc[-2])
        ):

        return datacon.screening_output(ticker=dat.ticker.iloc[-1],
                                        timeframe=timeframe,
                                        pet_datetime=dat.index[-1],
                                        entry_value=low,
                                        disruption_value=high,
                                        stop_loss=high,
                                        take_profit=low -
                                        ((high - low) * 2),
                                        direction='UPPER')
    else:
        return {}
