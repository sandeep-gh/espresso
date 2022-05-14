import xmlutils as xu
import epistudy_cfg as ec
import versa_core.relational as re
import versa_core.utils as vu
import utilities
import os

module_dir=os.path.dirname(os.path.realpath(__file__))


def get_intervention_param_values(cfg_root):
    intervention_elem = xu.get_elems(cfg_root, 'interventions', uniq=True)
    intervention_dict= {} #return empty dictionary if no intervention is defined
    if intervention_elem is not None:
        intervention_dict = xu.XmlDictConfig(intervention_elem)
    return intervention_dict


def prepare_intervention_param_value(cfg_root):
    interventions = get_intervention_param_values(cfg_root) #each intervention statement has block for param-values 
    #interventions is a recursive key-value pair object -- which is totally unnecessary -- but carry along
    all_intv_dict = {}
    for intv_set_key in interventions.keys():
        intv_dict = {}
        assert('iql_key' in interventions[intv_set_key].keys())
        iql_key = interventions[intv_set_key]['iql_key']
        for intv_attr in [x for x in interventions[intv_set_key].keys() if x != 'iql_key']:
            intv_attr_val = interventions[intv_set_key][intv_attr]
            intv_dict[iql_key + '_' + intv_attr] = intv_attr_val
        all_intv_dict.update(intv_dict)
    return all_intv_dict #we now have all intervention parameters and their values (i0_class, i0_efficacy and so on)


def get_iql_param_values(cfg_root):

    if xu.has_key(cfg_root, 'epistudy/iql_parameters', path_prefix='.//'):
        iql_param_elem = xu.get_elems(cfg_root, 'iql_parameters', uniq=True)
        iql_param_dict = xu.XmlDictConfig(iql_param_elem)
        return iql_param_dict
    else:
        return None


    
def prepare_study_param_values(cfg_root):
    if xu.has_key(cfg_root, 'doe/study_params', path_prefix='.//'):
        study_params_elem = xu.get_elems(cfg_root, 'doe/study_params', uniq=True)
        print "study param dict = ", xu.XmlDictConfig(study_params_elem)
        return xu.XmlDictConfig(study_params_elem)
    return {}

def prepare_continious_implict_study_param_values(cfg_root, study_param_dict=None):
    dynamic_param_val_dict = {}
    if xu.has_key(cfg_root, 'doe/dynamic_study_params', path_prefix='.//'):
        study_params_elem = xu.get_elems(cfg_root, 'doe/dynamic_study_params', uniq=True)
        for dvar in study_params_elem:
            var_name = dvar.tag
            var_value_expr = Template(dvar.text).substitute(study_param_dict)
            var_value = eval(var_value_expr)
            dynamic_param_val_dict[var_name]  = var_value
    return dynamic_param_val_dict


def load_continious_parameters(session, cfg_root, replicate_desc):
    '''
    returns a dictionary where key is the continious parameter
    and value is the module that evaluates the value of the continious 
    parameter
    '''
    
    if not xu.has_key(cfg_root, 'doe/continious_params', path_prefix='.//'):
        return None

    module_dir = ec.get_epistudy_config_dir(cfg_root)
    continious_params_elem =  xu.get_elems(cfg_root, 'doe/continious_params', uniq=True)
    continious_param_value_dict = dict()
    for cpe in continious_params_elem:
            var_name = cpe.tag
            var_module_name  = xu.get_value_by_attr(cpe, 'module')
            print "var_module_name = ", var_module_name
            var_module = utilities.import_module(module_dir=module_dir, module_name=var_module_name)
            continious_param_value_dict[var_name] = var_module
    return continious_param_value_dict

def load_setup_parameters(session, cfg_root, replicate_desc):
    if not xu.has_key(cfg_root, 'study_schema', './/'):
        return None
    
    study_schema_elem =  xu.get_elems(cfg_root, 'study_schema', uniq=True)
    setup_param_val_dict = dict()
    #get pop size
    agent_model = xu.get_value_by_attr(study_schema_elem, 'agent_model')
    region = ec.get_study_region(cfg_root)
    [agent_rmo]  = vu.load_rmos([region + "_" + agent_model])
    setup_param_val_dict['region_popsz'] = re.cardinality(session, agent_rmo)
    return setup_param_val_dict
 
