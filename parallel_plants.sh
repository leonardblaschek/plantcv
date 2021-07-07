#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/miniconda3/envs/plantcv/bin/plantcv-workflow.py \
-d /home/leonard/Documents/Uni/PhD/Phenotyping/2020-09_lac_mutants/front/renamed/ \
-a filename \
-p /home/leonard/Applications/plantCV/plantcv_vis.py \
-s %Y%m%d \
-j results.json \
-i /home/leonard/Dropbox/2021-05_plantcv_processing/2020-09_front/ \
-f timestamp,id \
-t jpg \
-T 6 \
-w
