import jpype
import xmlutils as xu
import epistudy_cfg as ec
import versa_utils as vu
import time
from string import Template
import sys
import numpy as np
import intervention_conductor_helper as ich

    

def run(cfg_root, replicate_desc, dry_run=False):
    #get indemics base dir
    #set the classpath

    #the session
    dbsession = ec.get_dbsession(cfg_root)
    session_run_dir = ec.get_study_dir(cfg_root)
    session = vu.build_session(dbsession, conn_remote=True, session_run_dir=session_run_dir)
    
    indemics_dir = xu.get_value_by_attr(cfg_root, 'system/indemics_dir')
    classpath=Template("${indemics_dir}/library/classes12.jar:${indemics_dir}/release/Indemics_client.jar:${indemics_dir}/release/build/").substitute(indemics_dir = indemics_dir)
    #print classpath
    #classpath="/home/sandeep/NDSSL-Software/devel/indemics_server/library/classes12.jar:/home/sandeep/NDSSL-Software/devel/indemics_server/release/Indemics_client.jar:/home/sandeep/NDSSL-Software/devel/indemics_server/release/build/"

    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % classpath)
    client_package = jpype.JPackage('edu').vt.ndssl.simdm.client
    agc = client_package.APIGameClient
    
    study_dir = ec.get_study_dir(cfg_root)
    conf_dir = study_dir + "/conf"
    agc.configure(conf_dir) #connects to the indemics server
    agci = agc()
    
    cfg_dir = ec.get_epistudy_config_dir(cfg_root)
    model_prefix = ec.get_model_prefix(cfg_root)
    replicate_desc = replicate_desc
    #prepare for intervention
    ip_header = Template("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE edcfg [
<!ENTITY var_model_prefix "$model_prefix">
<!ENTITY var_replicate_desc "$replicate_desc">
]>
""").substitute(locals())
    ip_fn = ec.get_intervention_prescription_config_file(cfg_root)
    ip_root = xu.read_string(ip_header + open(ip_fn).read())

    iql_param_dict = ich.get_iql_param_values(cfg_root)
    all_intv_dict = ich.prepare_intervention_param_value(cfg_root)
    if iql_param_dict is not None:
        all_intv_dict.update(iql_param_dict)

    #update with study_params
    study_param_value_dict =  ich.prepare_study_param_values(cfg_root)
    all_intv_dict.update(study_param_value_dict)
    

    #get setup parameters, i.e., parameters that are depeneded upon the setup or region
    setup_param_value_dict = ich.load_setup_parameters(session, cfg_root, replicate_desc)
    if setup_param_value_dict is not None:
        all_intv_dict.update(setup_param_value_dict)

    #load continious params modules
    continious_param_dict = ich.load_continious_parameters(session, cfg_root, replicate_desc)
    
    background_elem = xu.get_elems(ip_root, 'background', path_prefix='./', uniq=True)
    setup_elem = xu.get_elems(background_elem, 'setup_stmts', path_prefix='./', uniq=True)
    pre_intv_db_elem = xu.get_elems(background_elem, 'pre_intv_db_stmts', path_prefix='./', uniq=True)
    intv_elem = xu.get_elems(background_elem, 'intv_stmts', path_prefix='./', uniq=True)
    post_intv_db_elem = xu.get_elems(background_elem, 'post_intv_db_stmts', path_prefix='./', uniq=True)

    #cycle through the simulation days
    simulation_duration = ec.get_simulation_duration(cfg_root)
    if not dry_run:
        agci.execCommand("set player id: ndssl,ndssl")
        agci.execCommand(Template("select session: session = ${replicate_desc}, super player").substitute(locals())) #put its credentials
    
    assert 'day' not in all_intv_dict #day is special variable and should not be used
    if not dry_run:
        agci.execCommand("manage table: " + Template("create view ${replicate_desc}_diagnosed as select pid as pid, time as day from &{diagnosed table}").substitute(replicate_desc = replicate_desc))
        agci.execCommand("manage table: " + Template("create view ${replicate_desc}_infection_trace as select *  from &{infection table}").substitute(replicate_desc = replicate_desc))

    all_intv_dict['double_backslash'] = '\\' #for python create function

    schedule_default_idx = slice(0,int(simulation_duration))
    all_simulation_days = np.arange(0, int(simulation_duration))

    #load continious params info 
    continious_params_dict = ich.load_continious_parameters(session, cfg_root, replicate_desc)
    
    intv_label_to_schedule = {}
    intv_label_to_trigger = dict()
    for ws_e in intv_elem:
        schedule_elem = ws_e.find('schedule')
        label = ws_e.find('label').text
        if schedule_elem is not None:
            schedule_idx_text = schedule_elem.text
            print schedule_idx_text
            schedule_idx = slice(*[int(i) for i in schedule_idx_text.split(':')])
        else:
            schedule_idx = schedule_default_idx
        intv_label_to_schedule[label] = all_simulation_days[schedule_idx]

        trigger_elem = ws_e.find('trigger')
        intv_label_to_trigger[label] = None
        if trigger_elem is not None:
            start_threshold = float(xu.get_value_by_attr(trigger_elem, 'start_threshold'))
            stop_threshold = float(xu.get_value_by_attr(trigger_elem, 'stop_threshold'))
            continious_param = xu.get_value_by_attr(trigger_elem, 'on')
            intv_label_to_trigger[label] = [continious_param, start_threshold, stop_threshold]
            

    for ws_e in setup_elem: #for all setup statements
        st_e = ws_e.find('stmt')
        if st_e is None:
            continue
        label_e = ws_e.find('label')
        db_stmt = st_e.text 
        start = time.time()
        if not dry_run:
            agci.execCommand("manage table: " + Template(db_stmt).substitute(all_intv_dict))
        end = time.time()
        print "Time taken: ", label_e.text, " ", (end-start)/60



    for day in range(0, simulation_duration):
        all_intv_dict['day'] = day

        continious_params_value_dict = dict()
        if continious_params_dict is not None:
            for cpn, cpf in continious_params_dict.items():
                continious_params_value_dict[cpn] = cpf.evaluate(session, cfg_root, replicate_desc, day-1)
            all_intv_dict.update(continious_params_value_dict)
        
        #update dynamic parameters
        continious_implicit_params_value_dict = ich.prepare_continious_implict_study_param_values(cfg_root, all_intv_dict) #all_intv_dict is updated with day param-value
        all_intv_dict.update(continious_implicit_params_value_dict)
        for ws_e in pre_intv_db_elem:
            db_e = ws_e.find('stmt')
            if db_e is None:
                continue
            label_e = ws_e.find('label')
            db_stmt = db_e.text 
            #print Template(db_stmt).substitute(all_intv_dict) #pipe this statement to the client
            start = time.time()
            if not dry_run:
                agci.execCommand("manage table: " + Template(db_stmt).substitute(all_intv_dict))
            end = time.time()
            print "Time taken: ", label_e.text, " ", (end-start)/60

        intv_stmt = "set interventions: "
        for ws_e in intv_elem:
            it_e = ws_e.find('stmt')
            if it_e is None:
                continue
            label = ws_e.find('label').text
            scheduled = False
            if day in intv_label_to_schedule[label]: #intervention by default all scheduled for all days
                scheduled = True
            
            triggered = True
            if intv_label_to_trigger[label] is not None:
                on_param_name = intv_label_to_trigger[label][0]
                start_threshold = intv_label_to_trigger[label][1]
                end_threshold = intv_label_to_trigger[label][2]
                on_param_val = continious_params_value_dict[on_param_name]
                print "threshold check start_threshold=", '%.6f'% start_threshold, " curr val = ", '%.6f'%on_param_val
                if on_param_val > start_threshold:
                    triggered = True
                    print "start threshold met for intervention ", label
                    print "on_param_name = ", on_param_name, " on_param_val= ", on_param_val
                elif on_param_val < end_threshold:
                    triggered = False
                    print "end threshold met for intervention ", label
                    print "on_param_name = ", on_param_name, " on_param_val= ", on_param_val
                    
            if scheduled and triggered:
                it_stmt_template = it_e.text
                it_stmt = Template(it_stmt_template).substitute(all_intv_dict)
                intv_stmt = intv_stmt + it_stmt + ";"
        print "intv send = ", intv_stmt
        #TODO: bug when no intervention gets selected 
        start = time.time()
        if not dry_run:
            agci.execCommand(intv_stmt)
        end = time.time()
        print "Time taken: intv ", (end-start)/60

        for ws_e in post_intv_db_elem:
            db_e = ws_e.find('stmt')
            if db_e is None:
                continue
            db_stmt = db_e.text 
            label_e = ws_e.find('label')
            #print Template(db_stmt).substitute(all_intv_dict) #pipe this statement to the client
            start = time.time()
            if not dry_run:
                agci.execCommand("manage table:" + Template(db_stmt).substitute(all_intv_dict))
            end = time.time()
            print "Time taken: ", label_e.text, " ", (end-start)/60

        #log end of day
        if not dry_run:
            agci.execCommand(Template("manage table: insert into ${replicate_desc}_day_tracker values ($day)").substitute(day=day, replicate_desc=replicate_desc))

    if not dry_run:
        agci.execCommand("stop session: ")
        agci.execCommand("stop client: ")


import sys
replicate_cfg_fn = sys.argv[1]
cfg_root = xu.read_file(replicate_cfg_fn)
replicate_desc = sys.argv[2]
dry_run = bool(xu.get_value_by_attr(cfg_root, 'doe/dry_run_iconductor'))
run(cfg_root, replicate_desc, dry_run=dry_run)

