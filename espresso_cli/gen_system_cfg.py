#!/apps/packages/math/epd/7.3-1/bin/python
import sys
import argparse
import utilities

import gen_system_cfg_impl as gsci

parser = argparse.ArgumentParser()
parser.add_argument("--id", help="name of the spresso session", nargs='?', const=None)
parser.add_argument("--dicex_dir", help="specify dicex base dir", nargs='?', const=None)
parser.add_argument("--devel",  action='store_true', help="use the development branch")
parser.add_argument("--production",  action='store_true', help="use the tested branch")

#non essential 
parser.add_argument("--study_run_dir",  help="the study run directory", nargs='?', const=None)

parser.add_argument("--db_host_type",  choices = ['standard', 'largemem'], help="compute node type for db (standard or large memory)", nargs='?', const=None)
parser.add_argument("--db_walltime_hours",  help="walltime for database job", nargs='?', const=None)
parser.add_argument("--largemem", help="use largemem nodes for db and indemics server",action='store_true') 
parser.add_argument("--indemics_host_type",  choices = ['standard', 'largemem'], help="compute node type for indemics_server (standard or large memory)", nargs='?', const=None)
parser.add_argument("--indemics_walltime_hours",  help="walltime for indemics server job", nargs='?', const=None)
parser.add_argument("--walltime_hours",  help="walltime for both dbhost and indemics server", nargs='?', const=None)

parser.add_argument("--nostart",  help="start the spresso session", action='store_true')
parser.add_argument("--cleanup",  help="start the spresso session", action='store_true')



args = parser.parse_args()

if args.dicex_dir:
    gsci.pvar_dicex_dir = args.dicex_dir


if args.id:
    gsci.pvar_session = args.id 
else:
    session_mod = utilities.get_last_file_by_pattern("dbsession*.py")
    if session_mod is None:
        print "No session found..."
        sys.exit()
    gsci.pvar_session = session_mod[10:-22] #this is dangerous

if args.devel:
    gsci.pvar_devel = "devel"

if args.production:
    gsci.pvar_devel = ""

if args.study_run_dir:
    gsci.pvar_study_run_dir = args.study_run_dir




if args.db_host_type:
    gsci.pvar_db_host_type = args.db_host_type

if args.db_walltime_hours:
    gsci.pvar_db_job_walltime = args.db_walltime_hours



if args.indemics_host_type == 'largemem':
    gsci.pvar_indemics_server_host_type = args.indemics_host_type




if args.indemics_walltime_hours:
    gsci.pvar_indemics_server_job_walltime = args.indemics_server_job_walltime

if args.walltime_hours:
    gsci.pvar_indemics_server_job_walltime = args.walltime_hours
    gsci.pvar_db_job_walltime = args.walltime_hours


if args.largemem:
    gsci.pvar_db_host_type = 'largemem'
    gsci.pvar_indemics_host_type = 'largemem'

if args.nostart:
    gsci.pvar_nostart = True

if args.cleanup:
    gsci.pvar_cleanup = True
    gsci.cleanup()
else:
    gsci.launch()
