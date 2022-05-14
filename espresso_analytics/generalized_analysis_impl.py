#Readme: codifies the patterns/abstractions underlying
#various types of analysis (attack rate, attack_rate_by_region, etc.)
#used for simulations


from string import Template
import versa_utils as vu
import xmlutils as xu
import versa_core.relational as re
import versa_core.export as ex
import versa_core.schema as sc
import versa_core.plot as plt
import check_sim_runs_impl as csri
import epistudy_analysis_api as eaa
import replicate_analysis_utils as rau
import versa_api_list as vapil
import dicex_epistudy_utils as deu

def generalized_analysis(session, cfg_root):
    person_model = xu.get_value_by_attr(cfg_root, 'analysis/mappings/persons')
    person_info = vu.import_model(person_model)
    pop_sz = vapi.cardinality(session, person_info)
    #functor that will find attack rate for each replicate
    compute_attack_rate = (lambda model=None: vapi.div_const(session, vapi.aggregate_countall(session, model, 'total_infections'), 'total_infections', divisor=pop_sz, out_attr='attack_rate'))
    
    #collect all the replicate result as one table
    all_attack_rates = eaa.unify_rmos(session=session, cfg_root=cfg_root, rmo_desc="_infection_trace", pks=[], filter_func=None, agg_func=compute_attack_rate)
    
    #build attack rate --scatter plot
    all_attack_rates = vapil.aggregate_avg_stddev(session, all_attack_rates, zip_attrss=param_attrs, summary_attr='attack_rate')


#enum=>total count=>replicates
def attack_rate_by_cell(session=None, studycfg_root=None, daily_infected_rmo_base_name = 'infection_trace', filter_func =None, person_rmo=None):
    '''
    '''
    sid = xu.get_value_by_attr(studycfg_root, 'run/sid')
    sweep_params = rau.get_sweep_params(studycfg_root)
    pop_sz = re.cardinality(session, person_rmo)

    #fix for failed replicates 
    #[total_replicates, num_failed, model_selector] = csri.check_sim_runs_impl(studycfg_root) #returns which replicates have failed

    doe_iter  = deu.get_doe_iter(studycfg_root)
    completed_runs_iter = rau.filter_failed_runs_iter_c(session, doe_iter)
    
    enum_to_totalcount = (lambda model=None: vapil.aggregate_count(session, model, sweep_params, 'total_infected'))
    all_replicates_total_infected = eaa.unify_studycfg_rmos(session, studycfg_root, rmo_desc=daily_infected_rmo_base_name, doe_iter=completed_runs_iter,   filter_func = filter_func, agg_func= enum_to_totalcount, pks=[], out_desc="sid_" + sid + "_attack_rate_by_replicates")
    #compute rate
    x1 = sc.add_float_const_column(session, all_replicates_total_infected, str(pop_sz), 'pop_sz') 
    print re.cardinality(session, x1)
    x2 = re.div_attrs(session, x1, 'total_infected', 'pop_sz', 'attack_rate')

    stats_by_sweep_param =  vapil.aggregate_min_avg_median_max_stddev(session, x2, agg_on_attr='attack_rate', group_by_attrl= sweep_params[:-1])
    attack_rate_df = ex.export_as_dataframe(session, stats_by_sweep_param)
    attack_rate_rmo = ex.materialize_rmo(session, stats_by_sweep_param, name_prefix='sid_'+sid +  '_attack_rate_stat')
    
    return [attack_rate_rmo, attack_rate_df]


