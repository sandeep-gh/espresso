import os
import subprocess
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as dej
from string import Template

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
cfg_root = ec.read_epistudy_cfg(cfg_file)
dbsession = ec.get_dbsession(cfg_root)
dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
num_failed = 0

def get_job_walltime(cfg_root, replicate_desc, replicate_dir, param_root):
    stat_fn =  replicate_dir + Template("/job_rep_${replicate_desc}_status.txt").substitute(locals())
    assert os.path.isfile(stat_fn) 
    assert os.stat(stat_fn).st_size != 0
    wall_time = open(stat_fn).read()
    print replicate_desc, " ", wall_time


dej.vary_param(cfg_root, rep_method=get_job_walltime)

