#Readme: Provides low utilities to manage/query info about replicates and cells

from itertools import izip
import versa_api as vapi
import replicate_visitor as rv
from string import Template
import xmlutils as xu
import  collections
from collections import namedtuple
from itertools import chain, imap
import epistudy_cfg as ec
import versa_core.schema as sch
import versa_core.relational as re
import versa_api_meta as vam
import utilities
import versa_core.utils as vu

import versa_core.export as ex

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)

def get_replicate_model_obj(replicate_desc, model_base_name):
    model_name = replicate_desc + model_base_name
    [model_obj] = vu.load_rmos([model_name])
    #model_obj = vu.import_model(model_name)
    return model_obj

# def annotate_model_param_sweep_attrsvals_v2(session=None, model_base_name, config_xml=None):
#     '''
#     annotate each model/table of expconfig with attributes; is little flaky
#     '''
#     if not os.path.isfile(config_xml):
#         print "file not found", config_xml

#     rep_model = get_replicate_model_obj(replicate_desc, model_base_name)



        
    
def annotate_model_param_sweep_attrsvals(session=None, cls=None, descriptor=None, sweep_params=None):
    '''
    annotate each model/table of expconfig with attributes; is little flaky
    '''
    try:
        cls_name = cls.__name__
    except:
        print "expecting a class; but got a subquery object"
        assert(0)

    toks =  descriptor.split('_')[0:2 * len(sweep_params)]
    for par,val in pairwise(toks):
        cls = vapi.add_const_column(session, cls, val, par)
    return cls


def annotate_models_param_sweep_attrsvals(session, models, descriptors, sweep_params):
    return [annotate_model_param_sweep_attrsvals(session, m, d, sweep_params) for m,d in zip(models, descriptors)]


def get_sweep_params(cfg_root):
    '''returns list of sweep params
       scan the xml config file to list the sweep parameters
    '''
    domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
    return [xu.get_value_elem(dxe, 'abbrv', path_prefix='./') for dxe in domain_iter]
#     for dxe in domain_iter:
#         param_abbrv = xu.get_value_elem(dxe, 'abbrv', path_prefix='./')
#         sweep_params.append(param_abbrv)
#     return sweep_params

def get_cell_attrs(cfg_root):
    '''returns list of sweep params
       scan the xml config file to list the sweep parameters
    '''
    sweep_params = get_sweep_params(cfg_root)
    return sweep_params[:-1]


def get_rep_attr(cfg_root):
    '''returns label for the replicate attribute
    '''
    sweep_params = get_sweep_params(cfg_root)
    return sweep_params[-1]


class filter_failed_runs_iter_c:
    '''
    removes failed runs
    '''
    def __init__(self, session, doe_iter=None):
        self.session = session
        self.doe_iter = doe_iter
        self.day_tracker_model_suffix='_day_tracker'

    def __iter__(self):
        for replicate_info in self.doe_iter:
            cfg_root = replicate_info.cfg_root
            replicate_desc = replicate_info.abbrv_rep_desc
            replicate_dir = replicate_info.abbrv_rep_dir
            num_sim_days = ec.get_simulation_duration(cfg_root)
            day_tracker_model = get_replicate_model_obj(replicate_desc, self.day_tracker_model_suffix)
            num_days = re.cardinality(self.session, day_tracker_model)
            if num_days == num_sim_days or (num_days + 5) > num_sim_days + 1: 
                yield replicate_info #this run completed successfully
            else:
                print "replicate ", replicate_desc, " failed"


annotated_model_info_t = namedtuple('annotated_model_info', ['rep_rmo', 'doe_param_value', 'replicate_desc', 'orig_rep_rmo', 'cfg_root'])

class annotate_model_domain_attr_value:
    def __init__(self, session, model_base_name, doe_iter):
        self.session = session
        self.model_base_name = model_base_name
        self.doe_iter = doe_iter

    def __iter__(self):
        for replicate_info in self.doe_iter:
            cfg_root = replicate_info.cfg_root
            orig_replicate_desc = replicate_info.orig_rep_desc
            orig_replicate_dir = replicate_info.orig_rep_dir
            replicate_desc = replicate_info.abbrv_rep_desc
            rep_model = get_replicate_model_obj(replicate_desc, self.model_base_name)
            try:
                cls_name = rep_model.__name__
            except:
                print "expecting a class; but got a subquery object"
                assert(0)
            cls = rep_model
            doe_param_value = dict()
            domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
            columns_annotated = [] #list of fields/columns annotated 
            for de in domain_iter:
                [child_param_name, child_param_values, child_param_type, child_param_abbrv]  = ec.get_sweep_param_desc(de)
                param_val = xu.get_value_of_key(cfg_root, child_param_name, path_prefix='.//')
                if child_param_abbrv == 'sid' or child_param_abbrv == 'rep':
                    cls = sch.add_const_column(self.session, cls, param_val, child_param_abbrv)
                else:
                    cls = sch.add_float_const_column(self.session, cls, param_val, child_param_abbrv)
                columns_annotated.append(child_param_abbrv)

                doe_param_value[child_param_abbrv] = param_val
            vam.set_primary_keys(self.session, cls, columns_annotated)
            yield annotated_model_info_t(cls, doe_param_value, replicate_desc, rep_model, cfg_root)


