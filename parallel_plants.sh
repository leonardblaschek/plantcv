#!/bin/bash

# for an explanation of the arguments, see https://plantcv.readthedocs.io/en/stable/pipeline_parallel/

/home/leonard/Applications/plantcv/plantcv-pipeline.py \
-d /home/leonard/Dropbox/2020-01_LAC_phenotyping/images/front/renamed/harvesting/ \
-a filename \
-p /home/leonard/Applications/plantcv/plantcv_vis.py \
-s %Y%m%d \
-j results.json \
-i /home/leonard/Dropbox/2020-01_LAC_phenotyping/images/front/output/ \
-f timestamp,id,frame \
-t jpg \
-T 4 \
-w
