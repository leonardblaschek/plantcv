# define the date of germination for DPG (days past germination) calculation
germination="20200523"

# assign the starting number of the sequentially numbered trays
start=2

# assign the last number of the sequentially numbered trays
end=4

# rename images by DPG and tray number
a=$start

for i in *.jpg; do
  var1="_"
  DPG=$(( ($(date -r "$i" +%s) - $(date --date=$germination +%s) )/(60*60*24) ))
  mv -i -- "$i" "$DPG$var1$a.jpg"
  if [ "$a" -lt $end ]
  then
    let a=a+1
  else
    let a=$start
  fi
done
