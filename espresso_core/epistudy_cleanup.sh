#!/bin/bash

dicex_epistudy_dir=`dirname $0`
echo "performing remote cleanups..."
python ${dicex_epistudy_dir}/epistudy_cleanup.py $1
mkdir -p trash
echo "removing model files..."
mv *model.py *model.pyc    trash/ 2>/dev/null
rm .x.py 2>/dev/null
rm import_header.py  2>/dev/null
