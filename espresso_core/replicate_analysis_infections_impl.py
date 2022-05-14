import versa_utils as vu
import versa_api_plot as vapip
import versa_api as vapi
import versa_api_analysis as vapia
import replicate_analysis_utils as rau

def plot_total_diagnosed_vs_daily(cfg_root=None, param_root=None, replicate_desc=None, rep_dir=None, args=None):
    session = args[0]
    model_obj = rau.get_replicate_model_obj(replicate_desc, '_infections')
    res = vapia.build_distribution_X_vs_agg_Y(session = session, model =model_obj,  agg_by= 'day', agg_on= 'infections')
    vapip.plot_X_vs_Y(res, replicate_desc+'infections_per_day', 'day', '#infections')
    return


def plot_diagnosed_daily_all_replicates(session=None, all_replicate_models=None):
    all_reps_stmt =None
    for rep_model in all_replicate_models:
        stmt = vapia.build_stmt_X_vs_agg_Y(session = session, model = rep_model,  agg_by= 'day', agg_on= 'infections', agg_label='daily_infection_count')
        all_reps_stmt = vapi.set_union(session, all_reps_stmt, stmt, keep_duplicates=True, preserve_column_name=True)

    res_stmt = vapia.build_stmt_X_vs_agg_min_avg_max_Y(session = session, rmo =all_reps_stmt,  agg_by_attr= 'day', agg_on_attr= 'daily_infection_count')
    agg_on_attr = 'daily_infection_count'

    days= []
    mins = []
    avgs = []
    maxs = []
    for rec in vapi.scan(session, res_stmt):
        days.append(rec._asdict()['day'])
        mins.append(rec._asdict()['min_'+agg_on_attr])
        avgs.append(rec._asdict()['avg_'+agg_on_attr])
        maxs.append(rec._asdict()['max_'+agg_on_attr])
    result = {'xValues': days,
              'yValues': [[x for x in mins], avgs, [x for x in maxs]]
              }
    vapip.plot_X_vs_Ys(result, 'diagnosed_daily_summary', 'day', '#infections')
    return result
