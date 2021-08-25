#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/miniconda3/envs/plantcv/bin/plantcv-workflow.py \
-d /run/media/leonard/data/PhD/Phenotyping/2021-04_lac_mutants/front/renamed/ \
-a filename \
-p /home/leonard/Applications/plantcv/plantcv_vis.py \
-s %j \
-j /run/media/leonard/data/PhD/Phenotyping/2021-04_lac_mutants/front/renamed/output/results.json \
-i /run/media/leonard/data/PhD/Phenotyping/2021-04_lac_mutants/front/renamed/output/ \
-f timestamp,id \
-t JPG \
-T 4 \
-w
