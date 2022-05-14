import sys
import xmlutils as xu
from itertools import chain, imap, product
import  collections
from linear_doe_generator import doe_generator
import random
import random

def print_cfg(args):
    #print args.abbrv_rep_dir
    print args
    #print args.orig_rep_desc

cfg_root = xu.read_file(sys.argv[1])
domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')

doe_iter = doe_generator([cfg_root, domain_iter, '', None])
from assign_short_name import assign_short_name
doe_with_short_name_iter = assign_short_name(doe_iter)
collections.deque(imap(print_cfg, doe_with_short_name_iter), maxlen= 0)
#collections.deque(imap(print_cfg, doe_iter), maxlen= 0)
