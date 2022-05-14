import check_sim_runs_impl as csrl
import sys 
import utilities

if len(sys.argv) > 1:
    cfg_file=sys.argv[1]
else:
    cfg_file = utilities.get_last_file_by_pattern("sid_[0-9]*.xml")

[total_replicates, num_failed, model_selector] = csrl.check_sim_runs_impl(cfg_file)
if num_failed == 0:
    print "all replicates completed successfully"
else:
    print str(num_failed) + "/" + str(total_replicates) + " replicates failed"
