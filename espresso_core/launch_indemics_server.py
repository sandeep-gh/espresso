import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu

#TODO: Check if db is up
cfg_root = ec.read_epistudy_cfg(sys.argv[1])
dbsession = ec.get_dbsession(cfg_root)
port=pgu.get_db_port(dbsession)
conn = pgu.get_conn_handle(port)
cursor=conn.cursor()
deu.init(cfg_root)
deu.update_replicate_intv_files(cfg_root)
deu.start_indemics_server(cfg_root)
conn.close()

