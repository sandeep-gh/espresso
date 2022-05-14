#Readme: The stock analyses for any study


from sqlalchemy import inspect
import versa_core.utils as vu
import versa_api as vapi
import versa_api_meta as vam
import versa_api_list as vapil
import versa_api_join_list as vajl
import versa_api_analysis as vapia
import replicate_analysis_utils as rau
from string import Template
import versa_core.export as ex
import versa_core.relational as re
import xmlutils as xu
import doe_generator_plugin as dgp
import copy
import utilities
import epistudy_cfg as ec
import dicex_epistudy_utils as deu

def export_cell_table_as_dataframe(session=None, cfg_root=None, rmo_desc=None, filter_func=None, pks=[]):
    '''
    if rep_id is None then all the replicates are exported as one giant table.
    by default the rep_0 data is returned.
    '''
    #the xml file
    #[all_replicates_tbl, all_replicates_cls, all_replicates_rmo] = unify_studycfg_rmos(session, cfg_root, rmo_desc=rmo_desc, pks=pks)
    all_replicates_rmo = unify_studycfg_rmos(session, cfg_root, rmo_desc=rmo_desc, filter_func=filter_func, pks=pks)
    df = ex.export_as_dataframe(session, all_replicates_rmo)
    return df
    

def export_doe_replicate_results(session=None, doe_id=None, dataset_tags = ["intv", "infection_trace"], filter_funcs=[None, None]):
    '''
    filter_funcs : subselect data from replicate
    '''

        
    if doe_id is not None:
        doe_id = str(doe_id)
        cfg_fn = ec.get_doe_cfg_fn(doe_id) #e.g. returns sid_100.xml for doe_id = 100
    else:
        cfg_fn = utilities.get_last_file_by_pattern("sid_*.xml")
        
    cfg_root  = xu.read_file(cfg_fn)
    res_dataframes = dict()
    for tag, filter_func in zip(dataset_tags, filter_funcs):
        df = export_cell_table_as_dataframe(session, cfg_root, tag, filter_func=filter_func)
        res_dataframes[tag] = df

    return res_dataframes

def export_replicate_results(session=None, doe_id = None, rep_id=None, dataset_tags = ["intv", "infection_trace"]):
    if doe_id is not None:
        doe_id = str(doe_id)
        doe_cfg_fn = ec.get_doe_cfg_fn(doe_id) #e.g. returns sid_100.xml for doe_id = 100
    else:
        doe_cfg_fn = utilities.get_last_file_by_pattern("sid_*.xml")
        
    if doe_cfg_fn is None:
        doe_cfg_fn = utilities.get_last_file_by_pattern("sid_*.xml") 
    model_prefix = doe_cfg_fn[:-4]
    rep_desc = model_prefix + "_" + rep_id 
    rep_models = vu.load_rmos([rep_desc + "_" + _  for _ in dataset_tags])
    res_dataframes = dict()
    for dt,rm  in zip(dataset_tags, rep_models):
        res_dataframes[dt] = ex.export_as_dataframe(session, rm)
    return res_dataframes


# def unify_rmos(session = None, rmo_iter=None,  indexes=[], pks=None, filter_func = None, agg_func=None, name_prefix=None):
#     '''
#     merge all  rmos as a single rmo; required for efficiancy and export to pandas dataframe
#     prelim/context:
#         Replicate rmo  are named as follows: <cfg_label>_<rmo_desc>.py.
#         For example, rmo_desc is "block_daily_diagnosed", where maintains number of diagnosed per block per day during a simulation".
#         Now the rmo for a replicate corresponding to experiment label "c_0.5_r_1" is called "c_0.5_r_1_block_daily_diagnosed". 

#     input:
#         model_selector : a list of bools (for e.g., use to remove experiments that didn't run correctly), is optional
#         indexes : specifies a list of columns/attributes which will be indexed in the resulting rmo. sweep_params are indexed by default.

#         pks : columns that will work as primary key
#         filter_func: to mask rows/instances from each rmo ...why? sometimes we have -1 as entry to denote not selected, don't want to include those in the statistics
#         agg_func: apply an aggregation before storing..often there is no need to  store instance level records.
#     '''

