#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/miniconda3/envs/plantcv/bin/plantcv-workflow.py \
-d /run/media/leonard/data1/PhD/Phenotyping/2021-07_Emma/Side2/ \
-a filename \
-p /home/leonard/Applications/plantCV/plantcv_vis.py \
-s %j \
-j /run/media/leonard/data1/PhD/Phenotyping/2021-07_Emma/Side2/output/results.json \
-i /run/media/leonard/data1/PhD/Phenotyping/2021-07_Emma/Side2/output/ \
-f timestamp,id \
-t JPG \
-T 4 \
-w
