import copy
import getpass
from itertools import chain, imap
import  collections
from string import Template
import epistudy_cfg as ec
import pgsa_utils as pgu
import subprocess
import random 
import pgsa_utils as pgu
import socket
import versa_impl as vi
import metadata_utils as mu
import utilities
import os
import xmlutils as xu ##for debugging only
import sys
import imp
import versa_utils as vu
import versa_api as vapi
import sidap_utils as su
import pickle

user=getpass.getuser()

def init(cfg_root):
    dbsession = ec.get_dbsession(cfg_root)
    vi.init(dbsession)
    study_base_dir = ec.get_study_dir(cfg_root)
    subprocess.call('mkdir -p ' + study_base_dir, shell=True)
    #we no longer folow this convention -- all studies now are done at the base
#     study_dir = ec.get_study_dir(cfg_root) 
#     subprocess.call('mkdir -p ' + study_dir, shell=True)

####moved to add_study_utils module
# def update_intv_files_iter(iter):
#     update_intv_files(args[0], args[2], args[3])

# def update_intv_files(cfg_root, replicate_desc, replicate_dir):
#     '''update the intervention file with the indemics server ip address
#     '''
#     indemics_server_hostname=socket.gethostname()
#     indemics_server_ipaddr=socket.gethostbyname(indemics_server_hostname)

#     efdir=replicate_dir + '/epifast_job'
#     intv_config_loc = efdir+'/Intervention'
#     intv_config_template_loc = intv_config_loc + '.template'
#     intv_config_template_str = open(intv_config_template_loc, 'r').read()
#     intv_config_template = Template(intv_config_template_str)
#     a = locals()
#     b = globals()
#     a.update(b)
#     intv_config_str = intv_config_template.substitute(a)
#     intv_cfg_fh = open(intv_config_loc, 'w')
#     intv_cfg_fh.write(intv_config_str)
#     intv_cfg_fh.close()
###################

def get_incubation_period_cfg(cfg_root):
    template_dir = ec.get_cfg_template_dir(cfg_root)
    elem = None
    if xu.has_key(cfg_root, 'disease_model/incubation_period', path_prefix='.//'):
        elem = xu.get_elems(cfg_root, 'disease_model/incubation_period', uniq=True)

    if elem is None:
        return ['DISTRIBUTION', template_dir + "/Incubation.Period.Distribution"]
    incubation_cfg = xu.XmlDictConfig(elem)
    if incubation_cfg['type'] == 'distribution':
        file_loc_elem = xu.get_elems(elem, 'file_loc', uniq=True)
        assert file_loc_elem  is not None
        icb_fn = file_loc_elem.text
        return['DISTRIBUTION', icb_fn]
            
    if incubation_cfg['type'] == 'heterogenous':
        file_loc_elem = xu.get_elems(elem, 'file_loc', uniq=True)
        if file_loc_elem  is not None:
            icb_fn = file_loc_elem.text
        else:
            icb_fn  = ec.get_study_dir(cfg_root) + "/incubation_period.txt"
            #######################
            #assuming subpop by ORM
            #TODO: put a checker
            ######################
            with open(icb_fn, "w+") as fh:
                [session,stmts] = load_subpop_orms(cfg_root)
                subpop_icb_elems = xu.get_elems(elem, 'subpop_period', uniq=False)
                for icb_elem in subpop_icb_elems:
                    icb_cfg = xu.XmlDictConfig(icb_elem)
                    if icb_cfg['type'] == 'distribution':
                        for id in vapi.scan(session, stmts[icb_cfg['subpop']]):
                            id_icb = 2 ##TODO: sample from distribution
                            fh.write(str(id[0]) + " " + str(id_icb) + "\n")
                    if icb_cfg['type'] == 'fixed':
                        for id in vapi.scan(session, stmts[icb_cfg['subpop']]):
                            id_icb = icb_cfg['period'] 
                            fh.write(str(id[0]) + " " + str(id_icb) + "\n")
        return['HETEROGENEOUS', icb_fn]


