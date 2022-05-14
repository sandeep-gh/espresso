import sys
import xmlutils as xu
from itertools import chain, imap, product
import  collections
import full_factorial_doe_generator
doe_generator = full_factorial_doe_generator.doe_generator

import random


# def combinations(iterable, r):
#     # combinations('ABCD', 2) --> AB AC AD BC BD CD
#     # combinations(range(4), 3) --> 012 013 023 123
#     pool = tuple(iterable)
#     n = len(pool)
#     if r > n:
#         return
#     indices = range(r)
#     yield tuple(pool[i] for i in indices)
#     while True:
#         for i in reversed(range(r)):
#             if indices[i] != i + n - r:
#                 break
#         else:
#             return
#         indices[i] += 1
#         for j in range(i+1, r):
#             indices[j] = indices[j-1] + 1
#         yield tuple(pool[i] for i in indices)

# def combinations_with_replacement(iterable, r):
#     pool = tuple(iterable)
#     n = len(pool)
#     for indices in product(range(n), repeat=r):
#         if sorted(indices) == list(indices):
#             yield tuple(pool[i] for i in indices)


def print_cfg(args):
    print args



cfg_root = xu.read_file(sys.argv[1])
#domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')

#doe_iter = doe_generator([cfg_root, domain_iter, '', None])
#

domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
doe_iter = doe_generator([cfg_root, domain_iter, '', None,None])
from assign_short_name import assign_short_name
import  doe_iter_to_cell_info_iter as cii
to_cell_info = cii.to_cell_info
import  cell_info_iter_to_replicate_info_iter as torii
to_replicate_info = torii.to_replicate_info
#doe_with_short_name_iter = assign_short_name(doe_iter)
doe_with_short_name_iter = to_replicate_info(cfg_root, to_cell_info(doe_iter))
collections.deque(imap(print_cfg,doe_with_short_name_iter), maxlen= 0)

# comb_iter = combinations_with_replacement('ABCD', 3)
# for i in comb_iter:
#     print i


