import os
import epistudy_cfg as ec
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as deu

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
cfg_root = ec.read_epistudy_cfg(cfg_file)
dbsession = ec.get_dbsession(cfg_root)
dicex_base_dir = ec.get_dicex_base_dir(cfg_root)

deu.update_replicate_intv_files(cfg_root)

#########################################
###TODO: Also update the simdm.conf file
########################################
