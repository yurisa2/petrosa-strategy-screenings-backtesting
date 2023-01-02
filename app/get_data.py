import pymongo
import pandas as pd
import os
import newrelic.agent


@newrelic.agent.background_task()
def get_data(ticker, suffix, limit=999999999):

    client = pymongo.MongoClient(
                os.getenv(
                    'MONGO_URI', 'mongodb://root:QnjfRW7nl6@localhost:27017'),
                readPreference='secondaryPreferred',
                appname='petrosa-nosql-crypto'
                                        )
    db = client["petrosa_crypto"]
    history = db["candles_" + suffix]

    results = history.find({'ticker': ticker},
                           sort=[('datetime', -1)]).limit(limit)
    results_list = list(results)

    if (len(results_list) == 0):
        return []

    data_df = pd.DataFrame(results_list)

    data_df = data_df.sort_values("datetime")

    data_df = data_df.rename(columns={"open": "Open",
                                      "high": "High",
                                      "low": "Low",
                                      "close": "Close"}
                             )

    data_df = data_df.set_index('datetime')

    return data_df
