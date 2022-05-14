import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu
import versa_impl as vi
import os
from string import Template
import launch_epifast_jobs as lej
import subprocess
import utilities

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
cluster_name = utilities.get_cluster_name()


remote_cmd = Template('''ssh $host ". $dicex_base_dir/dicex_${cluster_name}.sh; cd $wd; $module_dir/remote_load_model.sh $cfg_fn"''').substitute(locals())
subprocess.call(remote_cmd, shell=True)