def get_infection_period_cfg(cfg_root):
    elem = None
    if xu.has_key(cfg_root, 'disease_model/infection_period', path_prefix='.//'):
        elem = xu.get_elems(cfg_root, 'disease_model/infection_period', uniq=True)
    template_dir = ec.get_cfg_template_dir(cfg_root)
    if elem is None:
        return ['DISTRIBUTION', template_dir + "/Infectious.Period.Distribution"]
    incubation_cfg = xu.XmlDictConfig(elem)
    if incubation_cfg['type'] == 'distribution':
        file_loc_elem = xu.get_elems(elem, 'file_loc', uniq=True)
        assert file_loc_elem  is not None
        icb_fn = file_loc_elem.text
        return['DISTRIBUTION', icb_fn]
    
    if incubation_cfg['type'] == 'heterogenous':
        file_loc_elem = xu.get_elems(elem, 'file_loc', uniq=True)
        if file_loc_elem  is not None:
            ipfn = file_loc_elem.text
        else:
            #######################
            #assuming subpop by ORM
            #TODO: put a checker
            ######################
            ipfn = ec.get_study_dir(cfg_root) + "/infection_period.txt"
            with open(ipfn, "w+") as fh:
                [session,stmts] = load_subpop_orms(cfg_root)
                subpop_icb_elems = xu.get_elems(elem, 'subpop_period', uniq=False)
                for icb_elem in subpop_icb_elems:
                    icb_cfg = xu.XmlDictConfig(icb_elem)
                    if icb_cfg['type'] == 'distribution':
                        for id in vapi.scan(session, stmts[icb_cfg['subpop']]):
                            id_icb = 2 ##TODO: sample from distribution
                            fh.write(str(id[0]) + " " + str(id_icb) + "\n")
                    if icb_cfg['type'] == 'fixed':
                        for id in vapi.scan(session, stmts[icb_cfg['subpop']]):
                            id_icb = icb_cfg['period'] ##TODO: sample from distribution
                            fh.write(str(id[0]) + " " + str(id_icb) + "\n")
        return['HETEROGENEOUS', ipfn]

def get_epidemic_seed_cfg(cfg_root):
    seed_elem = None
    if xu.has_key(cfg_root, 'epifast/epidemic_seed', path_prefix='.//'):
        seed_elem = xu.get_elems(cfg_root, 'epifast/epidemic_seed', uniq=True)
    #assert seed_elem is not None
    if seed_elem is None:
        EpidemicSeedType = "RANDOM_SEEDS_EVERY_DAY"
        EpidemicSeedNumber ="5"
        return [EpidemicSeedType, EpidemicSeedNumber, None]

    seed_type = xu.get_value_by_attr(seed_elem, 'seed_type')

    if seed_type not in  ['GIVEN_SEEDS', 'RANDOM_SEEDS_EVERY_DAY', 'RANDOM_SEEDS_FIRST_DAY']:
        print "This seed type is not supported"
        sys.exit(1)
    EpidemicSeedNumber = xu.get_value_elem(seed_elem, 'seed_number')
    if seed_type == 'RANDOM_SEEDS_EVERY_DAY':
        EpidemicSeedType = "RANDOM_SEEDS_EVERY_DAY"
        return [EpidemicSeedType, EpidemicSeedNumber, None]
        
    if seed_type == 'RANDOM_SEEDS_FIRST_DAY':
        EpidemicSeedType = "RANDOM_SEEDS_FIRST_DAY"
        EpidemicSeedSubpopFile = xu.get_value_elem(seed_elem, 'seed_subpop')
        return [EpidemicSeedType, EpidemicSeedNumber, EpidemicSeedSubpopFile]
        
    initial_infection_fn = "initial_infections.txt"
    if seed_type == 'GIVEN_SEEDS':
        #if the file_loc is specified
        file_loc_elem = xu.get_elems(seed_elem, 'file_loc', uniq=True)
        if file_loc_elem  is not None:
            EpidemicSeedSubpopFile = file_loc_elem.text
        else:
            #######################
            #assuming subpop by ORM
            #TODO: put a checker
            ######################
            inf_fn = ec.get_study_dir(cfg_root) + "/initial_infections.txt"
            with open(inf_fn, "w+") as fh:
                [session,stmts] = load_subpop_orms(cfg_root)
                subpop_seed_elems = xu.get_elems(seed_elem, 'subpop_seed', uniq=False)
            for subpop_elem in subpop_seed_elems: ##Assuming fixed distribution for now
                subpop_cfg = xu.XmlDictConfig(subpop_elem)
                for id in vapi.scan(session, stmts[subpop_cfg['subpop']]):
                    day_inf = 0 ###The day on which this id will be infected
                    fh.write(str(id[0]) + " " + str(day_inf) + "\n")
            EpidemicSeedSubpopFile = inf_fn
        EpidemicSeedType = "GIVEN_SEEDS"
        return [EpidemicSeedType, EpidemicSeedNumber, EpidemicSeedSubpopFile]

