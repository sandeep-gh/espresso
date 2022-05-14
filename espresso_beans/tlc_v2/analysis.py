#attack rate by cell
import sys
import xmlutils as xu
import analysis as ana
import utilities
import epistudy_cfg as ec
import versa_core.utils as utils
import versa_utils as vu
import generalized_analysis_impl as gai

last_config_fn = utilities.get_last_file_by_pattern("sid_*.xml")
session_name = vu.get_latest_dbsession(last_config_fn)
session = vu.build_session(session_name)
cfg_root = xu.read_file(last_config_fn)
region = ec.get_study_region(cfg_root)
[person_rmo] = utils.load_rmos([region + "_person_info"])
attack_rate_df = gai.attack_rate_by_cell(session, cfg_root,  person_rmo=person_rmo)
