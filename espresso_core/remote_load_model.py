import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu
import versa_impl as vi
import add_study_utils as asu

#TODO: Check if db is up
cfg_root = ec.read_epistudy_cfg(sys.argv[1])
dbsession = ec.get_dbsession(cfg_root)
host = pgu.get_db_host(dbsession)
port=pgu.get_db_port(dbsession)
conn = pgu.get_conn_handle(host=host, port=port)
vi.init(dbsession)
##############################################
###builds simdb.conf and simdm.conf  launch_indemics_server.sh
###############################################
deu.load_model_data(cfg_root)


