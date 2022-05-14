fn=$1
while [ 1 == 1 ]
do
   if [ -f $fn ]
   then
       break
   fi
   sleep 5
done
