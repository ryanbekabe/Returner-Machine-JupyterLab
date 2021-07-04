#https://gist.github.com/sahands/9538291
#SteinhausJohnsonTrotter algorithm or Johnson-Trotter algorithm
from time import sleep
from datetime import datetime

print('Time: ',datetime.now())
def start_end_timer(start_time=None):
    if not start_time:
        start_time = datetime.now()
        return start_time
    elif start_time:
        thour, temp_sec = divmod((datetime.now() - start_time).total_seconds(), 3600)
        tmin, tsec = divmod(temp_sec, 60)
        print('\nTime taken: %i hours %i minutes and %s seconds.' % (thour, tmin, round(tsec, 2)))

__author__ = "Sahand Saba"

start_time = start_end_timer(None)
def nobody():
    while True:
        yield False

# The term "troll" is taken from Knuth's choice of word
def sjt(pi, inv, i, trolls):
    d = -1  # Directoin. -1 is descending, +1 is ascending.
    while True:
        j = inv[i]  # j is the position of the current "troll"
        if pi[j] < pi[j + d]:
            d = -d
            yield next(trolls[i - 1])
        else:
            pi[j], pi[j + d] = pi[j + d], pi[j]
            inv[i] += d
            inv[pi[j]] -= d
            yield True
    #print('Time: ',datetime.now())

def setup(n):
    # Pad pi with n + 2, so that pi[i] will always be < the two ends.
    pi = [n + 2] + [i for i in range(1, n + 1)] + [n + 2]
    inv = pi[:-1]
    # nobody simply continuously yields False. By adding a "nobody" generator
    # at both ends of trolls, False is autmatically yieded by sjt when needed.
    trolls = [nobody()]
    trolls.extend(sjt(pi, inv, i + 1, trolls) for i in range(n))
    trolls += [nobody()]
    # The lead troll will be the item n in the permutation
    lead_troll = trolls[-2]
    return pi, lead_troll
    #print('Time: ',datetime.now())

def permutations(n):
    pi, lead_troll = setup(n)
    yield pi[1:-1]
    while next(lead_troll):
        yield pi[1:-1]
    #print('Time: ',datetime.now())

def cyclic_test(n):
    pi, lead_troll = setup(n)
    c = 0
    while True:
        print('Output: ', ''.join(str(x) for x in pi[1:-1]))
        c += 1
        if not next(lead_troll):
            print('-------')
            print(c)
            print('-------')
            sleep(1)
            c = 0
    #print('Time: ',datetime.now())

if __name__ == '__main__':
    #print('\n'.join(''.join(str(x) for x in pi) for pi in permutations(1)))
    #print('\n'.join(''.join(str(x) for x in pi) for pi in permutations(2)))
    #print('\n'.join(''.join(str(x) for x in pi) for pi in permutations(3)))
    #print('\n'.join(''.join(str(x) for x in pi) for pi in permutations(9)))
    print(' '.join(''.join(str(x) for x in pi) for pi in permutations(11)))
    start_end_timer(start_time)
    print('Time: ',datetime.now())
    #cyclic_test(3)
#12345678=Time taken: 0 hours 0 minutes and 0.32 seconds.
#permutations(7)=Time taken: 0 hours 0 minutes and 0.04 seconds.
#permutations(8)=Time taken: 0 hours 0 minutes and 0.34 seconds.
#permutations(9)=Time taken: 0 hours 0 minutes and 6.23 seconds.
#permutations(9)=Time taken: 0 hours 0 minutes and 2.9 seconds. pakai space ( )
#permutations(10)=Time taken: 0 hours 0 minutes and 52.54 seconds. pakai space ( ) rata2 CPU 30-an %
#permutations(11)=Time taken: 0 hours 16 minutes and 53.76 seconds. pakai space ( ) rata2 CPU 30-an %
