import dicex_epistudy_utils as deu
import epistudy_cfg as ec
from itertools import chain, imap
import  collections
import utilities
import xmlutils as xu
def launch_epifast_jobs(cfg_root):
    doe_iter = deu.get_doe_iter(cfg_root)
    num_total_replicates = utilities.count_iterable(doe_iter)
    if num_total_replicates > 300: 
        print "num_total_replicates ", num_total_replicates
        print "print any key to continue"
    doe_iter = deu.get_doe_iter(cfg_root)
    collections.deque(imap(deu.launch_ef_job_iter,doe_iter), maxlen= 0) #schedule launch for all the epifast jobs