def get_iql_template_loc(cfg_root=None, replicate_dir=None):
    '''
    if both iql_template and iql_template_genmod is present the
    iql_template_genmod takes precedece
    '''
    print xu.tostring(cfg_root)
    if xu.has_key(cfg_root, 'iql_template_genmod'):
        iql_genmod = ec.get_iql_template_genmod(cfg_root)
        print iql_genmod
        epistudy_config_dir = ec.get_epistudy_config_dir(cfg_root) #the directory where the genmod is kept
        print epistudy_config_dir
        #try to import the genmod and call the build_iql_template
        #function
        try:
            sys.path.append(epistudy_config_dir)
            imp.find_module(iql_genmod)
            genmod = __import__(iql_genmod)
            iql_template_loc = genmod.gen_iql_template(cfg_root=cfg_root, replicate_dir=replicate_dir)
            print iql_template_loc
            #iql_template_loc = ec.get_iql_template_loc(cfg_root)  ##for testing purposes returning to old set
            return iql_template_loc
        except Exception, e:
            print "Couldn't do it: %s" % e
            print "generation module not found", iql_genmod
            sys.exit()
            #TODO: how to raise exception
    elif xu.has_key(cfg_root, 'iql_template', path_prefix='.//'):
        iql_template_loc = ec.get_iql_template_loc(cfg_root)
        return iql_template_loc
    else:
        print "iql_template element is missing"
        sys.exit() ##figure out how to safely exit
            
        
    


def gen_replicate_iql(cfg_root=None, replicate_dir=None, param_dict=None):
    '''
    generate iql for replicate -- either from iql template 
    or by calling a iql tempate generate function
    '''
    if 'iql_parameters/target_sz' in param_dict:
        print 'parameter iql_parameters/target_sz present'
    efdir=replicate_dir + '/epifast_job'
    iql_template_loc = get_iql_template_loc(cfg_root=cfg_root, replicate_dir=replicate_dir) #previously was ec.get_iql_template_loc(cfg_root)
    assert (iql_template_loc is not None)
    iql_loc = efdir + '/intv.iql'
    try:
        iql_template_str = open(iql_template_loc, 'r').read()
    except IOError:
        print("intervention template file not found " + iql_template_loc)

    iql_template = Template(iql_template_str)
    iql_str = iql_template.substitute(param_dict)
    iql_fh = open(iql_loc, 'w+')
    iql_fh.write(iql_str) 
    iql_fh.close()
    subprocess.call('chmod +x '+iql_loc, shell=True)
    

def apply_post_setup_config(cfg_root, replicate_desc, replicate_dir):
    '''
    last change to modify config file. It calls the study specific 
    configuration function
    '''

    post_setup_config_elem = xu.get_elems(cfg_root, 'post_setup_config', uniq=True)
    customizer_module = xu.get_value_by_attr(post_setup_config_elem, 'module')
    epistudy_config_dir = ec.get_epistudy_config_dir(cfg_root) #the directory where the genmod is kept
    try:
        print epistudy_config_dir
        sys.path.append(epistudy_config_dir)
        imp.find_module(customizer_module)
        customizer = __import__(customizer_module)
        customized_cfg_root =  customizer.run(cfg_root=cfg_root, replicate_dir=replicate_dir, replicate_desc=replicate_desc)
        return customized_cfg_root
    except Exception, e:
        print "Couldn't do it: %s" % e
        print "couldn't run customization module", customizer_module
        sys.exit()
        #TODO: how to raise exception
    
    
def prepare_config_files_iter(replicate_info):
    '''
    prepare config files and intv tables for all replicates
    '''
    prepare_config_files(replicate_info.cfg_root, replicate_info.abbrv_rep_desc, replicate_info.abbrv_rep_dir)


def prepare_config_files(cfg_root, replicate_desc, replicate_dir):
    '''
    prepare config files and intv tables for all replicates
    '''
    #hook for post_setup_customization
    if xu.has_key(cfg_root, 'post_setup_config', path_prefix='.//'):
        [cfg_root,replicate_desc, replicate_dir] = apply_post_setup_config(cfg_root, replicate_desc, replicate_dir) 

    replicate_id = ec.get_replicate_id(cfg_root)
    template_dir = ec.get_cfg_template_dir(cfg_root)
    #intv_type = ec.get_intv_type(cfg_root)
    model_prefix = ec.get_model_prefix(cfg_root)
    ef_socnet_path = ec.get_socnet_path(cfg_root)
    assert ef_socnet_path is not None
    epistudy_config_dir = ec.get_epistudy_config_dir(cfg_root)
    assert epistudy_config_dir is not None

    dbsession=ec.get_dbsession(cfg_root)
    coord_ip_address=pgu.get_db_host(dbsession)
    
    efdir=replicate_dir + '/epifast_job'
    print "mkdir ", efdir
    subprocess.call('mkdir -p ' + efdir, shell=True)
    epifast_config_template_loc = template_dir + '/efcfg.template'
    epifast_config_loc = efdir + '/Configuration'
    epifast_config_template_str=open(epifast_config_template_loc, "r").read()
    epifast_config_template= Template(epifast_config_template_str)
    epifast_settings_dict = ec.get_epifast_setting(cfg_root)

    if xu.has_key(cfg_root, 'epifast/randgen_seed', path_prefix='.//'):
        rand_gen = xu.get_value_by_attr(cfg_root, 'epifast/randgen_seed')
    
    else:
        rand_gen = random.randint(0, 1048576 * 1000) #simulation rand gen
    #########
    ## Configure Incubation
    ########
    # [IncubationPeriodFormat, IncubationPeriodFile] = get_incubation_period_cfg(cfg_root)