def attack_rate_by_category(session=None, studycfg_root=None, daily_infected_rmo_base_name = 'infection_trace', category_info_rmo=None,  category_stat_rmo=None, category_attr=None, popsz_attr = None, filter_func= None, name_prefix=None):
    '''
    rmo_iter: lists all the replicate rmo that are part of this analysis 
    region_stat_rmo: rmo that lists population size of each region

    '''
    sid = xu.get_value_by_attr(studycfg_root, 'run/sid')
    sweep_params = rau.get_sweep_params(studycfg_root)
    print "sweep_params ", sweep_params
    
    annotate_category_func = (lambda model=None: re.fuseEQ(session, category_info_rmo, model,  'pid', 'transmitee_pid'))
    enum_to_totalcount = (lambda model=None: vapil.aggregate_count(session, model, [category_attr] + sweep_params, 'total_infected'))

    doe_iter = deu.get_doe_iter(studycfg_root)
    completed_runs_iter = rau.filter_failed_runs_iter_c(session, doe_iter)
    
    
    all_replicates_total_infected = eaa.unify_studycfg_rmos(session = session, studycfg_root=studycfg_root, rmo_desc=daily_infected_rmo_base_name, doe_iter=completed_runs_iter,  filter_func=filter_func, annotate_func = annotate_category_func, agg_func=enum_to_totalcount, pks=[category_attr], out_desc=name_prefix + '_total_infected_by_county_day_100')


    #indexes = [region_attr] + sweep_params, filter_func = None,  agg_func=enum_to_totalcount, name_prefix=name_prefix)

    stmt = re.fuseEQ(session, all_replicates_total_infected, category_stat_rmo, category_attr, category_attr)
    stmt = re.div_attrs(session, stmt, 'total_infected', 'popsz', 'attack_rate')
    stats_by_sweep_param =  vapil.aggregate_min_avg_median_max_stddev(session, stmt, agg_on_attr='attack_rate', group_by_attrl= [category_attr] + sweep_params[:-1])
    attack_rate_df = ex.export_as_dataframe(session, stats_by_sweep_param)
    attack_rate_rmo = ex.materialize_rmo(session, stats_by_sweep_param, name_prefix=name_prefix + '_attack_rate')
    return [attack_rate_rmo, attack_rate_df]




def attack_rate_by_day_and_category(session=None, studycfg_root=None, daily_infected_rmo_base_name = 'infection_trace', category_info_rmo=None,  category_stat_rmo=None, category_attr=None, popsz_attr = None, day_rmo=None, day_attr=None, res_rmo_desc=None):
    '''
    rmo_iter: lists all the replicate rmo that are part of this analysis 
    region_stat_rmo: rmo that lists population size of each region

    '''
    sid = xu.get_value_by_attr(studycfg_root, 'run/sid')
    sweep_params = rau.get_sweep_params(studycfg_root)
    print "sweep_params ", sweep_params

    #annotate by upto limit day and category
    annotate_category_func = (lambda model=None: re.fuseEQ(session, category_info_rmo,
                                                           re.fuseLTE(session, model, day_rmo, 'infection_time', day_attr),
                                                           'pid', 'transmitee_pid'))

    enum_to_totalcount = (lambda model=None: vapil.aggregate_count(session, model, [category_attr, day_attr] + sweep_params, 'total_infected'))

    doe_iter = deu.get_doe_iter(studycfg_root)
    completed_runs_iter = rau.filter_failed_runs_iter_c(session, doe_iter)
    
    
    all_replicates_total_infected = eaa.unify_studycfg_rmos(session = session, studycfg_root=studycfg_root, rmo_desc=daily_infected_rmo_base_name, doe_iter=completed_runs_iter,  filter_func=None, annotate_func = annotate_category_func, agg_func=enum_to_totalcount, pks=[category_attr], out_desc='total_infected_by_category_and_day')


    #indexes = [region_attr] + sweep_params, filter_func = None,  agg_func=enum_to_totalcount, name_prefix=name_prefix)

    stmt = re.fuseEQ(session, all_replicates_total_infected, category_stat_rmo, category_attr, category_attr)
    stmt = re.div_attrs(session, stmt, 'total_infected', 'popsz', 'attack_rate')
    stats_by_sweep_param =  vapil.aggregate_min_avg_median_max_stddev(session, stmt, agg_on_attr='attack_rate', group_by_attrl= [category_attr, day_attr] + sweep_params[:-1])
    sid = xu.get_value_by_attr(studycfg_root, 'run/sid')
    name_prefix='sid_'+ str(sid) + "_" + res_rmo_desc
    attack_rate_rmo = ex.materialize_rmo(session, stats_by_sweep_param, name_prefix=name_prefix)
    attack_rate_df = ex.export_as_dataframe(session, stats_by_sweep_param)

    return [attack_rate_rmo, attack_rate_df]




