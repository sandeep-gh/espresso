from string import Template
import os
import subprocess
import sys
from itertools import tee, izip
import os 
import xmlutils as xu
import utilities 


#should be part of utils package
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)
 
module_dir=os.path.dirname(os.path.realpath(__file__))

def merge_xml(xml1_path, xml2_path, xmlo_path):
    global module_dir
    with open("tmp.xml", "w+") as fh:
        fh.write(Template("""<?xml version="1.0"?>
<merge xmlns="http://informatik.hu-berlin.de/merge">
  <file1>${xml1_path}</file1>
  <file2>${xml2_path}</file2>
</merge>""").substitute(locals()))
    a = locals()
    a.update(globals())
    merge_cmd = Template("xsltproc ${module_dir}/merge.xslt tmp.xml > ${xmlo_path}").substitute(locals())
    subprocess.call(merge_cmd, shell=True)

#read the top level
pvar_session_run_dir = os.getcwd()
pvar_dicex_dir=utilities.get_dicex_base_dir()
pvar_devel="devel"
pvar_session="spresso_session"
pvar_db_job_group = 'sfx'
pvar_db_job_queue = 'dedicated_q'
pvar_db_job_ppn = '8'
pvar_db_job_walltime = '4'
pvar_db_host_type = 'standard'
pvar_config_base_dir = None

pvar_indemics_server_job_group = 'sfx'
pvar_indemics_server_job_queue = 'dedicated_q'
pvar_indemics_server_job_ppn = '8'
pvar_indemics_server_job_walltime = '2'
pvar_indemics_server_host_type = 'standard'

pvar_epifast_walltime='4'
pvar_model_base_dir='/sfxgroups/NDSSL/espresso_model_data'
pvar_simulation_duration='300'
study_directives = ""


pvar_nostart = False
pvar_cleanup = False

def launch():
    global pvar_session
    pvar_session = pvar_session + "_session" #because this is the convention
    #variables are defined in global space

    #set espresso beans directory

    if 'espresso_beans_base_dir_path' in os.environ:
        pvar_config_base_dir = os.environ['espresso_beans_base_dir_path']
    else:
        if 'dicex_base_dir' in os.environ:
            pvar_config_base_dir = os.environ['dicex_base_dir'] + '/espresso_all/espresso_beans/'
        else:
            print "dicex/versa/espresso enviorment not active and espresso beans path not set"
            print "most likely you need to execute /home/pgxxc/dicex.sh"
            print "exiting..."
            assert False

    #use system_config_xml to find the right queue names
    [pvar_db_job_group, pvar_db_job_queue, pvar_db_job_ppn] = utilities.get_qsub_queue_args(pvar_db_host_type)
    [pvar_indemics_server_job_group,  pvar_indemics_server_job_queue, pvar_indemics_server_job_ppn] = utilities.get_qsub_queue_args(pvar_indemics_server_host_type)

    config_key_value_dictionary = dict(globals(), **locals())
    #create common header here
    common_header = Template(open(module_dir + "/common_header.xml.template").read()).substitute(config_key_value_dictionary)
    config_key_value_dictionary = dict(globals(), **locals())

    header_xml = Template(open(module_dir + "/system_header.xml.template").read()).substitute(config_key_value_dictionary)

    #create system xml
    system_xml_fn = module_dir + "/system_default.xml"
    system_xml = header_xml + open(system_xml_fn).read()


    work_dir = utilities.build_work_dir()

    with open(pvar_session + ".xml", "w+") as fh: 
        fh.write(system_xml)


    with open(pvar_session + "_common.xml", "w+") as fh:
        fh.write(common_header)


    if pvar_nostart is False:
        subprocess.call("setup.sh " + pvar_session + ".xml", shell=True)


def cleanup():
    global pvar_session
    pvar_session = pvar_session + "_session" #because this is the convention
    cluster_name = utilities.get_cluster_name()
    subprocess.call(". " + pvar_dicex_dir + "/dicex_" + cluster_name + ".sh;" + "epistudy_cleanup.sh " + pvar_session + ".xml", shell=True)