#     #####################################
#     #get the list of sweep parameters and all the replicates 
#     ###################################
    

#     all_replicates_data_rmo = rmo_iter
#     if filter_func is not None:
#         all_replicates_data_rmo = [filter_func(model=rmi) for rmi in all_replicates_data_rmo]

#     if agg_func is not None:
#         all_replicates_data_rmo = [agg_func(model=rmi) for rmi in all_replicates_data_rmo]


#     #primary key of the aggregate table
#     if pks is None:
#         pks = vam.get_pkeys(session, all_replicates_data_rmo[0])
#     print "pks = ", pks

#     all_replicates_rmo  = ex.materialize_rmo_bevy(session, all_replicates_data_rmo, name_prefix=name_prefix, indexes = indexes , pks =  pks)
#     return all_replicates_rmo


def unify_studycfg_rmos(session = None, studycfg_root = None, rmo_desc=None, doe_iter=None,   indexes=[], pks=None, filter_func = None,  annotate_func=None, agg_func=None,  out_desc=None):
    '''
    merge all  rmos as a single rmo; required for efficiancy and export to pandas dataframe
    prelim/context:
        Replicate rmo  are named as follows: <cfg_label>_<rmo_desc>.py.
        For example, rmo_desc is "block_daily_diagnosed", where maintains number of diagnosed per block per day during a simulation".
        Now the rmo for a replicate corresponding to experiment label "c_0.5_r_1" is called "c_0.5_r_1_block_daily_diagnosed". 

    input:
        studycfg_root : a xml tree representing the design of a study.
        rmo_desc : defines the domain of this operation i.e., the set of all rmos in cfgsweepset that will be merged as one.
        model_selector : a list of bools (for e.g., use to remove experiments that didn't run correctly), is optional
        indexes : specifies a list of columns/attributes which will be indexed in the resulting rmo. sweep_params are indexed by default.

        pks : columns that will work as primary key
        filter_func: to mask rows/instances from each rmo ...why? sometimes we have -1 as entry to denote not selected, don't want to include those in the statistics
        agg_func: apply an aggregation before storing..often there is no need to  store instance level records.
    '''

    #####################################
    #get the list of sweep parameters and all the replicates 
    ###################################
    
    #add "_" to rmo_desc if not present
    if not rmo_desc.startswith('_'):
        rmo_desc='_' + rmo_desc
    #get the list of all classes
    sweep_params = rau.get_sweep_params(studycfg_root)

    if doe_iter is None:
        doe_iter  = deu.get_doe_iter(studycfg_root)
        
    annotated_model_iter = rau.annotate_model_domain_attr_value(session, rmo_desc, doe_iter)
    
    #if model_selector is not None:
    #all_replicates_data_rmo = [rmi for rmi,is_selected in zip(annotated_model_iter, model_selector) if is_selected]

    if out_desc is None:
        out_desc = rmo_desc
        
    if filter_func is None:
        filter_func = lambda x: x
        
    # transform_func = lambda x: x
    # if filter_func is not None:
    #     transform_func = lambda x: filter_func(x)

    if annotate_func is None:
        step2_func = filter_func
    else:
        step2_func = lambda x: annotate_func(filter_func(x))
        
    # if annotate_func is not None:
    #     old_transform_func = copy.deepcopy(transform_func)
    #     transform_func = lambda x: annotate_func(old_transform_func(x))

    if agg_func is None:
        step3_func = step2_func
    else:
        step3_func = lambda x: agg_func(step2_func(x))
        
    # if agg_func is not None:
    #     old_transform_func = copy.deepcopy(transform_func)
    #     transform_func = lambda x: agg_func(old_transform_func(x))


    #transformed_rmo_iter = rau.model_transform_iter_c(annotated_model_iter, annotated_model_iter,  transform_func)
    transformed_rmo_iter = rau.model_transform_iter_c(annotated_model_iter, annotated_model_iter,  step3_func)

    
    #if filter_func is not None:
    #    all_replicates_data_rmo = [filter_func(model=rmi) for rmi in all_replicates_data_rmo]

    #if agg_func is not None:
    #    all_replicates_data_rmo = [agg_func(model=rmi) for rmi in all_replicates_data_rmo]



    out_rep_rmo_iter = rau.proj_rmo_iter_c(session, transformed_rmo_iter)  #from rep_info pick only the rmo_model

        
    assert(sweep_params is not None)
    sid = xu.get_value_by_attr(studycfg_root, 'run/sid')
    name_prefix='sid_'+ str(sid) + '_all_replicates_' + out_desc
    
    all_replicates_rmo  = ex.materialize_rmo_bevy_iter(session, out_rep_rmo_iter, name_prefix=name_prefix, indexes = indexes + sweep_params)
    session.commit()
    return all_replicates_rmo



