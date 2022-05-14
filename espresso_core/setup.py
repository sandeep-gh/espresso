import os
import sys
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as dej
import xmlutils as xu
import utilities

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
cfg_root = ec.read_epistudy_cfg(cfg_file)
dbsession = ec.get_dbsession(cfg_root)
cluster_name = utilities.get_cluster_name()
#dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
assert  'dicex_base_dir' in os.environ
dicex_base_dir = os.environ['dicex_base_dir']
dpi.postdb_start_script= module_dir + '/run_postdb.sh ' + dicex_base_dir + ' ' + cluster_name + " " + cfg_file #TODO: this should be part of the argument list
dicex_walltime = ec.get_dicex_walltime(cfg_root)
[host_type, qsub_group_list, qsub_q, qsub_ppn] =  ec.get_dbengine_job_params(cfg_root)
print "setup = ", host_type
launch_status = dpi.launchdb(dbdesc=dbsession, host_type=host_type, walltime_hours = dicex_walltime) ##waits until the database has started

if launch_status == 0:
   print "failed db launch..aborting now"
   sys.exit()
    
#configure and launch indemics server
dej.launch_indemics_server_job(cfg_file, cfg_root) ###waits untils indemics server is launched
#lej.launch_epifast_jobs(cfg_root)
print "Data engine  and indemics server launched"