#     [InfectiousPeriodFormat, InfectiousPeriodFile] = get_infection_period_cfg(cfg_root)
#     [EpidemicSeedType, SetEpidemicSeed] = get_epidemic_seed_cfg(cfg_root)
    
    IncubationPeriodFormat = xu.get_value_by_attr(cfg_root, 'disease_model/IncubationPeriodFormat')
    IncubationPeriodFile = xu.get_value_by_attr(cfg_root, 'disease_model/IncubationPeriodFile')
    InfectiousPeriodFormat = xu.get_value_by_attr(cfg_root, 'disease_model/InfectiousPeriodFormat')
    InfectiousPeriodFile = xu.get_value_by_attr(cfg_root, 'disease_model/InfectiousPeriodFile')
    EpidemicSeedType = xu.get_value_by_attr(cfg_root, 'disease_model/EpidemicSeedType')
    EpidemicSeedNumber = xu.get_value_by_attr(cfg_root, 'disease_model/EpidemicSeedNumber')
    seed_number_stmt = "EpidemicSeedNumber = " + EpidemicSeedNumber
    seed_subpop_stmt = ""
    if xu.has_key(cfg_root, 'disease_model/EpidemicSeedFile', path_prefix='.//'):
        seed_subpop_stmt= "EpidemicSeedFile =  " + xu.get_value_by_attr(cfg_root, 'disease_model/EpidemicSeedFile')



    ####TODO: convert to dict and update
    
    a = locals()
    b = globals()
    a.update(b)
    a.update(epifast_settings_dict)
    epifast_config_str = epifast_config_template.substitute(a)
    efcfg = open(epifast_config_loc, 'w+')
    efcfg.write(epifast_config_str)
    efcfg.close()     
    
    ### prepare Diagnosis file
    diagnosis_config_loc = efdir + '/Diagnosis'
    diagnosis_fh =  open(diagnosis_config_loc, 'w+')
    diagnosis_dict = ec.get_epifast_diagnosis_settings(cfg_root)
    diagnosis_fh.write("ModelVersion = " + diagnosis_dict['ModelVersion']+'\n')
    diagnosis_fh.write("ProbSymptomaticToHospital = " + diagnosis_dict['ProbSymptomaticToHospital']+'\n')
    diagnosis_fh.write("ProbDiagnoseSymptomatic = " + diagnosis_dict['ProbDiagnoseSymptomatic']+'\n')
    diagnosis_fh.write("DiagnosedDuration = " + diagnosis_dict['DiagnosedDuration']+'\n')
    diagnosis_fh.close()
    

    ##prepare intervention file
    indemics_server_ipaddr = '${indemics_server_ipaddr}' #to be filled by indemics server
    intv_config_template_loc = template_dir + '/intvcfg.template'

    intv_config_loc = efdir+'/Intervention.template'
    intv_config_template_str = open(intv_config_template_loc, 'r').read()
    intv_config_template = Template(intv_config_template_str)
    a = locals()
    b = globals()
    a.update(b)
    intv_config_str = intv_config_template.substitute(a)
    intv_cfg_fh = open(intv_config_loc, 'w')
    intv_cfg_fh.write(intv_config_str)
    
    ##add offline interventions
    #if EpifastOfflineIntvFile is not None:
    #    offline_intv_str = open(EpifastOfflineIntvFile, 'r').read()
    #    intv_cfg_fh.write(offline_intv_str)

    #intv_cfg_fh.close()
    
    # prepare offline intervention file
    # SW: parameterize offline intervention file such that config elements within it can be accessed.
    if xu.has_key(cfg_root, 'epifast/offline_intv_path', path_prefix='.//'):
        EpifastOfflineIntvFile = xu.get_value_by_attr(cfg_root, 'epifast/offline_intv_path')
        offline_intervention_template_loc = template_dir + 'offline.template'
        offline_intervention_settings_dict = ec.get_offline_intervention_setting(cfg_root)
        offline_intervention_template_str = open(EpifastOfflineIntvFile, 'r').read()
        if offline_intervention_settings_dict is not None:
            offline_intervention_template = Template(offline_intervention_template_str)
            offline_intervention_str = offline_intervention_template.substitute(offline_intervention_settings_dict)
            intv_cfg_fh.write(offline_intervention_str)
        else:
            intv_cfg_fh.write(offline_intervention_template_str)

    intv_cfg_fh.close()
    
    ###########################################################
    ## dump the replicate config xml in the replicate directory
    ###########################################################
    cfg_string = xu.tostring(cfg_root)
    with open(replicate_dir + "/replicate_cfg.xml", 'w') as fh:
        fh.write(cfg_string)

    setup_dry_run = ""
    if xu.has_key(cfg_root, 'doe/setup_dry_run', path_prefix='.//'):
        setup_dry_run = xu.get_value_by_attr(cfg_root, 'doe/setup_dry_run')
    if not setup_dry_run:
        pre_intv_elem = ec.get_pre_intv_elem(cfg_root)
        process_pre_intv_begin(replicate_desc, pre_intv_elem)

    return

