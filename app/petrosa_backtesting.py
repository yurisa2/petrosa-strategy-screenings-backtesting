import datetime
import json
import logging
import time

import newrelic.agent
from backtesting import Backtest, Strategy

from app import datacon
from app import screenings

import json


class bb_backtest(Strategy):
    # buy_sl = None
    # buy_tp = None
    
    def init(self) -> None:
        pass

    def next(self):
        
#         if (
#             self.buy_sl is None
#  # type: ignore            or self.buy_tp is None
#         ):
#             return True

#         if(self.buy_sl > self.buy_tp): # should be done via constraints
#             return True
        
        if (self.data.index[-1] in self.main_data.index):
            work_data = self.main_data.loc[self.main_data.index
                                            <= self.data.index[-1]]

            if(len(self.orders) > 0):
                for order in self.orders:
                    order.cancel()


            try:
                func = getattr(screenings, self.params['strategy'])
                result = func(work_data, self.tf_timeframe)
                if result != {}:

                    if(self.params['type'] == "BUY"):
                        self.buy(sl=result['stop_loss'],
                                tp=result['take_profit'],
                                limit=result['entry_value'])
                    else:
                        self.sell(sl=result['stop_loss'],
                                 tp=result['take_profit'],
                                 limit=result['entry_value'])

            except UserWarning as usr_e:
                logging.info(usr_e)
            except Exception as e:
                logging.error(e)
                return False

       
        else:
            return True


@newrelic.agent.background_task()
def run_backtest(params):

    data = datacon.get_data(params['symbol'], 'm5')
    main_data = datacon.get_data(params['symbol'], params['period'])

    if (len(data) == 0 or len(main_data) == 0):
        return False

    strat = bb_backtest
    strat.main_data = main_data
    strat.tf_timeframe = params['period']
    
    strat.params = params
    

    bt = Backtest(
        data,
        strat,
        commission=0,
        exclusive_orders=True,
        cash=100000)

    # stats = bt.optimize(
    #     buy_sl=list(np.arange(1, 3, 0.5)),
    #     buy_tp=list(np.arange(1, 4, 0.5)),
    #     maximize='SQN',
    #     # minimize='Max. Drawdown [%]',
    #     max_tries=200,
    #     random_state=0,
    #     return_heatmap=False)
    stats = bt.run()

    new_hm = {}
    new_hm['insert_timestamp'] = datetime.datetime.now()
    new_hm['strategy'] = params['strategy']
    new_hm['period'] = params['period']
    new_hm['symbol'] = params['symbol']
    new_hm['test_type'] = 'LASTBAR'
    new_hm['n_trades'] = stats['# Trades']

    doc = json.dumps({**stats._strategy._params,
                     **stats, **new_hm}, default=str)
    doc = json.loads(doc)

    datacon.post_results(
        params['symbol'], params['period'], doc, params['strategy'])

    list_doc = {}
    list_doc['insert_timestamp'] = datetime.datetime.now()
    list_doc['n_trades'] = stats['# Trades']
    list_doc['strategy'] = params['strategy']
    list_doc['period'] = params['period']
    list_doc['symbol'] = params['symbol']
    list_doc['trades_list'] = stats._trades.to_dict('records')
    list_doc['equity_curve'] = stats._equity_curve.to_dict('records')
    
    list_doc = json.dumps(list_doc, default=str)
    list_doc = json.loads(list_doc)

    datacon.post_list_results(
        params['symbol'], params['period'], list_doc, params['strategy'])


@newrelic.agent.background_task()
def continuous_run():
    try:
        params = datacon.find_params()

        logging.warning('Running backtest for inside_bar_buy on: ' +
                        str(params))
        bt_ret = run_backtest(params)

        if bt_ret is False:
            datacon.update_status(params=params, status=-1)
        else:
            datacon.update_status(params=params, status=2)
        logging.warning('Finished ' + str(params))

    except Exception as e:
        logging.error(e)
        time.sleep(10)
        raise

    return True