def plot_studycfg_rmos_stats_by_grouping(session=None, all_runs_rmo=None, cell_attrs=[], rep_attr=None, day_attr=None, group_attr=None, event_count_attr=None, event_count_attr_label=None, group_measure_rmo = None, group_measure_attr=None,  ylabel=None, xlabel='day', plot_name=None): 
    '''
    prelim/context : the function assumes  an rmo with attributes [cell_attrs, rep_id, day_attr, group_attr, event_attr]. It will compute avg. count over the event attr and do a scatter plot
    the idea here is to do scatter plot -- there are group (collection of people), for each group there is a measure (pop sz). 
    this does scatter plot for avg. diagnosed count vs. group-measure
    '''
    
    #count event  per replicate -- keep cell_attrs, rep_attr, group_attr,  drop day
    #don't need event_attr because we are doing count
    
    event_count_sum_attr = 'sum_' + event_count_attr_label
    event_count_by_studycfg_group = vapil.aggregate_sum(session, all_runs_rmo, sum_by_attr=cell_attrs + [rep_attr, group_attr], sum_on_attr=event_count_attr, aggLabel=event_count_sum_attr)
    
    # compute min,avg, max across replicate -- drop replicate
    event_count_stats_by_studycfg_group = vapil.aggregate_min_avg_max(session, event_count_by_studycfg_group, agg_on_attr=event_count_sum_attr,   agg_by_attr = cell_attrs + [group_attr]) 
    

    #merge studycfg stats per group with group measure i.e. for each row of studycfg stat at the corresponding group measure
    event_count_stats_by_studycfg_group_with_group_measure = vajl.fuseEQ(session, event_count_stats_by_studycfg_group,  group_measure_rmo, [group_attr], [group_attr], relable_common_attr=True)
    

    #collect data as array
    event_count_stats_by_studycfg_group_arr = vapil.aggregate_array(session, rmo=event_count_stats_by_studycfg_group_with_group_measure, arr_attrl=['min_' + event_count_sum_attr, 'avg_' + event_count_sum_attr , 'max_' + event_count_sum_attr, 'o_' + group_attr, group_measure_attr], agg_key=cell_attrs) 

    all_result_errb = {}
    for rec in vapi.scan(session, event_count_stats_by_studycfg_group_arr):
        groups = rec._asdict()['array_' + 'o_' + group_attr] #because join relabels same attribute
        mins = rec._asdict()['array_min_'+ event_count_sum_attr]
        maxs = rec._asdict()['array_max_'+ event_count_sum_attr]
        avgs = rec._asdict()['array_avg_'+ event_count_sum_attr]
        measures = rec._asdict()['array_'+ group_measure_attr]
        #a standing bug in aggregate that doesn't keep the array sorted by day
        title="diagnosed_vs_block_sz"  
        label=""
        for cell_param in cell_attrs:
            cell_param_val = rec._asdict()[cell_param]
            title += Template("${cell_param}.eq.${cell_param_val}_").substitute(locals())
            label +=Template("${cell_param}=${cell_param_val}:").substitute(locals())
        result = {}
        result = {'xValues': measures,
                  'yValues': avgs,
                  'yLabel' : xlabel,
                  'xLabel' : ylabel
                  }
        vapip.plot_scatter(result, title[:-1])
#         result_errb = {'xValues': days,
#                   'yValues': [float(a) for a in avgs], 
#                   'yLabel' : 'avg ' + count_attr_label + ' by day' ,
#                   'yMinvals' : mins,
#                   'yMaxvals' : maxs,
#                   }
        #all_result_errb[label[:-1]] = result_errb
    #vapip.plot_X_vs_Ys_with_error_bar(all_result_errb, 'num_' + count_attr_label +'_daily',  xlabel='day', ylabel='#num_'+count_attr_label)

    
              
    


