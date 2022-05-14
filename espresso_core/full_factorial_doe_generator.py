import xmlutils as xu
import epistudy_cfg as ec
from itertools import chain, imap, tee
import  collections
import copy
import subprocess
import utilities
class doe_generator:
    def __init__(self, args):
        self.cell_cfg_root = args[0]
        self.domain_iter = args[1]
        self.param_desc_prefix = args[2]
        if args[3] is None: 
            self.base_dir = ec.get_study_dir(self.cell_cfg_root)
            #self.param_comb_iter = utilities.combinations_with_replacement('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1) because postgres requires special care with captials 
            self.param_comb_iter = utilities.combinations_with_replacement('abcdefghijklmnopqrstuvwxyz', 1)
            child_elem = next(self.domain_iter, None)
        else:
            self.base_dir = args[3]
            self.param_comb_iter = args[4]
            
        self.value_comb_iter = utilities.combinations_with_replacement('abcdefghijklmnopqrstuvwxyz', 1)

            
        self.children = []
        self.answer = None


        #get childrens of the root node
        


        child_elem = next(self.domain_iter, None)
        if child_elem is None:
            self.answer = [self.cell_cfg_root, self.param_desc_prefix, self.base_dir]
            #assert False
            return
        [child_param_name, child_param_values, child_param_type, child_param_abbrv]  = ec.get_sweep_param_desc(child_elem)

        if child_param_name == "run/replicate":
            self.answer = [self.cell_cfg_root, self.param_desc_prefix, self.base_dir, self.param_comb_iter, self.value_comb_iter]
            return

        #don't assign label to "sid" 
        cell_param_id_label = next(self.param_comb_iter) # the char represeting this cell design
            
        for child_param_val in child_param_values:
            child_param_dir=self.base_dir + '/param_'+ child_param_name + "_" + str(child_param_val)
            #subprocess.call('mkdir -p ' + child_param_dir, shell=True)
            xmlstr = xu.tostring(self.cell_cfg_root)
            curr_cfg_root  = copy.deepcopy(self.cell_cfg_root)
            #ec.add_cfg_node(curr_cfg_root, child_param_name, str(child_param_val))
            ec.set_cfg_node(curr_cfg_root, child_param_name, str(child_param_val))
            #child_desc_prefix=self.param_desc_prefix +  child_param_abbrv + '_' + str(child_param_val).replace(".", "") + '_'
            #using new descriptor
            cell_value_id_label = next(self.value_comb_iter)
            child_desc_prefix=self.param_desc_prefix +  ''.join(cell_param_id_label) + ''.join(cell_value_id_label)
            self.domain_iter, child_iter = tee(self.domain_iter)
            
            
            child_args = [curr_cfg_root, child_iter, child_desc_prefix, child_param_dir, self.param_comb_iter, self.value_comb_iter]
            self.children.append(child_args)


            
    def __iter__(self):
        "iterate over the childerns"
        if  self.answer is not None:
            yield self.answer
        else:
            for v in chain(*imap(iter, [doe_generator(c) for c in self.children])): #create an iterator over the childrens
                yield v
        

