#!/apps/packages/math/epd/7.3-1/bin/python
import gen_doe_cfg_impl as gdci
import utilities
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--id", help="id for this study set", nargs='?', const=None)
parser.add_argument("--model", help="model xml file on which this doe is designed", nargs='?', const=None)
parser.add_argument("--scenario", help="specify scenario (basecase, scene1, etc.)", nargs='?', const=None)
parser.add_argument("--doe_type", help="full factorial or lhs", nargs='?', const=None)
parser.add_argument("--output", help="name of the config file", nargs='?', const=None)
parser.add_argument("--simulation_duration",  help="number of days for running the simulation", nargs='?', const=None)
parser.add_argument("--walltime_hours",  help="simulation walltime hours", nargs='?', const=None)
parser.add_argument("--labeling",  help="label design for cells and replicates", nargs='?', const=None)
parser.add_argument("--launcher_type",  help="standard or throttled", nargs='?', const=None)  


parser.add_argument("--study_args", help="study specific argument list", nargs='?', const=None)
parser.add_argument("--domain_file", help="xml file that specifies parameter domain for the doe", nargs='?', const=None)

parser.add_argument("--num_samples", help="number of samples to be used for lhs design", nargs='?', const=None)
parser.add_argument("--ef_host_type",  choices = ['standard', 'largemem'], help="compute node type for db (standard or large memory)", nargs='?', const=None)
parser.add_argument("--ef_num_nodes", help="number of compute nodes ", nargs='?', const=None)


parser.add_argument("--num_replicates", help="specify number of replicates", nargs='?', const=None)
parser.add_argument("--norun",  help="generate configuration only -- don't run the doe", action='store_true')
parser.add_argument("--epifast_dry_run",  help="launch qsub but don't run indemics/client -- used for qsub config test", action='store_true')
parser.add_argument("--setup_dry_run",  help="cycle through each replicate but don't build the setup data -- used for config file syntax check", action='store_true')
parser.add_argument("--dry_run_iconductor",  help="cycle through the code but don't fire the intervention--use for syntax checking", action='store_true')


args = parser.parse_args()

if args.id: 
    gdci.pvar_sid = args.id
else:
    last_doe_xml = utilities.get_last_file_by_pattern("sid_[0-9]*.xml")
    if last_doe_xml is None:
        gdci.pvar_sid = '1'
    else:
        last_doe_id_str = last_doe_id[4:-4]
        try:
            last_doe_id = int(last_doe_id_str)
            gdci.pvar_sid = str(last_doe_id + 1)
            print "Created new experiment design with sid = ", gdci.pvar_sid
        except:
            gdci.pvar_sid = '1'
            print "Created new experiment design with sid = ", gdci.pvar_sid

if args.model:
    gdci.pvar_model_id = args.model
else:
    last_model  = utilities.get_last_file_by_pattern("common*_model.xml")
    if last_model is None:
        print "No existing model found in this directory"
        sys.exit()
    model_id = last_model[7:-10]
    print model_id
    gdci.pvar_model_id = model_id

if args.walltime_hours:
    gdci.pvar_epifast_walltime = args.walltime_hours

if args.ef_host_type:
    gdci.pvar_epifast_host_type = args.ef_host_type

if args.ef_num_nodes:
    gdci.pvar_epifast_num_nodes = args.ef_num_nodes 

if args.scenario:
    gdci.pvar_scenario = args.scenario

# if args.doe_type:
#     gdci.pvar_doe_cfg_suffix = args.doe_type

if args.output is None:
    gdci.pvar_cfg_out = "sid_" + gdci.pvar_sid + ".xml"

if args.domain_file:
    gdci.pvar_domain_param_cfg_fn = args.domain_file

if args.study_args:
    gdci.pvar_study_args = args.study_args

if args.simulation_duration:
    gdci.pvar_simulation_duration = args.simulation_duration

if args.num_replicates:
    gdci.pvar_num_replicates = args.num_replicates

if args.doe_type:
    gdci.pvar_doe_type = args.doe_type

if args.num_samples:
    gdci.pvar_lhs_num_samples = args.num_samples

if args.labeling:
    gdci.pvar_labeling = args.labeling

if args.launcher_type:
    gdci.pvar_launcher_type = args.launcher_type

if args.setup_dry_run:
    gdci.pvar_setup_dry_run = "1"

if args.dry_run_iconductor:
    gdci.pvar_dry_run_iconductor = "1"
    
if args.epifast_dry_run:
    gdci.pvar_epifast_dry_run = "1"
    
if args.norun is True:
    gdci.pvar_norun = True

gdci.run()
