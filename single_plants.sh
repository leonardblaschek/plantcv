#!/bin/bash

# Here we are running a VIS top-view pipeline over a flat directory of images

# Image names for this example look like this: cam1-16-08-06_16:45_el1100s1_p19.jpg

/home/leonard/Applications/plantcv/plantcv-pipeline.py \
-d /home/leonard/Documents/Uni/PhD/Phenotyping/2019-03-26_Laccase_mutants/Trays/ \
-a filename \
-p /home/leonard/Applications/plantcv/tray_vis.py \
-s test.sqlite3 \
-i /home/leonard/Documents/Uni/PhD/Phenotyping/2019-03-26_Laccase_mutants/Trays/ \
-f timestamp_id \
-t jpg \
-T 8 \
-w
