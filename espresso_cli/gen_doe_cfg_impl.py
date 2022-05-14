#!/apps/packages/math/epd/7.3-1/bin/python
from string import Template
import os
import subprocess
import sys
from itertools import tee, izip
import xmlutils as xu
import utilities 

#should be part of utils package
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
 
module_dir=os.path.dirname(os.path.realpath(__file__))

#read the top level
pvar_sid=None
pvar_study_run_dir = "./"
pvar_scenario="basecase"
pvar_doe_cfg_suffix = "default"
pvar_cfg_out = "spresso_doe.xml"
pvar_model_id = None
pvar_epifast_walltime='4'
pvar_simulation_duration='30'
study_directives = ""
pvar_study_args = None
pvar_norun = False
pvar_num_replicates=2
pvar_domain_param_cfg_fn = None
pvar_ef_cfg_fn = module_dir + "/ef_cfg_default.xml"
pvar_epifast_host_type = 'standard'
pvar_epifast_num_nodes = '4'
pvar_epifast_exec_path=None
pvar_mpi_module = None
pvar_doe_type = 'full_factorial'
pvar_lhs_num_samples = 5
pvar_labeling = 'cell_rep_lexicograhic'
pvar_launcher_type ='standard'
pvar_setup_dry_run=""
pvar_epifast_dry_run="0"
pvar_dry_run_iconductor=""

def run():

    global pvar_cfg_out
    assert pvar_sid is not None
    assert pvar_model_id is not None
    pvar_cfg_out = "sid_" + pvar_sid + ".xml"
    if os.path.isfile(pvar_cfg_out):
        print pvar_cfg_out, " already exists. Espresso will not overwrite existing config file."
        print "Choose new identifier or remove ", pvar_cfg_out, " from this directory"
        print "exiting.."
        sys.exit()
        
#     if pvar_study_args is not None:
#         study_directive_fn  = module_dir + "/" + pvar_intv_type + "/" + "study_header_directives.xml"
#         study_arguments_key_value_list = args.study_args.split()
#         study_arg_dict = {}
#         for key, value in pairwise(study_arguments_key_value_list):
#             study_arg_dict['pvar_' + key]=value

#         study_arg_dict['pvar_sid'] = pvar_sid
#         study_directives = Template(open(study_directive_fn).read()).substitute(study_arg_dict)
    


    model_root = xu.read_file(pvar_model_id + "_model.xml")
    pvar_session = xu.get_value_elem(model_root, 'session')
    pvar_study = xu.get_value_elem(model_root, 'study')
    pvar_region = xu.get_value_elem(model_root, 'region')
    model_dir = xu.get_value_elem(model_root, 'model_dir')
    study_config_dir = xu.get_value_elem(model_root, 'epistudy_config_dir')

    [pvar_mpi_module, pvar_epifast_exec_path] = utilities.get_epifast_exec_path()
    common_header = open(pvar_session + "_common.xml").read()
    common_model_header = open("common_" + pvar_model_id + "_model.xml").read()
    config_key_value_dictionary = dict(globals(), **locals())
    header_xml = Template(open(module_dir + "/doe_header.xml.template").read()).substitute(config_key_value_dictionary)


    #create base xml
    cell_cfg_base_fn  = module_dir + "/"  + "cell_cfg_base.xml" 
    cell_cfg_base_xml_template = header_xml + open(cell_cfg_base_fn).read()

    #study schema xml
    study_schema_xml = ""
    study_schema_xml_fn = study_config_dir + "/study_schema.xml"
    if os.path.isfile(study_schema_xml_fn):
        study_schema_xml = open(study_schema_xml_fn).read()
        
    
    #epifast config
    ef_cfg_xml  =  open(pvar_ef_cfg_fn).read() #the default config
    ef_cfg_fn = study_config_dir + "/ef_cfg.xml" 
    if os.path.isfile(ef_cfg_fn):
        ef_cfg_xml = open(ef_cfg_xml).read()     #use study config if available
    ef_cfg_fn = study_config_dir + "/ef_cfg.xml." + pvar_scenario
    if os.path.isfile(ef_cfg_fn):
        ef_cfg_xml = open(ef_cfg_fn).read() #override with scenario ef config


    #replcate tables xml
    replicate_tables_fn = study_config_dir + "/replicate_tables.xml." + pvar_scenario
    replicate_tables_xml = ""
    if os.path.isfile(replicate_tables_fn):
        replicate_tables_xml =  open(replicate_tables_fn).read()

    #study param xml 
    study_params_xml = ""
    study_param_fn = study_config_dir + "/study_params.xml." + pvar_scenario
    if os.path.isfile(study_param_fn):
        study_params_xml =  open(study_param_fn).read()

    #domain param
    doe_domain_param_xml = ""
    global pvar_domain_param_cfg_fn
    if pvar_domain_param_cfg_fn is None:
        pvar_domain_param_cfg_fn = study_config_dir + "/doe_domain_param.xml"
    if os.path.isfile(pvar_domain_param_cfg_fn):
        doe_domain_param_xml = open(pvar_domain_param_cfg_fn).read()
        #see if there is xslt for the scenario -- abandon for now. doing xslt stuff manually. 
        #pvar_domain_param_xsl_fn = study_config_dir + "/doe_domain_param.xsl." + pvar_scenario
        #if os.path.isfile(pvar_domain_param_xsl_fn):
            
        #if filter_doe_domain_param_regular_expression:
        #doe_domain_param_xml = xu.filter_elems(doe_domain_param_xml, filter_doe_domain_param_regular_expression, elem_type='sweep', tag='label')

    #place hook for post setup config
    post_setup_config_xml = ""
    post_setup_config_fn = study_config_dir + "/post_setup_config.xml." + pvar_scenario
    if os.path.isfile(post_setup_config_fn):
        post_setup_config_xml = open(post_setup_config_fn).read()


    cell_cfg_base_xml = Template(cell_cfg_base_xml_template).substitute(replicate_tables_xml= replicate_tables_xml, doe_domain_param_xml=doe_domain_param_xml, post_setup_config_xml=post_setup_config_xml, study_params_xml=study_params_xml, ef_cfg_xml=ef_cfg_xml, study_schema_xml=study_schema_xml)
    
    with open(pvar_cfg_out, "w+") as fh: 
        fh.write(cell_cfg_base_xml)


    if pvar_norun is False:
        subprocess.call("add_study.sh " + pvar_cfg_out, shell=True)
        print "simulations launched; wait for them to be finished and then  run analysis"

