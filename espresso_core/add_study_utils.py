import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import socket
from string import Template

def update_intv_files_iter(replicate_info):
    update_intv_files(replicate_info.cfg_root, replicate_info.abbrv_rep_desc, replicate_info.abbrv_rep_dir)


def update_intv_files(cfg_root, replicate_desc, replicate_dir):
    '''update the intervention file with the indemics server ip address
       this is a variation of rep_method=update_intv_files of deu module.
       At some point they need to be refactored.
       we actually need a principled data organization for bookkeeping for where the 
       indemics servers are being launched. We could use XML-in-database as well
    '''
    dbsession = ec.get_dbsession(cfg_root)
    indemics_server_hostname=deu.get_indemics_server_hostname(dbsession)
    indemics_server_ipaddr=socket.gethostbyname(indemics_server_hostname)
    efdir=replicate_dir + '/epifast_job'
    intv_config_loc = efdir+'/Intervention'
    intv_config_template_loc = intv_config_loc + '.template'
    intv_config_template_str = open(intv_config_template_loc, 'r').read()
    intv_config_template = Template(intv_config_template_str)
    a = locals()
    b = globals()
    a.update(b)
    intv_config_str = intv_config_template.substitute(a)
    intv_cfg_fh = open(intv_config_loc, 'w')
    intv_cfg_fh.write(intv_config_str)
    intv_cfg_fh.close()
