import epistudy_analysis_api as eaa



doe_id = None

one_replicate = eaa.export_replicate_results(session, doe_id=doe_id, rep_id='aa_0')

remove_non_intervened_func = (lambda model=None: re.filterNEQ(session, model, 'intervened', -1))
all_replicates_in_doe = eaa.export_doe_replicate_results(session, doe_id=doe_id, dataset_tags = ["intv", "infection_trace"], filter_funcs=[remove_non_intervened_func, None])