def process_iql_helper_scripts(iql_helper_templates_elem, replicate_desc, replicate_dir):
    if iql_helper_templates_elem is None:
        return
    print "this functionality is not yet implemented"
    sys.exit(1)


def process_pre_intv_begin(replicate_desc, pre_intv_node):

    create_table_elems = xu.get_elems(pre_intv_node, 'create_table')
    if create_table_elems is None: #no tables need to be created for this
        return 
    for ct in create_table_elems:
        location_fp = None
        model_name  = None
        metadata_fn = xu.get_value_by_attr(ct, 'metadata')
        if xu.has_key(ct, 'location'):
            location_fp = xu.get_value_by_attr(ct, 'location')
        if xu.has_key(ct, 'model_name'):
            model_name = xu.get_value_by_attr(ct, 'model_name')
        
        metadata_root = mu.read_metadata(metadata_fn)
        if model_name is None:
            model_name = mu.get_model_name(metadata_root)
        
        new_model_name = replicate_desc + '_' + model_name
        mu.set_model_name(metadata_root, new_model_name)
        vi.build_orm_from_metadata(metadata_root, create_table=True, force_create_model=True, location=location_fp, class_decorator="")
    
    #orm for tables -- assumes that the table is already created by external programs
    create_table_orms = xu.get_elems(pre_intv_node, 'create_orm')
    if create_table_orms is None: #no tables need to be created for this
        return 
    for ct in create_table_orms:
        model_name = None
        metadata_fn = xu.get_value_by_attr(ct, 'metadata')
        if xu.has_key(ct, 'model_name'):
            model_name = xu.get_value_by_attr(ct, 'model_name')
        metadata_root = mu.read_metadata(metadata_fn)
        if model_name is None:
            model_name = mu.get_model_name(metadata_root)
        
        new_model_name = replicate_desc + '_' + model_name
        mu.set_model_name(metadata_root, new_model_name)
        vi.build_orm_from_metadata(metadata_root, base_tbl_name = None, create_table=False, force_create_model=True, location=None, class_decorator="")
    
def launch_ef_job_iter(replicate_info):
    launch_ef_job(replicate_info.cfg_root, replicate_info.abbrv_rep_desc, replicate_info.abbrv_rep_dir)


