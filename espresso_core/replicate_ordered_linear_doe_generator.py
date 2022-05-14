import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap, tee
import  collections
import copy
import subprocess
import json
import random
import os
import pickle
from datetime import datetime

def build_cell_param_attr_dict(domain_iter, cfg_root):
    param_val_dict = dict()
    domain_iter_ref = domain_iter

    for child_elem in domain_iter:
        [child_param_name, child_param_values, child_param_type, child_param_abbrv]  = ec.get_sweep_param_desc(child_elem)
        param_val = xu.get_value_of_key(cfg_root, child_param_name, path_prefix='.//')
        param_val_dict[child_param_name] = param_val
    return param_val_dict


class doe_generator:
    def __init__(self, args):
        self.cell_cfg_root = args[0]
        self.domain_iter = args[1]
        self.param_desc_prefix = args[2]
        self.base_dir = ec.get_study_dir(self.cell_cfg_root)
        self.all_cell_signature = set() #set of all cell signature
        self.all_randgen_seed = set()
        sid = xu.get_value_by_attr(self.cell_cfg_root, 'run/sid')
        self.random_seed_fn  = 'sid_' + str(sid) + "_generator_random_seed.pickle"
        if not os.path.isfile(self.random_seed_fn):
            generator_seed = datetime.now()
            with open(self.random_seed_fn, 'w') as fh:
                pickle.dump(generator_seed, fh)
            print "seed ", generator_seed
        else:
            with open(self.random_seed_fn, 'r') as fh:
                generator_seed = pickle.load(fh)
            print "using pregenerated generator seed ", generator_seed
        random.seed(generator_seed)
        
    def __iter__(self):
        rep_elem = xu.get_elem_by_key_value(self.cell_cfg_root, 'sweep',  'abbrv', 'rep', uniq=True)
        num_replicates = int(xu.get_value_by_attr(rep_elem, 'end_val'))
        print "num_replicates = ", num_replicates
        self.domain_iter, domain_iter_ref = tee(self.domain_iter)
        for i in xrange(num_replicates): # create rep directory
            #self.all_cell_signature.clear()
            #fix epifast/randgen_seed
            rep_i_seed = random.randint(0, 1048576 * 1000)
            while  rep_i_seed in self.all_randgen_seed:
                rep_i_seed = random.randint(0, 1048576 * 1000)
            randgen_seeded_root = copy.deepcopy(self.cell_cfg_root)
            ec.set_cfg_node(randgen_seeded_root, 'epifast/randgen_seed', str(rep_i_seed))
            domain_iter_ref, domain_iter_loop = tee(domain_iter_ref)
            for child_elem in domain_iter_loop:
                [child_param_name, child_param_values, child_param_type, child_param_abbrv]  = ec.get_sweep_param_desc(child_elem)
                if child_param_name == 'run/sid':
                    continue
                if child_param_name == 'run/replicate':
                    continue


                for child_param_val in child_param_values:
                    child_param_dir=self.base_dir + '/param_'+ child_param_name + "_" + str(child_param_val)
                    xmlstr = xu.tostring(self.cell_cfg_root)
                    curr_cfg_root  = copy.deepcopy(randgen_seeded_root)
                    ec.set_cfg_node(curr_cfg_root, child_param_name, str(child_param_val))
                    child_desc_prefix=self.param_desc_prefix +  child_param_abbrv + '_' + str(child_param_val).replace(".", "") + '_'
                    #need this so that we are not generating duplicate cells
                    #domain_iter_ref, domain_iter_copy = tee(domain_iter_ref)
                    #cell_param_val_dict = build_cell_param_attr_dict(domain_iter_copy, curr_cfg_root)
                    #cell_param_val_json = json.dumps(cell_param_val_dict)
                    #turning off duplicate --
                    #uniqness is guaranteed because of randgen_seed
                    #if cell_param_val_json in self.all_cell_signature:
                    #    continue
                    #self.all_cell_signature.add(cell_param_val_json)
                    rep_dir = child_param_dir + '/param_replicate_' + str(i)
                    rep_prefix = child_desc_prefix + 'rep_' + str(i)
                    param_name = 'run/replicate'
                    ec.set_cfg_node(curr_cfg_root, param_name, str(i))
                    ans = [curr_cfg_root, rep_prefix, rep_dir]
                    yield ans
