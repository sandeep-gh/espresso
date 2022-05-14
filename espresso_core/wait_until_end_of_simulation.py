import os
import subprocess
from string import Template
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as deu
import replicate_analysis_utils as rau

import versa_api as vapi
import versa_utils as vu
import xmlutils as xu
import  collections
from itertools import chain, imap
import  utilities

num_failed = 0
session = None
num_sim_days = None
status_file_template=Template('''job_rep_${replicate_desc}_status.txt''')
def check_run_status(replicate_info):
    
    global num_failed
    global model_base_name
    cfg_root = replicate_info.cfg_root
    replicate_desc = replicate_info.abbrv_rep_desc
    replicate_dir = replicate_info.abbrv_rep_dir
    status_file = replicate_dir + "/" + status_file_template.substitute(locals())
    print "waiting for ", status_file
    subprocess.call('wait_for_file.sh ' + status_file, shell=True)
    print "file is ready"

#TODO: how to do callback with additional parameters
def run(cfg_file):
    global session
    global num_sim_days
    cfg_root = ec.read_epistudy_cfg(cfg_file)
    dbsession = ec.get_dbsession(cfg_root)
    session = vu.build_session(dbsession, conn_remote=True)
    dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
    num_sim_days = ec.get_simulation_duration(cfg_root) 

    doe_iter = deu.get_doe_iter(cfg_root)
    collections.deque(imap(check_run_status,doe_iter), maxlen= 0) #call prepare_config_files for each cfg of the doe
    return num_failed

if len(sys.argv) > 1:
    cfg_file=sys.argv[1]
else:
    cfg_file = utilities.get_last_file_by_pattern("sid_[0-9]*.xml")
run(cfg_file )
