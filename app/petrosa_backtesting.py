from urllib.request import Request, urlopen
import datetime
import json
import logging
import time

import newrelic.agent
import numpy as np
from backtesting import Backtest, Strategy

from app import datacon

import aiohttp
import requests
import json


def request_setup(post_data):
    from urllib.parse import urlencode


    # inside_bar_value = requests.post(
    #     # f"http://localhost:8090/inside_bar_buy/{self.timeframe}",
    #     f"http://localhost:8090/inside_bar_buy/m15",
    #     data=post_data)
    
    url = 'http://localhost:8090/inside_bar_buy/m15'  # Set destination URL here

    data = post_data     # Set POST fields here
    # data = json.dumps(post_data)     # Set POST fields here
    req = Request(url, urlencode(data).encode())
    inside_bar_value = urlopen(req).read().decode()

    print(inside_bar_value)

    return inside_bar_value

class bb_backtest(Strategy):
    buy_sl = None
    buy_tp = None
    sell_sl = None
    sell_tp = None
    buy_threshold = None
    sell_threshold = None
    sell_enabled = True
    buy_enabled = True

    def init(self) -> None:
        pass

    @newrelic.agent.background_task()
    def next(self):

        if (
            self.buy_sl is None
            or self.buy_tp is None
            or self.sell_sl is None
            or self.sell_tp is None
            or self.buy_threshold is None
            or self.sell_threshold is None
            or self.sell_enabled is None
            or self.buy_enabled is None
        ):
            return True

        if (self.buy_sl > self.buy_tp
                or self.sell_sl > self.sell_tp):  # should be done via constraints
            return True

        try:
            if (self.data.index[-1] in self.main_data.index):
                work_data = self.main_data.loc[self.main_data.index
                                               <= self.data.index[-1]]

                post_data = work_data.sort_values(
                    by='datetime', ascending=False)
                post_data = post_data[:201]

                print('oi Im before')

                # async with aiohttp.ClientSession() as session:
                #     async with session.get('http://httpbin.org/get') as resp:
                #         print(resp.status)
                #         print(await resp.text())

                # print(request_setup(post_data))

                print("oi " * 100)
                print("im inside")


            else:
                return True

        except Exception as e:
            pass


@newrelic.agent.background_task()
def run_backtest(symbol, test_period):

    data = datacon.get_data(symbol, 'm5', limit=1000)
    main_data = datacon.get_data(symbol, test_period, limit=200)

    if (len(data) == 0 or len(main_data) == 0):
        return False

    strat = bb_backtest
    strat.main_data = main_data

    bt = Backtest(
        data,
        strat,
        commission=0,
        exclusive_orders=True,
        cash=100000)

    stats = bt.optimize(
        buy_sl=list(np.arange(1, 3, 0.5)),
        buy_tp=list(np.arange(1, 4, 0.5)),
        sell_sl=list(np.arange(1, 3, 0.5)),
        sell_tp=list(np.arange(1, 4, 0.5)),
        buy_threshold=list(np.arange(1, 3, 0.5)),
        sell_threshold=list(np.arange(1, 3, 0.5)),
        maximize='SQN',
        # minimize='Max. Drawdown [%]',
        max_tries=200,
        random_state=0,
        return_heatmap=False)

    new_hm = {}
    new_hm['insert_timestamp'] = datetime.datetime.now()
    new_hm['strategy'] = 'simple_gap_finder'
    new_hm['period'] = test_period
    new_hm['symbol'] = symbol

    doc = json.dumps({**stats._strategy._params,
                     **stats, **new_hm}, default=str)
    doc = json.loads(doc)

    datacon.post_results(symbol, test_period, doc)


@newrelic.agent.background_task()
def continuous_run():
    try:
        params = datacon.find_params()

        logging.warning('Running backtest for simple_gap_finder on: ' +
                        str(params))
        bt_ret = run_backtest(params['symbol'], params['period'])

        if bt_ret is False:
            datacon.update_status(params=params, status=-1)
        else:
            datacon.update_status(params=params, status=2)
        logging.warning('Finished ' + str(params))

    except Exception as e:
        logging.error(e)
        time.sleep(10)

    return True
