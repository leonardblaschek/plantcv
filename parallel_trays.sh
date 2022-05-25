#!/bin/bash

# for an explanation of the arguments, see: 
# https://plantcv.readthedocs.io/en/stable/pipeline_parallel/#legacy-command-line-parameters

/home/leonard/Applications/miniconda3/envs/plantcv/bin/plantcv-workflow.py \
-d /run/media/leonard/data/PhD/Phenotyping/2020-01_LAC_phenotyping/images/top/renamed/ \
-a filename \
-p /home/leonard/Applications/plantcv/tray_vis.py \
-s %j \
-j tray_results.json \
-i /run/media/leonard/data/PhD/Phenotyping/2020-01_LAC_phenotyping/images/top/renamed/output \
-f timestamp,id \
-t jpg \
-T 4 \
-w
