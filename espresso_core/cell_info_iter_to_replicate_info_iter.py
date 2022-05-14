import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap, tee, product
import  collections
import math
import subprocess
import copy

def combinations_with_replacement(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    for indices in product(range(n), repeat=r):
        if sorted(indices) == list(indices):
            yield tuple(pool[i] for i in indices)

replicate_info = collections.namedtuple('replicate_info', 'cfg_root, orig_rep_desc, orig_rep_dir, abbrv_rep_desc, abbrv_rep_dir')


class to_replicate_info:
    def __init__(self, cfg_root, doe_cell_iter):
        rep_elem = xu.get_elem_by_key_value(cfg_root, 'sweep',  'abbrv', 'rep', uniq=True)
        self.num_replicates = int(xu.get_value_by_attr(rep_elem, 'end_val'))  #+2 for num_replicates = 0
        self.id_comb_slots = int(math.ceil(math.log10(max(2,self.num_replicates))))
        self.doe_cell_iter = doe_cell_iter
        self.sid = xu.get_value_by_attr(cfg_root, 'run/sid')
    def __iter__(self):
        for ci in self.doe_cell_iter: #create an iterator over the childrens
            comb_iter = combinations_with_replacement('0123456789', self.id_comb_slots)
            subprocess.call('mkdir -p ' + ci.abbrv_cell_dir, shell=True)
            for rid in xrange(self.num_replicates):
                short_name_tup = next(comb_iter)
                short_name = ''.join(short_name_tup)
                param_name = 'run/replicate'
                curr_cfg_root = copy.deepcopy(ci.cfg_root)
                ec.set_cfg_node(curr_cfg_root, param_name, str(rid))
                ri = replicate_info(cfg_root=curr_cfg_root, orig_rep_desc=ci.orig_cell_desc + "_" + short_name,   orig_rep_dir = ci.orig_cell_dir + "_" + short_name, abbrv_rep_desc="sid_" + self.sid + "_" + ci.abbrv_cell_desc + "_" + short_name, abbrv_rep_dir = ci.abbrv_cell_dir + "/" + short_name)
                yield ri
