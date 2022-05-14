import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu
import versa_impl as vi
import os
from string import Template
import launch_epifast_jobs as lej
import launch_epifast_jobs_throttled as lejt
import subprocess
import utilities
import xmlutils as xu
#TODO: Check if db is up
module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_fn = sys.argv[1]
cfg_root = ec.read_epistudy_cfg(sys.argv[1])
dbsession = ec.get_dbsession(cfg_root)
dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
host = pgu.get_db_host(dbsession)
port=pgu.get_db_port(dbsession)
conn = pgu.get_conn_handle(host=host, port=port)
wd = os.getcwd()
cluster_name  = utilities.get_cluster_name()
doe_iter = deu.get_doe_iter(cfg_root)
num_total_replicates = utilities.count_iterable(doe_iter)
if num_total_replicates > 300: 
    print "num_total_replicates ", num_total_replicates
    key_code = raw_input("press any key to continue or type ctrl-c")


remote_cmd = Template('''ssh $host ". $dicex_base_dir/dicex_${cluster_name}.sh; cd $wd; $module_dir/remote_add_study.sh $cfg_fn"''').substitute(locals())
subprocess.call(remote_cmd, shell=True)
launcher_type = 'standard'
if xu.has_key(cfg_root, 'doe/launcher_type', path_prefix='.//'):
    launcher_type = xu.get_value_by_attr(cfg_root, 'doe/launcher_type')
if launcher_type == 'standard':
    launcher = lej
if launcher_type == 'throttled':
    launcher = lejt
launcher.launch_epifast_jobs(cfg_root)
