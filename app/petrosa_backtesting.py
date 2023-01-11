import datetime
import json
import logging
import time

import newrelic.agent
import numpy as np
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
                result = screenings.inside_bar_buy(work_data, self.tf_timeframe)
            except UserWarning as usr_e:
                logging.info(usr_e)
            except Exception as e:
                logging.error(e)
                return False

            if result != {}:
                try:
                    
                    # sl = result['entry_value'] * ((100 - self.buy_sl) / 100)
                    # tp = result['entry_value'] * ((100 + self.buy_tp) / 100)
                    
                    # self.buy(sl=sl, 
                    #         tp=tp, 
                    #         limit=result['entry_value'])
                    self.buy(sl=result['stop_loss'], 
                            tp=result['take_profit'], 
                            limit=result['entry_value'])
                except Exception as e:
                    logging.error(e)            
        else:
            return True


@newrelic.agent.background_task()
def run_backtest(symbol, test_period):

    data = datacon.get_data(symbol, 'm5')
    main_data = datacon.get_data(symbol, test_period)

    if (len(data) == 0 or len(main_data) == 0):
        return False

    strat = bb_backtest
    strat.main_data = main_data

    strat.tf_timeframe = test_period

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
    new_hm['strategy'] = 'inside_bar_buy'
    new_hm['period'] = test_period
    new_hm['symbol'] = symbol
    new_hm['trades_list'] = stats._trades.to_dict('records')
    new_hm['equity_curve'] = stats._equity_curve.to_dict('records')
    new_hm['test_type'] = 'LASTBAR'

    doc = json.dumps({**stats._strategy._params,
                     **stats, **new_hm}, default=str)
    doc = json.loads(doc)

    datacon.post_results(symbol, test_period, doc)


@newrelic.agent.background_task()
def continuous_run():
    try:
        params = datacon.find_params()

        logging.warning('Running backtest for inside_bar_buy on: ' +
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
        raise

    return True
