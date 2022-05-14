import os
import subprocess
import epistudy_cfg as ec
import dicex_pgsa_impl as dpi
import sys
import launch_epifast_jobs as lej
import dicex_epistudy_utils as dej

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
if os.path.isfile(cfg_file):
    cfg_root = ec.read_epistudy_cfg(cfg_file)
    dbsession = ec.get_dbsession(cfg_root)
    dicex_base_dir = ec.get_dicex_base_dir(cfg_root)
    indemics_jobid = dej.get_indemics_qsub_jobid(dbsession)

    if indemics_jobid is not None:
        subprocess.call("qdel "+indemics_jobid, shell=True)
    dpi.removejob(dbsession)
else:
      print "no file ", cfg_file, " found...exiting"