#enum=>daily count=>replicates
def plot_daily_enumerated(session=None, studycfg_root=None, rmo_base_name=None, day_attr=None, enum_attr=None, category_attrl=None, plotcontext=None):
    """
    category_attrl overrides sweep_params
    """
    sweep_params = rau.get_sweep_params(studycfg_root)
    #fix for failed replicates 
    [total_replicates, num_failed, model_selector] = csri.check_sim_runs_impl(studycfg_root) #returns which replicates have failed

    enum_to_count = (lambda model=None: vapil.aggregate_count(session, model, sweep_params + [day_attr], 'day_count'))
    #collect all replicate data in one table
    all_replicates_day_count = eaa.unify_studycfg_rmos(session, studycfg_root, rmo_desc=rmo_base_name, agg_func= enum_to_count, model_selector=model_selector, pks=[day_attr])
    plot_daily_count_impl(session=session, studycfg_root=studycfg_root, all_replicates_day_count=all_replicates_day_count, day_attr=day_attr, count_attr='day_count', category_attrl=category_attrl, plotcontext=plotcontext)



#enum=>daily count=>replicates
def plot_daily_count(session=None, studycfg_root=None, rmo_base_name=None, day_attr=None, count_attr=None, category_attrl=None, plotcontext=None):
    """
    category_attrl overrides sweep_params -- should not include day_attr
    """
    #collect all replicate data in one table
    #fix for failed replicates 
    [total_replicates, num_failed, model_selector] = csri.check_sim_runs_impl(studycfg_root) #returns which replicates have failed
    all_replicates_day_count = eaa.unify_studycfg_rmos(session, studycfg_root, rmo_base_name, model_selector=model_selector, agg_func= None)
    plot_daily_count_impl(session=session, studycfg_root=studycfg_root, all_replicates_day_count=all_replicates_day_count, day_attr=day_attr, count_attr=count_attr, category_attrl=category_attrl, plotcontext=plotcontext)


def plot_daily_count_impl(session=None, studycfg_root=None, all_replicates_day_count=None, day_attr=None, count_attr=None, category_attrl=None, plotcontext=None):

    #compute states over daily count
    agg_on_attr = count_attr
    sweep_params = rau.get_sweep_params(studycfg_root)
    group_by_attrl =  [] 

    if category_attrl is None:
        group_by_attrl = sweep_params[:-1] 
    else:
        group_by_attrl = group_by_attrl + category_attrl
    stmt = vapil.aggregate_min_avg_max_stddev(session, all_replicates_day_count, group_by_attrl=group_by_attrl+[day_attr], agg_on_attr=agg_on_attr)
    daily_count_stats = stmt #vapil.ascending(session, stmt,  group_by_attrl) #because Sqlalchemy has bug where scending followed by aggregate_array  this does not work


    plt.initplot(plotcontext)
    daily_count_stats_agg = vapil.aggregate_array(session, rmo=daily_count_stats, agg_on_attrl=['min_' + agg_on_attr, 'avg_' + agg_on_attr , 'max_' + agg_on_attr, day_attr],  group_by_attrl=group_by_attrl) 

    print daily_count_stats_agg.c.keys()
    all_result_errb = {}
    for rec in ex.scan(session, daily_count_stats_agg):
        days = rec._asdict()['array_'+ day_attr]
        mins = rec._asdict()['array_min_'+agg_on_attr]
        maxs = rec._asdict()['array_max_'+agg_on_attr]
        avgs = rec._asdict()['array_avg_'+agg_on_attr]
        #a standing bug in aggregate that doesn't keep the array sorted by day
        zipped = zip(days, mins, maxs, avgs)
        zipped.sort()
        days, mins, maxs, avgs = zip(*zipped)

        title="num_daily_" 
        label=""
        for cell_param in group_by_attrl:
            cell_param_val = rec._asdict()[cell_param]
            title += Template("${cell_param}.eq.${cell_param_val}_").substitute(locals())
            label +=Template("${cell_param}=${cell_param_val}:").substitute(locals())

        label = label[:-1]
        plt.plot_data(days, avgs,  label=label)
        #plt.plot(session, daily_count_rmo, day_attr, 'avg_day_count', label=label)
        #plt.plot(session, daily_count_rmo, day_attr, 'max_day_count', label=label)
        #plt.plot(session, daily_count_rmo, day_attr, 'min_day_count', label=label)

    plt.saveplot(plotcontext=plotcontext)


    