class filter_replicates_by_attr_value_iter_c:
    def __init__(self, session, annotated_rmo_iter=None, attr=None, value=None):
        self.session = session
        self.rmo_iter = annotated_rmo_iter
        self.attr = attr
        self.value = value
    def __iter__(self):
        for annotated_model_info in self.rmo_iter:
            assert self.attr in annotated_model_info.doe_param_value
            if annotated_model_info.doe_param_value[self.attr] == str(self.value):
                yield annotated_model_info

class model_transform_iter_c:
    '''
    input: iterator, functor
    action:
    applies the functor to the models in the iterator
    '''
    def __init__(self, session, annotated_rmo_iter=None, model_functor=None):
        self.session = session
        self.rmo_iter = annotated_rmo_iter
        self.model_functor = model_functor
        
    def __iter__(self):
        for annotated_model_info in self.rmo_iter:
            transformed_rep_rmo = self.model_functor(annotated_model_info.rep_rmo)
            yield annotated_model_info_t(transformed_rep_rmo, annotated_model_info.doe_param_value, annotated_model_info.replicate_desc, annotated_model_info.orig_rep_rmo, annotated_model_info.cfg_root)



# class annotate_agents_by_category_iter_c:
#     '''
#     takes an rmo iterator and returns an rmo iterator
#     '''

#     def __init__(self, session, category_rmo=None, doe_iter=None, category_attr=None, agent_attr=None):
#         self.session = session
#         self.doe_iter = doe_iter
#         self.category_rmo = category_rmo
#         self.category_attr = category_attr
#         self.agent_attr = agent_attr
        
#     def __iter__(self):
#         for rep_rmo_info in self.doe_iter:
#             stmt = re.fuseEQ(self.session, self.category_rmo, rep_rmo_info.cls,  category_attr, agent_attr)
#             yield annotated_model_info_t(stmt, rep_rmo_info.doe_param_value, rep_rmo_info.replicate_desc, rep_rmo_info.rep_model, rep_rmo_info.cfg_root)
            
class proj_rmo_iter_c:
    '''
    returns an iterator of only rmo_model 
    '''
    def __init__(self, session, rep_info_iter=None):
        self.session = session
        self.rep_info_iter = rep_info_iter
        
    def __iter__(self):
        for rep_info in self.rep_info_iter:
            yield(rep_info.rep_rmo)
    
#this is phased out
# def get_all_replicate_models(session, cfg_root, model_base_name, param_sweep_annotation=True):
#     class replicate_models:
#         def __init__(self):
#             self.all_models = []
#             self.all_orig_rep_desc = []
#             self.all_config_xml = []
#         def add_models(self, replicate_info):
#             cfg_root = replicate_info.cfg_root
#             orig_replicate_desc = replicate_info.orig_rep_desc
#             orig_replicate_dir = replicate_info.orig_rep_dir
#             replicate_desc = replicate_info.abbrv_rep_desc
#             rep_model = get_replicate_model_obj(replicate_desc, model_base_name)
#             self.all_models.append(rep_model)
#             self.all_orig_rep_desc.append(orig_replicate_desc)
#     rm = replicate_models()
#     add_models_func = (lambda args=None: rm.add_models(args))
    

#     import doe_generator_plugin as dgp
#     import add_study_utils as asu
#     doe_generator = dgp.get_doe_generator(cfg_root)
#     domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
#     doe_iter = doe_generator([cfg_root, domain_iter, '', None])
#     from assign_short_name import assign_short_name
#     doe_with_short_name_iter = assign_short_name(doe_iter)
#     collections.deque(imap(add_models_func,doe_with_short_name_iter), maxlen= 0) #call prepare_config_files for each cfg of the doe

#     sweep_params = get_sweep_params(cfg_root)
#     if param_sweep_annotation:
#         rm.all_models = annotate_models_param_sweep_attrsvals(session, rm.all_models, rm.all_orig_rep_desc, sweep_params)
#     return [rm.all_models, sweep_params]





