import epistudy_cfg as ec
import xmlutils as xu
import sys
import os
import imp

module_dir=os.path.dirname(os.path.realpath(__file__))
def get_doe_generator(cfg_root):
    doe_type = xu.get_value_elem(cfg_root, 'doe/design/type')
    print "doe_type = ", doe_type
    doe_module_dir = module_dir
    if  xu.has_key(cfg_root, 'doe/design/module_dir'):
        doe_module_dir = xu.get_value_elem(cfg_root, 'doe/design/module_dir')
        
    try:
        sys.path.append(doe_module_dir)
        imp.find_module(doe_type + "_doe_generator")
        doe_generator = __import__(doe_type+ "_doe_generator")
    except ImportError:
        found=False
        print ("cannot find  doe generator " + doe_type)
        assert(0)
    return getattr(doe_generator, 'doe_generator')
        