def plot_studycfg_rmos_stats_daily_count(session=None, all_runs_rmo=None, cell_attrs=[], count_attr=None, count_attr_label='infected', day_attr=None, ylabel=None, xlabel='day', plot_name=None): 
    '''
    prelim/context: a set of runs with same expcfg. 

    description: Compute and plot  stats on daily event count over a set of runs from same expcfg
    all_runs_rmo: A single rmo derived from merging all the rmo of a run.  Rows corresponding to each rmo represents event count by day.
    cell_attrs : attribute/parameter/column collection (including rep id) that collectively define a cell -- much like primary key of the database
    count_attr : attribute that denotes  event count (e.g. num person infected) 
    day_attr : attribute that denotes the day of the simulation
    TODO : what is event, day
    '''
    agg_on_attr = count_attr
    # derive aggregates (min, max, avg) on daily count (attr_label: count_attr) by cells (attr_label: cell_attrs). 
    stats_by_sweep_param_and_day =  vapil.aggregate_min_avg_max(session, all_runs_rmo, agg_on_attr=agg_on_attr, agg_by_attr = cell_attrs + [day_attr]) 
    
    #collect them as array
    agg_array_by_sweep_param = vapil.aggregate_array(session, rmo=stats_by_sweep_param_and_day, arr_attrl=['min_' + agg_on_attr, 'avg_' + agg_on_attr , 'max_' + agg_on_attr, 'day'], agg_key=cell_attrs) 

    all_result_errb = {}
    for rec in vapi.scan(session, agg_array_by_sweep_param):
        days = rec._asdict()['array_day']
        mins = rec._asdict()['array_min_'+agg_on_attr]
        maxs = rec._asdict()['array_max_'+agg_on_attr]
        avgs = rec._asdict()['array_avg_'+agg_on_attr]
        #a standing bug in aggregate that doesn't keep the array sorted by day
        zipped = zip(days, mins, maxs, avgs)
        zipped.sort()
        days, mins, maxs, avgs = zip(*zipped)
        title="daily_" + count_attr_label
        label=""
        for cell_param in cell_attrs:
            cell_param_val = rec._asdict()[cell_param]
            title += Template("${cell_param}.eq.${cell_param_val}_").substitute(locals())
            label +=Template("${cell_param}=${cell_param_val}:").substitute(locals())
        result = {}
        result = {'xValues': days,
                  'yValues': [mins, avgs, maxs],
                  'yLabels' : ['mins', 'avgs', 'maxs']
                  }
        result_errb = {'xValues': days,
                  'yValues': [float(a) for a in avgs], 
                  'yLabel' : 'avg ' + count_attr_label + ' by day' ,
                  'yMinvals' : mins,
                  'yMaxvals' : maxs,
                  }
        all_result_errb[label[:-1]] = result_errb
        #vapip.plot_X_vs_Ys(result, title=label,  xlabel='day', ylabel='#num_infections')
    vapip.plot_X_vs_Ys_with_error_bar(all_result_errb, 'num_' + count_attr_label +'_daily',  xlabel='day', ylabel='#num_'+count_attr_label)



