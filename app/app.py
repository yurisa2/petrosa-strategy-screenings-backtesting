import os
from app import petrosa_backtesting
from datetime import datetime
import time
import random
import logging


logging.warning('starting petrosa-strategy-screenings-backtesting | ver.: ' + 
                os.environ.get('VERSION', '0.0.0'))

# time.sleep(random.randint(1,150))

while True:
    petrosa_backtesting.continuous_run()