def launch_ef_job(cfg_root, replicate_desc, replicate_dir):
    replicate_cfg_fn = 'replicate_cfg.xml'
    walltime = ec.get_epifast_walltime(cfg_root)
    template_dir=ec.get_cfg_template_dir(cfg_root)
    indemics_dir = ec.get_indemics_dir(cfg_root)
    region = ec.get_study_region(cfg_root)
    ef_nodes = ec.get_epifast_num_nodes(cfg_root)
    ef_host_type = ec.get_epifast_host_type(cfg_root)
    [qsub_group_list, qsub_q, qsub_ppn]  = utilities.get_qsub_queue_args(ef_host_type)

    study_dir = ec.get_study_dir(cfg_root)
    epifast_bin = ec.get_epifast_bin(cfg_root)
    mpi_module = ec.get_mpi_module(cfg_root)
    cluster_name = utilities.get_cluster_name()
    espresso_base_dir = ec.get_espresso_base_dir(cfg_root)
    dicex_env = ". " + utilities.get_dicex_base_dir() + "/dicex_" + cluster_name + ".sh"
    
    #is this a dry run
    epifast_dry_run = '0'
    if xu.has_key(cfg_root, 'doe/epifast_dry_run', path_prefix=".//"):
        epifast_dry_run = xu.get_value_by_attr(cfg_root, 'doe/epifast_dry_run')
        
    PBS_O_WORKDIR = '$PBS_O_WORKDIR'
    PBS_JOBID = '$PBS_JOBID'
    jobid = '$jobid'
    PBS_NODEFILE = '$PBS_NODEFILE'
    SIMDM_ROOT='$SIMDM_ROOT'
    CLASSPATH='$CLASSPATH'
    SIMDM_LIB='$SIMDM_LIB'
    SIMDM_JAR='$SIMDM_JAR'
    NUM_NODES='$NUM_NODES'
    MPIRUN='$MPIRUN' 
    iql_loc = replicate_dir + '/epifast_job/intv.iql'
    ef_cfg_loc = replicate_dir + '/epifast_job/Configuration'
    rep_home = replicate_dir
    job_out_file = rep_home + '/epifast_job/ef_job.out'
    client_out = rep_home  +  '/client.out'
    client_err = rep_home  +  '/client.err'
    ef_out = rep_home + '/epifast_job/ef_out.txt'
    ef_err = rep_home + '/epifast_job/ef_err.txt'
    ef_jobname=region + '-' + replicate_desc
    ef_qsub_job_cfg_template_loc = template_dir + '/epifast_job.qsub.template'
    ef_qsub_job_cfg_loc = rep_home + '/epifast_job/ef_job.qsub'
    ef_qsub_job_cfg_template_str = open(ef_qsub_job_cfg_template_loc, 'r').read()
    ef_qsub_job_cfg_template = Template(ef_qsub_job_cfg_template_str)

    a = locals()
    b = globals()
    a.update(b)
    ef_qsub_job_cfg_str = ef_qsub_job_cfg_template.substitute(a)
    ef_qsub_job_cfg_fh = open(ef_qsub_job_cfg_loc, 'w')
    ef_qsub_job_cfg_fh.write(ef_qsub_job_cfg_str)
    ef_qsub_job_cfg_fh.close()
    subprocess.call('qsub ' + ef_qsub_job_cfg_loc, shell=True) 
    return



def get_doe_iter(cfg_root=None):
    '''
    builds an iterator over the experiment designe 
    specified in the config file
    
    Caution: use full_factorial only with cell_rep_lexicograhic and
            contigious_lexicograhic with replicate_ordered
    '''
    labeling = 'cell_rep_lexicograhic'

    if xu.has_key(cfg_root, 'doe/labeling', path_prefix='.//'):
        labeling = xu.get_value_by_attr(cfg_root, 'doe/labeling')

    import doe_generator_plugin as dgp
    import add_study_utils as asu
    doe_generator = dgp.get_doe_generator(cfg_root)
    domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
    doe_iter = doe_generator([cfg_root, domain_iter, '', None])
    if labeling == 'cell_rep_lexicograhic':

        import  doe_iter_to_cell_info_iter as cii
        to_cell_info = cii.to_cell_info
        import  cell_info_iter_to_replicate_info_iter as torii
        to_replicate_info = torii.to_replicate_info
        #doe_with_short_name_iter = assign_short_name(doe_iter)
        doe_with_short_name_iter = to_replicate_info(cfg_root, to_cell_info(doe_iter))
        return doe_with_short_name_iter
    if labeling == 'contigious_lexicograhic':
        from assign_short_name import assign_short_name
        doe_with_short_name_iter = assign_short_name(doe_iter) 
        return doe_with_short_name_iter
    
    assert False


