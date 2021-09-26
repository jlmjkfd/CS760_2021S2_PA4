#!/bin/bash

#output_file_name="PA4DATA"
output_file_name="PA4DATA_nobrand"

temp_file_name="temp.csv"

> "./selected/"$output_file_name".csv"
> "./selected/"$temp_file_name

for file in `ls *.csv`
do 
# id time tweet search
## awk -F'\t' -e '{split(FILENAME,fname,".");OFS="\t"; print $1,$3,$11,fname[1]}' $file >> "./selected/"$temp_file_name
# time tweet
awk -F'\t' -e '{OFS="\t"; print $3,$11}' $file >> "./selected/"$temp_file_name
done

#cat $temp_file_name | awk '!a[$0]++{print}'

# remove non-Eng, sort, uniq
#   reverse
## grep -P "\ten\t" $temp_file_name | sort -k3 -r | uniq | tee -a $output_file_name"_daily.csv"
#   normal
# id time tweet search
## awk -F'\t' -e 'NR==1{OFS="\t"; print $1,$2,$3,"searchBrand"}' "./selected/"$temp_file_name | tee -a "./selected/"$output_file_name".csv"
## awk -F'\t' -e '$1 !~ /id/' "./selected/"$temp_file_name | sort -k2 | tee -a "./selected/"$output_file_name".csv"

# time tweet
awk -F'\t' -e 'NR==1' "./selected/"$temp_file_name | tee -a "./selected/"$output_file_name".csv"
awk -F'\t' -e '$1 !~ /created_at/' "./selected/"$temp_file_name | sort -k1 | uniq | tee -a "./selected/"$output_file_name".csv"

rm "./selected/"$temp_file_name
