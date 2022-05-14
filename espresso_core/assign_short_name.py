import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap, tee, product
import  collections

def combinations_with_replacement(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    for indices in product(range(n), repeat=r):
        if sorted(indices) == list(indices):
            yield tuple(pool[i] for i in indices)

replicate_info = collections.namedtuple('replicate_info', 'cfg_root, orig_rep_desc, orig_rep_dir, abbrv_rep_desc, abbrv_rep_dir')

doe_size = "small"
id_comb_slots = 4

class assign_short_name:
    def __init__(self, args):
        self.doe_iter = args
        self.comb_iter = combinations_with_replacement('abcdefghijklmnopqrstuvwxyz', id_comb_slots)
    def __iter__(self):
        for v in self.doe_iter: #create an iterator over the childrens

            short_name_tup = next(self.comb_iter)
            short_name = ''.join(short_name_tup)
            study_dir = ec.get_study_dir(v[0])
            sid = xu.get_value_by_attr(v[0], 'run/sid')

            ri = replicate_info(cfg_root=v[0], orig_rep_desc=v[1], orig_rep_dir = v[2], abbrv_rep_desc="sid_" + sid + "_" + short_name, abbrv_rep_dir = study_dir + "/" + "sid_" + sid + "_" + short_name)
            yield ri
