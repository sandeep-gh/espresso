#!/bin/bash

dicex_epistudy_dir=`dirname $0`
python ${dicex_epistudy_dir}/epistudy_workflow.py $1
echo "moving to  dbhost machine...(type exit to return back)"
to_dbhost