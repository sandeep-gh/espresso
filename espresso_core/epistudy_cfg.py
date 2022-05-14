import xmlutils as xu
import os
import sys
import copy
from datetime import datetime
from string import Template
module_dir=os.path.dirname(os.path.realpath(__file__))

default_config_fn = module_dir + "/config_param_default.xml"
def to_number(string_val):
    try:
        return int(string_val)
    except ValueError:
        return float(string_val)
    except ValueError:
        print "Unkown value type", string_val
        sys.exit(0)

def read_epistudy_cfg(cfg_fn):
    return xu.read_file(cfg_fn)


def get_doe_cfg_fn(doe_id=None):
    assert doe_id is not None
    return 'sid_' + doe_id + ".xml"

# def get_study_base_dir(cfg_root):
#     study_home=xu.get_value_by_attr(cfg_root, 'study_base_dir')
#     if study_home is None:
#         study_home = os.getcwd()
#     if not os.path.isabs(study_home):
#         study_home = os.getcwd() + '/' + study_home
#     return study_home

def get_study_dir(cfg_root):
    study_dir=xu.get_value_by_attr(cfg_root, 'session_run_dir')
    if study_dir is None:
        study_dir = os.getcwd()
    if not os.path.isabs(study_dir):
        study_dir = os.getcwd() + '/' + study_dir
    return study_dir

def get_metadata_dir(cfg_root):
    return  xu.get_value_by_attr(cfg_root, 'metadata_dir')

# def gen_param_values_strided(elem_dict):
#     start_val = to_number(elem_dict['start_val'])
#     end_val = to_number(elem_dict['end_val'])
#     inc  = to_number(elem_dict['inc'])
#     cur = start_val
#     param_vals = []
#     while 1:
#         if cur > end_val:
#             break
#         param_vals.append(cur)
#         cur = cur+inc
#     return param_vals

def gen_param_values_strided(elem):
    start_val = to_number(xu.get_value_elem(elem, 'start_val', path_prefix='./'))
    end_val = to_number(xu.get_value_elem(elem, 'end_val', path_prefix='./'))
    inc  = to_number(xu.get_value_elem(elem, 'inc', path_prefix='./'))
    cur = start_val
    param_vals = []
    while 1:
        if cur > end_val:
            break
        param_vals.append(cur)
        cur = cur+inc
    return param_vals


def gen_param_values_enum_float(elem):
    value_elem = xu.get_elems(elem, 'values',  path_prefix='./', uniq=True)
    param_vals = xu.get_value_elems(value_elem, 'val')
    
    param_vals = [float(v) for v in param_vals]

    return param_vals

def gen_param_values_enum(elem):
    value_elem = xu.get_elems(elem, 'values',  path_prefix='./', uniq=True)
    param_vals = xu.get_value_elems(value_elem, 'val')
    param_vals = [int(v) for v in param_vals]
    return param_vals


def gen_param_values_singleton(elem):
    #value_elem = xu.get_elems(elem, 'value',  path_prefix='./', uniq=True)
    #param_vals = xu.get_value_elem(value_elem, 'value')
    param_val = xu.get_value_elem(elem, 'value', path_prefix='./')
    return [param_val] #suppose to return list
    
    

# def get_child_sweep_param(cfg_root):
#     elem = xu.get_elems(cfg_root, 'sweep', './')
#     if elem is None:
#         return [None, None, None,None]
#     if len(elem) == 0:
#         return [None, None, None, None]
#     elem = elem[0]
#     elem_dict = xu.XmlDictConfig(elem)
#     sweep_type=elem_dict['type']
#     param_values = globals()['gen_param_values_'+sweep_type](elem_dict)
#     return [elem, elem_dict['parameter'], param_values, elem_dict['abbrv']]

def get_child_sweep_param(cfg_root):
    elem = xu.get_elems(cfg_root, 'sweep', './')
    if elem is None:
        return [None, None, None,None]
    if len(elem) == 0:
        return [None, None, None, None]
    elem = elem[0]
    sweep_type = xu.get_value_elem(elem, 'type', path_prefix='./')
    parameter = xu.get_value_elem(elem, 'parameter', path_prefix='./')
    abbrv  = xu.get_value_elem(elem, 'abbrv', path_prefix='./')
    param_values = globals()['gen_param_values_'+sweep_type](elem)
    return [elem, parameter, param_values,  abbrv]

#def get_domain_sweep_iter(cfg_root):
def get_sweep_param_desc(param_elem):
    sweep_type = xu.get_value_elem(param_elem, 'type', path_prefix='./')
    parameter = xu.get_value_elem(param_elem, 'parameter', path_prefix='./')
    abbrv  = xu.get_value_elem(param_elem, 'abbrv', path_prefix='./')
    param_values = globals()['gen_param_values_'+sweep_type](param_elem)
    return [parameter, param_values, sweep_type, abbrv]