def generalized_attack_rate(session=None, all_replicates_num_=None, agent_state_count_attr=None, sweep_params=None, pop_sz=None):
    '''
    all_replicates_num_infected: for each cell/rep/day report num_diagnosed/infected
    agent_state_attr: the attribute that defines the state of the agent, e.g. diagnosed/infected
    agent_state_count_attr: the attribute that represent aggrgegated value  of the count attribute
    
    '''
    cummulative_infected = vapil.aggregate_sum(session, all_replicates_num_infected, attr_num_infected,  sweep_params, 'total_infected')
    x1 = vapi.add_const_column(session, cummulative_infected_till_today, str(pop_sz), 'pop_sz')
    agg_attr_label='attack_rate'
    x2 = vapi.div_attrs(session, x1, 'total_infected', 'pop_sz', agg_attr_label)
    stats_by_sweep_param =  vapil.aggregate_min_avg_max_stddev(session, x2, agg_on_attr=agg_attr_label, agg_by_attr= sweep_params[:-1]) #aggregation over replicates
    agg_array_by_sweep_param = vapil.aggregate_array(session, rmo=stats_by_sweep_param, arr_attrl=['min_' + agg_attr_label, 'max_' + agg_attr_label, 'avg_' + agg_attr_label, 'stddev_' + agg_attr_label], agg_key=sweep_params[:-1]) 
    result = {}
    for rec in vapi.scan(session, agg_array_by_sweep_param):
        mins = rec._asdict()['array_min_'+agg_attr_label]
        maxs = rec._asdict()['array_max_'+agg_attr_label]
        avgs = rec._asdict()['array_avg_'+agg_attr_label]
        stddevs = rec._asdict()['array_stddev_'+agg_attr_label]
        
        title=""
        for sweep_param in sweep_params[:-1]:
            sweep_param_val = rec._asdict()[sweep_param]
            title += Template("${sweep_param}.eq.${sweep_param_val}_").substitute(locals())
        print "cell = ", title[:-1], " attack rate=", float(avgs[0]), "stddevs = ", stddevs[0]
        result[title[:-1]] = float(avgs[0])
    #vapip.plot_bars(result, "attack_rate", "cell description", "attack rate")


# def plot_cfgsweepset_stats_daily_instances(session=None, all_rmos=None, cell_attrs=[], rep_attr=None, inst_attr=None, inst_attr_label='infected', day_attr=None, ylabel=None, xlabel='day', plot_name=None):
#       '''
#     description: Compute and plot  stats on daily event count over a given set of replicates.
#     precondition: schema  across the rmo in all_rmos should be homogenous. 
#     all_rmos: A collection of rmos. Each rmo stores event count 
#                          coun over which the aggregate statistics is to be computed.
#     cell_attrs : attribute/parameter/column collection (including rep id) that collectively define a cell -- much like primary key of the database
#     rep_attr : attribute describe the replicate id
#     count_attr : attribute that denotes  event count (e.g. num person infected) 
#     day_attr : attribute that denotes the day of the simulation
#     TODO : what is event, day
#     '''
#       count_attr = 'num_'+ inst_attr_label
#       num_instances_by_day = vapil.aggregate(session, all_rmos , agg_by_attr=cell_attrs + [rep_attr, day_attr], aggLabel=count_attr)
#       plot_cfg_sweepset_stats_daily_count(session=session, all_rmos = all_rmos, cell_attrs, count_attr=count_attr, count_attr_label=count_attr, day_attr=day_attr, ylabel=ylabel, xlabel=xlabel, plot_name=plot_name)


# def plot_cfgsweepset_stats_daily_partitioned_count(session=None, all_rmos=None, cell_attrs=[], rep_attr=None, partitioned_count_attr=None, partition_count_attr_label='num_infected', day_attr=None, ylabel=None, xlabel='day', plot_name=None):
#       '''
#     description: Compute and plot  stats on daily event count over a given set of replicates.
#     precondition: schema  across the rmo in all_rmos should be homogenous. 
#     all_rmos: A collection of rmos. Each rmo stores event count 
#                          count over which the aggregate statistics is to be computed.
#     cell_attrs : attribute/parameter/column collection (including rep id) that collectively define a cell -- much like primary key of the database
#     rep_attr : attribute describe the replicate id
#     partitioned_count_attr : attribute that denotes  event count (e.g. num person infected) 
#     day_attr : attribute that denotes the day of the simulation
#     TODO : what is event, day
#     '''
#       #Need to think what to plot for the partitions 
#       #we can do epicurves per partition..what if there are too many partitions..then plot histograms
#       #num_instances_by_day = vapil.aggregate_sum(session, all_rmos , sum_by_attr=cell_attrs + [rep_attr, day_attr], sum_on_attr= aggLabel=count_attr)
#       #plot_cfg_sweepset_stats_daily_count(session=session, all_rmos = all_rmos, cell_attrs, count_attr=count_attr, count_attr_label=count_attr, day_attr=day_attr, ylabel=ylabel, xlabel=xlabel, plot_name=plot_name)