def create_replicate_configurations(cfg_root):
    '''
    create configuration for each replicate of doe. 
    '''
    #return if no doe is defined
    if not xu.has_key(cfg_root, "epistudy/doe"): #switched to doe
        print "doe element not found"
        return
    random_seed=ec.get_epifast_seed(cfg_root)
    random.seed(random_seed)
    
    [IncubationPeriodFormat, IncubationPeriodFile] = get_incubation_period_cfg(cfg_root)

    [InfectiousPeriodFormat, InfectiousPeriodFile] = get_infection_period_cfg(cfg_root)
    [EpidemicSeedType, EpidemicSeedNumber, EpidemicSeedFile] = get_epidemic_seed_cfg(cfg_root)
    epf_dm = None
    if xu.has_key(cfg_root, 'epifast/disease_model', path_prefix='.//'):
        epf_dm = xu.get_elems(cfg_root, 'epifast/disease_model', uniq=True)
    if epf_dm is None:
        epf = xu.get_elems(cfg_root, 'epifast', uniq=True)
        epf.append(xu.gen_node('disease_model', 'disease_model'))
    epf_dm = xu.get_elems(cfg_root, 'epifast/disease_model', uniq=True)
    epf_dm.append(xu.gen_node('IncubationPeriodFormat', IncubationPeriodFormat))
    epf_dm.append(xu.gen_node('IncubationPeriodFile', IncubationPeriodFile))
    epf_dm.append(xu.gen_node('InfectiousPeriodFormat', InfectiousPeriodFormat))
    epf_dm.append(xu.gen_node('InfectiousPeriodFile', InfectiousPeriodFile))
    epf_dm.append(xu.gen_node('EpidemicSeedType', EpidemicSeedType))
    epf_dm.append(xu.gen_node('EpidemicSeedNumber', EpidemicSeedNumber))
    if EpidemicSeedFile is not None:
        epf_dm.append(xu.gen_node('EpidemicSeedFile', EpidemicSeedFile))



        
    doe_iter = get_doe_iter(cfg_root)
    collections.deque(imap(prepare_config_files_iter,doe_iter), maxlen= 0) #call prepare_config_files for each cfg of the doe
    import add_study_utils as asu
    doe_iter = get_doe_iter(cfg_root)
    collections.deque(imap(asu.update_intv_files_iter,doe_iter), maxlen= 0) #call prepare_config_files for each cfg of the doe

        

def prepare_launch_indemics_server_script(cfg_root):
    '''
    build launch_indemics_server.sh
    '''

    template_dir=ec.get_cfg_template_dir(cfg_root)
    study_dir = ec.get_study_dir(cfg_root)
    indemics_dir = ec.get_indemics_dir(cfg_root)
    cluster_name = utilities.get_cluster_name()
    indemics_server_template_loc = template_dir + '/launch_indemics_server.sh.template'
    indemics_server_loc = study_dir + '/launch_indemics_server.sh'
    indemics_server_template_str=open(indemics_server_template_loc, "r").read()
    indemics_server_template= Template(indemics_server_template_str)
    a = locals()
    b = globals()
    a.update(b)
    indemics_server_str = indemics_server_template.safe_substitute(a) #ignore shell variables
    start_fh = open(indemics_server_loc, 'w+')
    start_fh.write(indemics_server_str)
    start_fh.close()
    subprocess.call('chmod +x ' + indemics_server_loc, shell=True)
    
def prepare_indemics_server_cfg(cfg_root):
    max_threads = ec.get_indemics_max_threads(cfg_root) ##TOOD:  used for indemics_server_cfg.template
    template_dir=ec.get_cfg_template_dir(cfg_root)
    study_dir = ec.get_study_dir(cfg_root)
    dbsession= ec.get_dbsession(cfg_root)
    port = pgu.get_db_port(dbsession)
    assert (port is not None)
    coord_hostname=socket.gethostname()
    coord_ip_address=socket.gethostbyname(coord_hostname)
    a = locals()
    b = globals()
    a.update(b)
    conf_dir = study_dir + '/conf'
    subprocess.call('mkdir -p ' + conf_dir, shell=True)
    
    indemics_server_cfg_template_loc = template_dir + '/indemics_server_cfg.template'
    indemics_server_cfg_loc = study_dir+'/conf/simdm.conf'
    indemics_server_cfg_template_str = open(indemics_server_cfg_template_loc, 'r').read()
    indemics_server_cfg_template = Template(indemics_server_cfg_template_str)
    indemics_server_cfg_str = indemics_server_cfg_template.substitute(a)


    indemics_server_cfg_fh = open(indemics_server_cfg_loc, 'w+')
    indemics_server_cfg_fh.write(indemics_server_cfg_str)
    indemics_server_cfg_fh.close()
    
    #prepare simdb_server.conf
    subprocess.call('cp ' + template_dir +  '/simdb.conf ' + study_dir + "/conf",  shell=True)
    prepare_launch_indemics_server_script(cfg_root)



def load_model_data(cfg_root):
    if xu.has_key(cfg_root, "model/model_data/edcfg_file"):
        load_model_data_from_edcfg(cfg_root)
    if xu.has_key(cfg_root, "model_data/gp_pipeline/"):
        load_model_data_from_gp_pipeline(cfg_root)
        

def load_model_data_from_gp_pipeline(cfg_root):
    dbsession = ec.get_dbsession(cfg_root)
    work_dir= pgu.get_work_dir(dbsession)
    pipeline_log = xu.get_value_elem(cfg_root, 'model_data/gp_pipeline/gp_pipeline_log')
    mapping_xml = xu.get_value_elem(cfg_root, 'model_data/gp_pipeline/mapping_file')
    pipeline_log_root = xu.read_file(pipeline_log)
    mapping_root = xu.read_file(mapping_xml)
    all_sios = xu.get_elems(cfg_root, 'sio', path_prefix=".//gp_pipeline/sio_list/")
    for sio in all_sios:
        su.build_relational_mapping(sio.text, mapping_root, pipeline_log_root, work_dir)
    
    #print all_sios



