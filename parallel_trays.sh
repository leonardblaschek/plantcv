#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/miniconda3/envs/plantcv/bin/plantcv-workflow.py \
-d /run/media/leonard/data/PhD/Phenotyping/2021-07_Emma/Top/ \
-a filename \
-p /home/leonard/Applications/plantcv/tray_vis.py \
-s %j \
-j tray_results.json \
-i /run/media/leonard/data/PhD/Phenotyping/2021-07_Emma/Top/ \
-f timestamp,id \
-t JPG \
-T 4 \
-w
