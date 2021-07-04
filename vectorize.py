import numpy as np
from timeit import default_timer as timer
from numba import vectorize
import time
from datetime import datetime

def start_end_timer(start_time=None):
    if not start_time:
        start_time = datetime.now()
        return start_time
    elif start_time:
        thour, temp_sec = divmod((datetime.now() - start_time).total_seconds(), 3600)
        tmin, tsec = divmod(temp_sec, 60)
        print('Time taken: %i hours %i minutes and %s seconds.' % (thour, tmin, round(tsec, 2)))

@vectorize(['float32(float32, float32)'], target='cuda')
def pow(a, b):
    print(a,b)
    return a ** b

start = timer()
start_time = start_end_timer(None)
a = 90000
b = 90000
print(a, '**', b)
print(pow(a, b))
start_end_timer(start_time)
duration = timer() - start
print(duration)
#[8.261686e+37]
#Time taken: 0 hours 0 minutes and 0.39 seconds.
#0.39451120000001083
#82616862383558673827191783893367291899
#Time taken: 0 hours 0 minutes and 0.0 seconds.
#0.0012121999999408217
#99 ** 20
#8179069375972308708891986605443361898001
#Time taken: 0 hours 0 minutes and 0.0 seconds.
#0.0007308000000421089
#1000 ** 1000
#[inf]
#Time taken: 0 hours 0 minutes and 0.3 seconds.
#0.30604360000006636