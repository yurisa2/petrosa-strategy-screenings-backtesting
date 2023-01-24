import pymongo
import os
import pandas as pd

def get_client() -> pymongo.MongoClient:
    client = pymongo.MongoClient(
        os.getenv(
            'MONGO_URI', 'mongodb://root:QnjfRW7nl6@localhost:27017'),
        readPreference='secondaryPreferred',
        appname='petrosa-nosql-crypto'
    )

    return client


col = get_client().petrosa_crypto['backtest_results']

item_list = col.find({{"# Trades": {"$gte": 1000}, "strategy": 1, "symbol": 1}})
item_list = list(item_list)

new_list_keys = []
dupes = []

for item in item_list:
    work_place = f"{item['period']}-{item['strategy']}-{item['symbol']}"
    new_list_keys.append(work_place)
    

df = pd.DataFrame(new_list_keys)


print(dupes)
