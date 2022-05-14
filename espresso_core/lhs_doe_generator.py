import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap
import  collections
import copy
import sys
import subprocess
import os
sys.path.append('/home/pgxxc/public/FUSE')
import exp_design
import pickle

#def prepare_config_files(cfg_root, replicate_desc, replicate_dir, param_root):
#def vary_param(cfg_root, param_desc_prefix='', param_root=None, curr_dir=None, rep_method=None):
#------------------------------------------------------------------------------
# SW: flat version for doe

def doe_lhs(domain_iter, num_samples) :
    param_list = list()
    abbrv_list = list()
    continuous_p = dict()
    discrete_p = dict()
    for child_elem in domain_iter:
        #print xu.tostring(child_elem)
        [child_param_name, child_param_values, child_param_type, child_param_abbrv]  = ec.get_sweep_param_desc(child_elem)
        if child_param_name == 'run/sid':
            continue
        if child_param_name == 'run/replicate':
            continue
        param_list.append(child_param_name)
        abbrv_list.append(child_param_abbrv)
        lbound = child_param_values[0]
        ubound = child_param_values[-1]
        scale = float(ubound) - float(lbound) 

        #discrete_p[child_param_name] = [] #list of levels
        if child_param_type == 'strided': #consider this as continuous parameter
            continuous_p[child_param_name] = (lbound, scale,num_samples, '','UNIFORM')
        if child_param_type == 'enum': #consider this as discrete parameter
            print "using enum for param ", child_param_name, " with values ", child_param_values
            discrete_p[child_param_name] = child_param_values

    #n = len(param_list) #number of parameter
    #intervals = n * [num_samples]
    exp = exp_design.exp_init(continuous_parameters=continuous_p, discrete_parameters=discrete_p, num_samples=int(num_samples))
    #exp = exp_design.exp_init(continuous_parameters=continuous_p, num_samples=int(num_samples))
                              
    # Samples are flat parameter value list, each item corresponds to a cell:
    # A n parameter experimental design with m number of cells will look like following:
    #   [[p11, p21, ..., pn1],
    #     [p12, p22, ..., pn2],
    #     .
    #     .
    #     .
    #     [p1m, p2m, ..., pnm]
    #    ]
    samples = exp.doe_rest
    factors = exp.factors

    #print samples

    return [param_list, abbrv_list, factors, samples]

class doe_generator:
    def __init__(self, args):
        self.cfg_root = args[0]
        self.domain_iter = args[1]
        self.param_desc_prefix = args[2]
        if args[3] is None: 
            self.base_dir = ec.get_study_dir(self.cfg_root)
        else:
            self.base_dir = args[3]
        num_samples = ec.get_num_samples(self.cfg_root)
        sid = xu.get_value_by_attr(self.cfg_root, 'run/sid')
        
        self.doe_fn  = 'sid_' + str(sid) + "_lhs.pickle"
        sid_sweep_elem = next(self.domain_iter)
        if not os.path.isfile(self.doe_fn):
            doe = doe_lhs(self.domain_iter, num_samples)
            with open(self.doe_fn, 'w') as fh:
                u = pickle.Pickler(fh)
                u.dump(doe)

    def __iter__(self):

        with open(self.doe_fn, 'r') as fh:
            u = pickle.Unpickler(fh)
            doe = u.load()
        param_list = doe[0]
        abbrv_list = doe[1]
        factors = doe[2]
        samples = doe[3]
        #replicate = int(ec.get_replicate_flat(self.cfg_root))
        rep_elem = xu.get_elem_by_key_value(self.cfg_root, 'sweep',  'abbrv', 'rep', uniq=True)
        num_replicates = int(xu.get_value_by_attr(rep_elem, 'end_val'))
        for cell in samples:
            cell_dir = self.base_dir
            sid = xu.get_value_by_attr(self.cfg_root, 'run/sid')
            cell_prefix = 'sid_' + sid + '_' #TODO: add sid here
            curr_cfg_root = copy.deepcopy(self.cfg_root)
            for i, val in enumerate(cell):
                param_name = factors[i]
                if type(val) is float:
                    val = str('%f' % val)
                print "param name = ", param_name, " cell val = ", val
                
                cell_dir = cell_dir +  '/param_' + param_name + '_' + str(val)
                param_abbrv = abbrv_list[i]
                cell_prefix = cell_prefix + param_abbrv + '_' + str(val).replace(".", "").replace("-", "") + '_'
                # set parameter value
                ec.set_cfg_node(curr_cfg_root, param_name, str(val))
        
            for i in xrange(num_replicates): # create rep directory
                rep_dir = cell_dir + '/param_replicate_' + str(i)
                rep_prefix = cell_prefix + 'rep_' + str(i)
                param_name = 'run/replicate'
                ec.set_cfg_node(curr_cfg_root, param_name, str(i))
                #subprocess.call('mkdir -p ' + rep_dir, shell=True)
                ans = [curr_cfg_root, rep_prefix, rep_dir]
                yield ans




 
