#!/apps/packages/math/epd/7.3-1/bin/python
import argparse
import gen_model_cfg_impl as gmci
import utilities
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--id", help="identifier for the model", nargs='?', const=None)
parser.add_argument("--session", help="name of the session", nargs='?', const=None)
parser.add_argument("--region", help="specify region (Miami, Chicago)", nargs='?', const=None)
parser.add_argument("--dicex_dir", help="specify dicex base dir", nargs='?', const=None)
#parser.add_argument("--output", help="name of the config file", nargs='?', const=None)
parser.add_argument("--devel",  action='store_true', help="use the development branch")
parser.add_argument("--production",  action='store_true', help="use the tested branch")
parser.add_argument("--study", help="study type (tlc_v2, tidewater)", nargs='?', const=None)
parser.add_argument("--noload",  help="start the spresso session", action='store_true')
#parser.add_argument("--scenario", help="specify scenario (basecase, scene1, etc.)", nargs='?', const=None)

#non essential 
parser.add_argument("--study_run_dir",  help="the study run directory", nargs='?', const=None)

args = parser.parse_args()


if args.region:
    gmci.pvar_region = args.region #TODO: when do we need args.region.title() --we shouldn't need to 
else:
    print "specify a region over which to run the study (e.g. miami, seattle, and so on)"
    sys.exit()

if args.study:
    gmci.pvar_study = args.study
else:
    print "specify a (epi) study  (e.g. block, d1, and so on)"

if args.dicex_dir:
    gmci.pvar_dicex_dir = args.dicex_dir

if args.session:
    gmci.pvar_session = args.session
else:
    session_mod = utilities.get_last_file_by_pattern("dbsession*.py")
    if session_mod is None:
        print "No session found..."
        sys.exit()
    gmci.pvar_session = session_mod[10:-22] #this is dangerous

if args.id:
    gmci.pvar_model_id = args.id
else:
    gmci.pvar_model_id = args.region + "_" + args.study

if args.devel:
    gmci.pvar_devel = "devel"

if args.production:
    gmci.pvar_devel = ""

if args.study_run_dir:
    gmci.pvar_study_run_dir = args.study_run_dir

if args.dicex_dir:
    gmci.pvar_dicex_dir = args.dicex_dir



#if args.scenario:
#    gmci.pvar_scenario = args.scenario


if args.noload:
    gmci.pvar_noload = True

gmci.launch()



