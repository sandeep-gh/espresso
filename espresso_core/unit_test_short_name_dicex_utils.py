import sys
import xmlutils as xu
from itertools import chain, imap, product
import  collections
from lhs_doe_generator import doe_generator
from dicex_epistudy_utils import prepare_config_files_iter
import dicex_epistudy_utils as deu
import random


def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

def combinations_with_replacement(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    for indices in product(range(n), repeat=r):
        if sorted(indices) == list(indices):
            yield tuple(pool[i] for i in indices)


def print_cfg(args):
    print type(args.abbrv_rep_dir)


cfg_root = xu.read_file(sys.argv[1])
domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')

doe_iter = doe_generator([cfg_root, domain_iter, '', None])
#from assign_short_name import assign_short_name
#doe_with_short_name_iter = assign_short_name(doe_iter)
#collections.deque(imap(prepare_config_files_iter, doe_with_short_name_iter), maxlen= 0)

#collections.deque(imap(print_cfg, doe_with_short_name_iter), maxlen= 0)
deu.create_replicate_configurations(cfg_root)
# comb_iter = combinations_with_replacement('ABCD', 3)
# for i in comb_iter:
#     print i


