# import epistudy_cfg as ec

# import sys

# cfg_root = ec.read_epistudy_cfg(sys.argv[1])
# doe_generator.all_in_one(cfg_root)
# #doe = doe_generator([cfg_root, cfg_root, '', None])

import psycopg2 as pgsai
import epistudy_cfg as ec
import dicex_epistudy_utils as deu
import sys
import pgsa_utils as pgu
import versa_api as vapi
import xmlutils as xu
import launch_epifast_jobs as lej
from itertools import chain, imap
from lhs_doe_generator import doe_generator
#import lhs_doe_generator as doe_generator
import  collections


def prepare_config_files(cfg_root=None, replicate_desc=None, replicate_dir=None):
    print cfg_root, replicate_dir 

def prepare_config_files_iter(args):
    prepare_config_files(args[0], args[1], args[2])

cfg_root = ec.read_epistudy_cfg(sys.argv[1])
domain_iter = xu.get_elem_iter(cfg_root, 'domain/sweep')
doe = doe_generator([cfg_root, domain_iter, '', None])
collections.deque(imap(prepare_config_files_iter,doe), maxlen= 0) #call prepare_config_files for each cfg of the doe

