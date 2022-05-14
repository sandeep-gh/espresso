#wraps doe iterator (doe, full_factorial, or lhs) to replicate_info iterator


import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap, tee, product
import  collections


cell_info = collections.namedtuple('cell_info', 'cfg_root, orig_cell_desc, orig_cell_dir, abbrv_cell_desc, abbrv_cell_dir')



class to_cell_info:
    def __init__(self, args):
        self.doe_iter = args
    def __iter__(self):
        for v in self.doe_iter: #create an iterator over the childrens

            study_dir = ec.get_study_dir(v[0])
            sid = xu.get_value_by_attr(v[0], 'run/sid')
            ri = cell_info(cfg_root=v[0], orig_cell_desc=v[1], orig_cell_dir = v[2], abbrv_cell_desc=v[1], abbrv_cell_dir = study_dir + "/" + "sid_" + sid + "_" + v[1])
            yield ri
