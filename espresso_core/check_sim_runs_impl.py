import os
import subprocess
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as dej
import replicate_analysis_utils as rau
import versa_api as vapi
import versa_utils as vu
import xmlutils as xu
import  collections
import dicex_epistudy_utils as deu
from itertools import chain, imap

num_failed = 0
total_replicates = 0
num_runs = 0
model_base_name='_day_tracker'
session = None
num_sim_days = None
model_selector  = []

def check_run_status(replicate_info):
    global num_failed
    global model_base_name
    global num_runs
    global total_replicates
    cfg_root = replicate_info.cfg_root
    replicate_desc = replicate_info.abbrv_rep_desc
    replicate_dir = replicate_info.abbrv_rep_dir
    num_runs = num_runs+1
    has_failed = True
    #turning off ef_err test because mpiexec is throwing warning in there
    #ef_err_fn =  replicate_dir + "/epifast_job/ef_err.txt"
    #if os.stat(ef_err_fn).st_size == 0: 
    rep_model = rau.get_replicate_model_obj(replicate_desc, model_base_name)
    num_days = vapi.cardinality(session, rep_model)

    total_replicates = total_replicates + 1
    if num_days == num_sim_days or (num_days + 5) > num_sim_days + 1: #simulation finished till completion #TODO: fix num of days 
        has_failed = False
        model_selector.append(True)
    else:
        model_selector.append(False)

    if has_failed:
        num_failed  = num_failed + 1
        print "failed: ", replicate_desc 

#TODO: how to do callback with additional parameters
def check_sim_runs_impl(cfg_file):
    global num_failed
    global session
    global num_sim_days
    num_failed = 0
    cfg_root = ec.read_epistudy_cfg(cfg_file)
    dbsession = ec.get_dbsession(cfg_root)
    session = vu.build_session(dbsession, conn_remote=True)
    dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
    num_sim_days = ec.get_simulation_duration(cfg_root) 
    doe_iter = deu.get_doe_iter(cfg_root)
    collections.deque(imap(check_run_status,doe_iter), maxlen= 0) #call prepare_config_files for each cfg of the doe
    return [total_replicates, num_failed, model_selector]

 
def run(cfg_file):
    '''return 0 if no runs were successful, 1 otherwise
    '''
    
    num_failed = check_sim_runs_impl(cfg_file)
    if num_failed == num_runs:
        return 0
    return 1
