#!/apps/packages/math/epd/7.3-1/bin/python
import utilities
from string import Template
import os
import subprocess
import sys
from itertools import tee, izip

import xmlutils as xu

#should be part of utils package
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
 
module_dir=os.path.dirname(os.path.realpath(__file__))

#read the top level
pvar_region="Miami"
pvar_study_run_dir = "./"
pvar_model_base_dir="/sfxgroups/NDSSL/espresso_model_data/"
pvar_session = "spresso"
pvar_model_id = None
pvar_cfg_out = None #"spresso_model.xml"
pvar_devel="devel"
pvar_study="tlc_v2"
pvar_scenario="basecase"
pvar_system_cfg="system.xml"
pvar_noload = False

def launch():
    global pvar_cfg_out
    #source global scale variables
    assert(pvar_model_id is not None)
    pvar_cfg_out = pvar_model_id + "_model.xml"
    session_root = xu.read_file(pvar_session + "_session.xml")

    pvar_session_run_dir = xu.get_value_elem(session_root, 'session_run_dir')
    config_base_dir = xu.get_value_elem(session_root, 'epistudy_config_base_dir')
    common_header = open(pvar_session + "_session_common.xml").read()
    config_key_value_dictionary = dict(globals(), **locals())
    common_model_header = Template(open(module_dir + "/common_model_header.xml.template").read()).substitute(config_key_value_dictionary)
    config_key_value_dictionary = dict(globals(), **locals())
    header_xml = Template(open(module_dir + "/model_header.xml.template").read()).substitute(config_key_value_dictionary)

    #create cell xml
    #create system xml
    model_xml_fn = module_dir + "/model_default.xml"
    model_xml = header_xml + open(model_xml_fn).read()
    work_dir = utilities.build_work_dir()

    #with open(work_dir + "/model.xml", "w+") as fh:
    #    fh.write(model_xml)
    with open(pvar_cfg_out, "w+") as fh:
        fh.write(model_xml)

    with open("common_" + pvar_cfg_out, "w+") as fh:
        fh.write(common_model_header)

    #xu.merge_xml(pvar_session + "_session.xml", work_dir + "/model.xml", pvar_cfg_out)

    #create replicate table xml
    study_config_dir = config_base_dir + "/" + pvar_study
#     replicate_tables_fn = study_config_dir + "/replicate_tables.xml." + pvar_scenario
#     replicate_tables_xml = header_xml + open(replicate_tables_fn).read()
#     replicate_table_out_fn = pvar_session_run_dir  + "/" + pvar_model_id + "_replicate_tables.xml"
#     with open(replicate_table_out_fn, "w") as fh:
#         fh.write(replicate_tables_xml)

    
    if pvar_noload is False:
        subprocess.call("load_model.sh " + pvar_cfg_out, shell=True)




