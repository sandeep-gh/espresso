import versa_core.utils as vcu
import versa_core.relational as re
import versa_core.schema as sch
import versa_core.export as ex

def evaluate(session=None, cfg_root=None, replicate_desc=None, today=None):
    print replicate_desc
    [attack_rate_model] = vcu.load_rmos([replicate_desc +"_attack_rate_by_day"])
    stmt = sch.proj(session, re.filterEQ(session, attack_rate_model, 'day', today), ['attack_rate'])
    rate_today = ex.scan_singleton(session, stmt)
    return rate_today[0] #it has only one column