def get_sweep_param_flat(cfg_root):
    """
    SW: flat version of get_child_sweep_param_flat.
    Return lower bound and upper bound of parameter instead of actual list of
    values. This parameter bounds will be used for DOE sampling.
    """
    params = list()
    elems = xu.get_elems(cfg_root, 'sweep') 
    if elems is None:
        return None
    if len(elems) == 0:
        return None
    for elem in elems:
        parameter = xu.get_value_elem(elem, 'parameter', path_prefix='./')
        abbrv = xu.get_value_elem(elem, 'abbrv', path_prefix='./')
        lbound = xu.get_value_elem(elem, 'start_val', path_prefix='./')
        ubound = xu.get_value_elem(elem, 'end_val', path_prefix='./')
        params.append([parameter, abbrv, lbound, ubound])
    return params

# def get_replicate_flat(cfg_root):
#     doe_root = get_doe_cfg_root(cfg_root)
#     assert doe_root is not None
#     return xu.get_value_elem(doe_root, 'doe/replicate')

def get_num_samples(cfg_root):
    return int(xu.get_value_elem(cfg_root, 'doe/design/num_samples'))

def get_study_region(cfg_root):
    return xu.get_value_elem(cfg_root, 'region')

def get_epifast_num_nodes(cfg_root):
    '''
    parallelism size per epifast 
    compute node
    '''
    return xu.get_value_elem(cfg_root, 'epifast/num_nodes')


def get_indemics_max_threads(cfg_root):
    return xu.get_value_elem(cfg_root, 'indemics_server/max_threads')

def get_cfg_template_dir(cfg_root):
    template_dir = xu.get_value_elem(cfg_root, 'system/template_dir')
    if not os.path.isabs(template_dir):
        return module_dir+"/"+template_dir
    return template_dir
        

def get_dicex_base_dir(cfg_root):
    assert  'dicex_base_dir' in os.environ
    dicex_base_dir = os.environ['dicex_base_dir']
    return dicex_base_dir
    #return xu.get_value_elem(cfg_root, 'system/dicex_base_dir')

def get_espresso_base_dir(cfg_root):
    assert  'espresso_base_dir' in os.environ
    espresso_base_dir = os.environ['espresso_base_dir']
    return  espresso_base_dir
    #return xu.get_value_elem(cfg_root, 'system/dicex_base_dir')

def get_dicex_walltime(cfg_root):
    return xu.get_value_elem(cfg_root, 'data_engine/walltime')


def get_dbsession(cfg_root):
    return xu.get_value_elem(cfg_root, 'data_engine/dbsession')

def get_model_data_cfg_file(cfg_root):
    return xu.get_value_elem(cfg_root, 'model_data/edcfg_file')

def get_model_prefix(cfg_root):
    if xu.has_key(cfg_root, 'model_prefix'):
        return get_value_elem(cfg_root, 'model_prefix')
    else:
        return ""
    
def get_replicate_id(cfg_root):
    return xu.get_value_elem(cfg_root, 'replicate')

def get_model_dir(cfg_root):
    return xu.get_value_elem(cfg_root, 'model_dir')

def get_model_prefix(cfg_root):
    return xu.get_value_elem(cfg_root, 'model_prefix')





def get_intv_type(cfg_root):
    return xu.get_value_elem(cfg_root, 'intv_type')

def get_iql_template_loc(cfg_root):
    return xu.get_value_elem(cfg_root, 'iql_template')


def get_iql_helper_templates_elem(cfg_root):
    if xu.has_key(cfg_root, 'iql_helper_templates'):
        elem = xu.get_elems(cfg_root, 'iql_helper_templates', uniq=True)
        return elem
    return None


def get_epistudy_config_dir(cfg_root):
    return xu.get_value_elem(cfg_root, 'epistudy_config_dir')

def get_isis_area_name(cfg_root):
    return xu.get_value_elem(cfg_root, 'isis_area_name').lower()

def set_param_value_cfg(cfg_root, param_name, param_value):
    '''
    add a node with param and value 
    in the config root tree
    '''
    cfg_root.append(xu.gen_node(param_name, param_value))
    
def add_cfg_node(cfg_root, node_name, node_value):
    cfg_root.append(xu.gen_node(node_name, node_value)) ##TODO:revisit

def set_cfg_node(cfg_root, node_name, node_value):
    node_elem = xu.get_elems(cfg_root, node_name, uniq=True)
    if node_elem is None:
        print "set_cfg_node ", node_name, "not found"
    node_elem.text = node_value


def get_pre_intv_elem(cfg_root):
    pre_intv_elem = xu.get_elems(cfg_root, 'pre_intv_begin', uniq=True)
    return pre_intv_elem

