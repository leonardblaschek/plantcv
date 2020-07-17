#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/plantcv/plantcv-pipeline.py \
-d /home/leonard/Documents/Uni/PhD/Phenotyping/2020-05_lac11_segregating/ \ 
-a filename \
-p /home/leonard/Applications/plantcv/tray_vis.py \
-s %d \
-j tray_results.json \
-i /home/leonard/Documents/Uni/PhD/Phenotyping/2020-05_lac11_segregating/output/ \
-f timestamp,id \
-t jpg \
-T 4 \
-w
