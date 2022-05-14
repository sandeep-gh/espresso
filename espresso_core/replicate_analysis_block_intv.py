import os
import sys
import epistudy_cfg as ec
import replicate_visitor as rv
import replicate_analysis_block_intv_impl as rai
import versa_api_utils as vapiu

module_dir=os.path.dirname(os.path.realpath(__file__))
cfg_file=sys.argv[1]
cfg_root = ec.read_epistudy_cfg(cfg_file)
dbsession = ec.get_dbsession(cfg_root)
session = vapiu.build_session(dbsession)
rv.visit_replicates(cfg_root=cfg_root, method=rai.plot_total_diagnosed_vs_daily, args=[session])

#############################################################
##plot spread across replicates for daily diagnose counts ###
#############################################################
all_replicate_models = rv.get_all_replicate_models(session, cfg_root,'_block_daily_diag_count')
res = rai.plot_diagnosed_daily_all_replicates(session, all_replicate_models)


