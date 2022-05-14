dicex_base_dir=$1
cluster_name=$2
cfg_fn=$3
module_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" 
. ${dicex_base_dir}/dicex_${cluster_name}.sh
python $module_dir/postdb.py ${cfg_fn}