def load_model_data_from_edcfg(cfg_root):
    print "in load_model_data_from_edcfg"
    model_data_cfg = ec.get_model_data_cfg_file(cfg_root)
    region = ec.get_study_region(cfg_root)
    metadata_dir = ec.get_metadata_dir(cfg_root)
    model_dir = ec.get_model_dir(cfg_root)
    model_prefix = ec.get_model_prefix(cfg_root)
    edcfg_entity_header = Template("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE edcfg [
<!ENTITY var_region "$region">
<!ENTITY var_metadata_dir "$metadata_dir">
<!ENTITY var_model_dir "$model_dir">
<!ENTITY var_model_prefix "$model_prefix">
]>
""").substitute(locals())
    print edcfg_entity_header
    print model_data_cfg
    edcfg_root = xu.read_string(edcfg_entity_header + open(model_data_cfg).read())
    vi.build_orms(edcfg_root)

def launch_indemics_server_job(cfg_fn, cfg_root):
    ''' build the qsub file
    '''
    global user
    template_dir=ec.get_cfg_template_dir(cfg_root)
    study_dir = ec.get_study_dir(cfg_root)
    dbsession = ec.get_dbsession(cfg_root)
    dicex_base_dir =ec.get_dicex_base_dir(cfg_root)
    work_dir= pgu.get_work_dir(dbsession)
    host_type = ec.get_indemics_server_host_type(cfg_root)
    [qsub_group_list, qsub_q, qsub_ppn]  = utilities.get_qsub_queue_args(host_type)
    #[qsub_group_list, qsub_q, qsub_ppn] = ec.get_indemics_server_job_params(cfg_root)
    #print qsub_group_list, " ", qsub_q
        
    ##################################################################
    ## build indemics_server job
    ##################################################################
    PATH="$PATH"
    PYTHONPATH="$PYTHONPATH"
    PBS_O_WORKDIR="$PBS_O_WORKDIR"
    PBS_JOBID="$PBS_JOBID"
    jobid="$jobid"
    launcher_hostname  = socket.gethostname()
    walltime = xu.get_value_elem(cfg_root, 'indemics_server/walltime')
    message_port = utilities.get_new_port()
    cluster_name = utilities.get_cluster_name()
    template_loc = template_dir + "/indemics_server_job.qsub.template"
    template_str = Template(open(template_loc, 'r').read())
    a = locals()
    b = globals()
    a.update(b)
    cmd_str = template_str.substitute(a)
    qsub_loc = study_dir + "/launch_indemics_server.qsub"
    qsub_fh = open(qsub_loc, 'w+')
    qsub_fh.write(cmd_str)
    qsub_fh.close()
    subprocess.call("qsub "+ qsub_loc, shell=True)
    message_port_listener = utilities.get_listener(message_port)
    utilities.signal_listen(message_port_listener)




def get_indemics_qsub_jobid(dbdesc=None):
    session_fn=pgu.get_session_fn(dbdesc)
    jobid=None
    try:
        sys.path.append(os.getcwd())
        imp.find_module(session_fn)
        dbsession=__import__(session_fn)
        jobid=dbsession.indemics_server_jobid
    except :
        found=False
        print ("import error in get_qsub_jobid")
    return jobid

def get_indemics_server_hostname(dbdesc=None):
    session_fn=pgu.get_session_fn(dbdesc)
    jobid=None
    try:
        sys.path.append(os.getcwd())
        imp.find_module(session_fn)
        dbsession=__import__(session_fn)
        hostname=dbsession.indemics_server_hostname
    except ImportError:
        found=False
        print ("import error in get_indemics_server_hostname")
    return hostname



def load_subpop_orms(cfg_root):
    dbsession = ec.get_dbsession(cfg_root)
    edcfg_root = ec.get_edcfg_root(cfg_root)
    
    if edcfg_root is None:
        return

    session = vi.init(dbsession)
    subpop_id_stmts = {}
    vi.build_orm_files(edcfg_root)
    for subpop_elem in xu.get_elems(cfg_root, 'subpops/subpop'):
        subpop_cfg= xu.XmlDictConfig(subpop_elem)
        subpop_orm = vu.import_model(subpop_cfg['pyorm'])
        subpop_id_stmts[subpop_cfg['name']] = vapi.proj(session, subpop_orm, subpop_cfg['id_attr'])
    return [session, subpop_id_stmts]
 




