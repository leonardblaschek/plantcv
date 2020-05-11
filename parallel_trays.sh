#!/bin/bash

# Here we are running a VIS top-view pipeline over a flat directory of images

# Image names for this example look like this: cam1-16-08-06_16:45_el1100s1_p19.jpg

/home/leonard/Applications/plantcv/plantcv-pipeline.py \
-d /home/leonard/Dropbox/2020-01_LAC_phenotyping/images/top/renamed/nikon_images/ \
-a filename \
-p /home/leonard/Applications/plantcv/tray_vis.py \
-s %Y%m%d \
-j tray_results.json \
-i /home/leonard/Dropbox/2020-01_LAC_phenotyping/images/top/renamed/nikon_images/output/ \
-f timestamp,id \
-t jpg \
-T 4 \
-w
