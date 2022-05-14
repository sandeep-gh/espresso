import os
import subprocess
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as dej

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
cfg_root = ec.read_epistudy_cfg(cfg_file)
dbsession = ec.get_dbsession(cfg_root)
dicex_base_dir = ec.get_dicex_base_dir(cfg_root)

def report_client_dir(cfg_root, replicate_desc, replicate_dir, param_root):
    print replicate_desc


dej.vary_param(cfg_root, rep_method=report_client_dir)
