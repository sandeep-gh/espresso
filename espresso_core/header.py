import sys
from sqlalchemy import Column, Integer, String,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship,backref
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

Base = declarative_base()

from itertools import izip

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)

def deco_param_sweep(cls):
    return cls

# def deco_param_sweep(cls):
#     cls_name = cls.__name__
#     rep_cfg  = cls_name.split('_r_')[0]
#     for par,val in pairwise(rep_cfg.split('_')):
#         @hybrid_property
#         def afunc(self):
#             return val
#         afunc.__doc__ = "getters for parameter attributes"
#         afunc.__name__= par
#         setattr(cls, afunc.__name__, afunc)
#     return cls


# def deco_param_sweep(session,cls):
#     cls_name = cls.__name__
#     rep_cfg  = cls_name.split('_r_')[0]
#     for par,val in pairwise(rep_cfg.split('_')):
#         cls = vapi.add_const_column(session, cls, val, par)
#     return cls


