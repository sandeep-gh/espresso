import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu

#TODO: Check if db is up
cfg_root = ec.read_epistudy_cfg(sys.argv[1])
dbsession = ec.get_dbsession(cfg_root)
port=pgu.get_db_port(dbsession)
conn = pgu.get_conn_handle(port=port)
cursor=conn.cursor()
cursor.execute("create table player (pid int ,  name varchar,  pwd varchar, admin varchar)")
cursor.execute("Insert into player(pid, name, pwd, admin) values (1, 'ndssl', 'ndssl', 'yes')")
conn.commit()
deu.init(cfg_root)
##############################################
###builds simdb.conf and simdm.conf  launch_indemics_server.sh
###############################################
deu.prepare_indemics_server_cfg(cfg_root) 
deu.load_model_data(cfg_root)
deu.create_replicate_configurations(cfg_root) #launches the epifast job
conn.close()
