import os
import json
import datetime
import time
import logging 
import numpy as np
import pymongo
from backtesting import Strategy, Backtest
from app import get_data
from backtesting.lib import plot_heatmaps
import newrelic.agent
import datetime
import random
from app import constants
import requests

class bb_backtest(Strategy):
    buy_sl=None
    def init(self) -> None:
        pass


    @newrelic.agent.background_task()
    def next(self):

        try:
            if(self.data.index[-1] in self.main_data.index):
                work_data = self.main_data.loc[self.main_data.index
                                               <= self.data.index[-1]]
                # print('work_data', work_data.index[-1])
                # print('main_Data', self.data.index[-1

                # print(self.data.index[-1])
                
                post_data = work_data.sort_values(
                    by='datetime', ascending=False)
                post_data = post_data[:201]
                
                inside_bar_value = requests.post(
                    f"http://localhost:8090/inside_bar_buy/{self.timeframe}", 
                    data=post_data)
                
                print("oi " * 100)
                print("im inside")
                print(inside_bar_value)

            else:
                return True

        except Exception as e:
            pass


@newrelic.agent.background_task()
def run_backtest(symbol, test_period, strategy_name):

    data = get_data.get_data(symbol, 'm5', limit=2000)
    main_data = get_data.get_data(symbol, test_period, limit=220)

    if(len(data) == 0 or len(main_data) == 0):
        return False

    strat = bb_backtest
    strat.main_data = main_data
    
    strat.timeframe = test_period

    bt = Backtest(
                    data,
                    strat,
                    commission=0,
                    exclusive_orders=True,
                    cash=100000)

    stats, heatmap = bt.optimize(
        buy_sl=[1],

        maximize='SQN',
        # minimize='Max. Drawdown [%]',
        max_tries=200,
        random_state=0,
        return_heatmap=True)
    # plot_heatmaps(heatmap, agg='mean')

    client = pymongo.MongoClient(
                os.getenv(
                    'MONGO_URI', 'mongodb://root:QnjfRW7nl6@localhost:27017'),
                readPreference='secondaryPreferred',
                appname='petrosa-strategy-screenings-backtesting'
                                        )

    heatmap = heatmap.dropna().sort_values().iloc[-10:]
    new_hm = {}
    new_hm['heatmap'] = heatmap
    new_hm['insert_timestamp'] = datetime.datetime.now()
    new_hm['strategy'] = strategy_name
    new_hm['period'] = test_period
    new_hm['symbol'] = symbol

    doc = json.dumps({**stats._strategy._params,
                     ** stats, **new_hm}, default=str)
    doc = json.loads(doc)

    client.petrosa_crypto['backtest_results'].update_one(
                                            {"strategy": strategy_name,
                                             "symbol": symbol,
                                             "period": test_period
                                             }, {"$set": doc}, upsert=True)


@newrelic.agent.background_task()
def continuous_run() -> None:
    client = pymongo.MongoClient(
                os.getenv(
                    'MONGO_URI', 'mongodb://root:QnjfRW7nl6@localhost:27017'),
                readPreference='secondaryPreferred',
                appname='petrosa-strategy-screenings-backtesting'
                                        )
    try:
        params = client.petrosa_crypto['backtest_controller'].find(
            {"status": 0, "strategy": {"$in": constants.screenings}})
        params = list(params)

        if len(params) == 0:
            params = client.petrosa_crypto['backtest_controller'].find(
                {"status": 1, "strategy": {"$in": constants.screenings}})
            params = list(params)

 
        if len(params) == 0:
            params = client.petrosa_crypto['backtest_controller'].find(
                {"strategy": {"$in": constants.screenings}})
            params = list(params)
        
        # params = params[random.randint(0, len(params))]
        params = params[0]



        client.petrosa_crypto['backtest_controller'].update_one(
            params, {"$set": {"status": 1}})

        logging.warning('Running backtest for screenings on: ' + 
                        str(params))
        bt_ret = run_backtest(params['symbol'], params['period'], params['strategy'])

        if bt_ret is False:
            status = -1
        else:
            status = 2

        client.petrosa_crypto['backtest_controller'].update_one(
            {"_id": params['_id']}, {"$set": {"status": status}})

        logging.warning('Finished ' + str(params))

        pass
    except Exception as e:
        logging.error(e)
        time.sleep(10)

# bt.run()