def get_epifast_setting(cfg_root):
    epifast_elem = xu.get_elems(cfg_root, 'epifast', uniq=True)
    epifast_dict = xu.XmlDictConfig(epifast_elem)
    return epifast_dict

def get_offline_intervention_setting(cfg_root):
    # SW: utility function for getting offline intervention setting
    if xu.has_key(cfg_root, 'epifast/offline_interventions', path_prefix='.//'):
        offline_intervention_elem = xu.get_elems(cfg_root, 'offline_interventions', uniq=True)
        offline_intervention_dict = xu.XmlDictConfig(offline_intervention_elem)
        return offline_intervention_dict
    return None

def get_epifast_walltime(cfg_root):
    return xu.get_value_elem(cfg_root, 'epifast/walltime')

def get_epifast_host_type(cfg_root):
    return xu.get_value_elem(cfg_root, 'epifast/host_type')

def get_indemics_server_host_type(cfg_root):
    return xu.get_value_elem(cfg_root, 'indemics_server/cluster_qsub/host_type')



def get_epifast_seed(cfg_root):
    if xu.has_key(cfg_root, 'epifast/seed', path_prefix='.//'):
        seed=xu.get_value_elem(cfg_root, 'epifast/seed')
    seed = datetime.now()
    return seed   

def get_indemics_dir(cfg_root):
    return xu.get_value_elem(cfg_root, 'system/indemics_dir')

def get_epifast_diagnosis_settings(cfg_root):
    diagnosis_elem = xu.get_elems(cfg_root, 'epifast/Diagnosis', uniq=True)
    diagnosis_dict = xu.XmlDictConfig(diagnosis_elem)
    return diagnosis_dict

def get_simulation_duration(cfg_root):
    sim_duration = xu.get_value_elem(cfg_root, 'epifast/simulation_duration')
    return int(sim_duration)
def get_intervention_prescription_config_file(cfg_root):
    ip_fn = xu.get_value_elem(cfg_root, 'intervention_prescription_config_file')
    return ip_fn


    
def get_socnet_path_template(cfg_root):
    return xu.get_value_elem(cfg_root, 'model/socnet_path_template')

def get_socnet_path(cfg_root):
    return xu.get_value_elem(cfg_root, 'model/socnet_path')

def get_edcfg_root(cfg_root):
    return xu.get_elems(cfg_root, 'edcfg', uniq=True)

def get_epifast_bin(cfg_root):
    elem = xu.get_elems(cfg_root, 'epifast/epifast_bin', uniq=True)
    if elem is None:
        default_root = xu.read_file(default_config_fn)
        return xu.get_value_elem(default_root, 'epifast_bin')
    return elem.text


def get_mpi_module(cfg_root):
    elem = xu.get_value_elem(cfg_root, 'epifast/mpi_module')
    return elem


def get_indemics_server_job_params(cfg_root=None):
    if xu.has_key(cfg_root, 'indemics_server/cluster_qsub', path_prefix='.//'):
        return [xu.get_value_by_attr(cfg_root, 'indemics_server/cluster_qsub/group_list'), xu.get_value_by_attr(cfg_root, 'indemics_server/cluster_qsub/qsub_q'),xu.get_value_by_attr(cfg_root, 'data_engine/cluster_qsub/qsub_ppn')]
    else:
        #return default qsub
        return ['sfx', 'dedicated_q', 12]


def get_dbengine_job_params(cfg_root=None):
    if xu.has_key(cfg_root, 'data_engine/cluster_qsub', path_prefix='.//'):
        return [xu.get_value_by_attr(cfg_root, 'data_engine/cluster_qsub/host_type'), xu.get_value_by_attr(cfg_root, 'data_engine/cluster_qsub/group_list'), xu.get_value_by_attr(cfg_root, 'indemics_server/cluster_qsub/qsub_q'), xu.get_value_by_attr(cfg_root, 'data_engine/cluster_qsub/qsub_ppn')]
    else:
        #return default qsub
        print "ec: returning default for dbhost"
        return ['standard', 'sfx', 'dedicated_q', 12]


def get_iql_template_genmod(cfg_root):
    return xu.get_value_elem(cfg_root, 'iql_template_genmod')

#def get_subpop_elems(cfg_root):
#    return

def flat_sweep_trigger(cfg_root):
    doe_root = get_doe_cfg_root(cfg_root)
    if doe_root is None:
        return False
    doe_type = xu.get_value_elem(doe_root, 'doe/doe_type')
    assert(doe_type!=None)
    return doe_type=="FULL_FACT"

# def get_doe_cfg_root(cfg_root):
#     doe_cfg_fn = xu.get_value_elem(cfg_root, 'doe', path_prefix='//')
#     if doe_cfg_fn is None:
#         return None
#     doe_cfg_root = xu.read_file(doe_cfg_fn)
#     return doe_cfg_root
