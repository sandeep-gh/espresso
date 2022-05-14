#README: launches a large number of jobs in phases so as to
#not over overload the qsub system


import dicex_epistudy_utils as deu
import epistudy_cfg as ec
from itertools import chain, imap, islice, tee
import  collections
import utilities
import xmlutils as xu
import time
def print_cfg(replicate_info):
    print replicate_info


class chunk_iter_naiive:
    def __init__(self, doe_iter, chunk_size, carry_over):
        self.doe_iter = doe_iter
        self.chunk_size = chunk_size
        self.eos = False
        self.carry_over = carry_over
        
    def __iter__(self):
        idx = 0

        self.doe_iter, doe_iter_copy = tee(self.doe_iter)
        print "iter is called again idx=", idx
        print utilities.count_iterable(doe_iter_copy)

        if self.carry_over is not None:
            idx = 1
            yield self.carry_over
            
        self.carry_over = None
        for v in self.doe_iter:
            if idx == self.chunk_size:
                self.carry_over = v
                break
            else:
                idx = idx + 1
                yield v
            
def launch_epifast_jobs(cfg_root):
    doe_iter = deu.get_doe_iter(cfg_root)
    doe_iter, doe_iter_copy = tee(doe_iter)
    num_total_replicates = utilities.count_iterable(doe_iter_copy)
    if num_total_replicates > 300: 
        print "num_total_replicates ", num_total_replicates
        print "print any key to continue"
    doe_iter = deu.get_doe_iter(cfg_root)
    chunk_size = 200
    chunk_iter = chunk_iter_naiive(doe_iter, chunk_size, None)
    start_pos = 0
    while True:
        #chunk_iter = chunk_iter_naiive(doe_iter, chunk_size)
        collections.deque(imap(deu.launch_ef_job_iter, chunk_iter), maxlen= 0) #schedule launch for all the epifast jobs
        if chunk_iter.carry_over is None:
            break
        #chunk_iter = islice(doe_iter, start_pos, chunk_size)
        #workaround for checking if an iterator is empty
        #this check is slow and memory consuming -- standard efficient now known in python
        #workaround depend on special use case
        #chunk_iter, chunk_iter_copy = tee(chunk_iter)
        #if True: #list(chunk_iter_copy): #there are still replicates in the iterator
            #collections.deque(imap(deu.launch_ef_job_iter,chunk_iter), maxlen= 0) #schedule launch for all the epifast jobs
        #    collections.deque(imap(print_cfg, chunk_iter), maxlen= 0) #schedule launch for all the epifast jobs
        #else:
        #break

        print chunk_size, " jobs launched... waiting"
        time.sleep(200)
            
