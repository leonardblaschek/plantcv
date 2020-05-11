#!/usr/bin/env python
# coding: utf-8

# In[1]:

#import sys, traceback
import cv2
from PIL import Image
import imutils
import csv
import argparse
#import zbarlight
#import numpy as np
import matplotlib
#import matplotlib.pyplot as plt
#matplotlib.use("TkAgg")
from plantcv import plantcv as pcv

def options():
    parser = argparse.ArgumentParser(description="Imaging processing with PlantCV.")
    parser.add_argument("-i", "--image", help="Input image file.", required=True)
    parser.add_argument("-r","--result", help="Result file.", required= True )
    parser.add_argument("-o", "--outdir", help="Output directory for image files.", required=False)
    parser.add_argument("-w","--writeimg", help="Write out images.", default=False, action="store_true")
    parser.add_argument("-D", "--debug", help="Turn on debug, prints intermediate images.")
    args = parser.parse_args()
    return args

def main():
    
    # Get options
    args = options()
    
    # Set variables
    pcv.params.debug = args.debug        # Replace the hard-coded debug with the debug flag
    img_file = args.image     # Replace the hard-coded input image with image flag
    ref_file = '/home/leonard/Dropbox/2020-01_LAC_phenotyping/images/front/renamed/20200419_Q-5_5.jpg'

    ############### Image read-in ################

    # read image to be analysed
    img, path, filename = pcv.readimage(filename = img_file, mode = "rgb")
    
    # remove oversaturated pixels
    start_mask, img = pcv.threshold.custom_range(img, lower_thresh=[0,0,0], upper_thresh=[254,254,254], channel='RGB')
    start_mask, img = pcv.threshold.custom_range(img, lower_thresh=[0,0,0], upper_thresh=[255,254,255], channel='HSV')

    # read ref image
    ref_img, ref_path, ref_filename = pcv.readimage(filename = ref_file, mode = "rgb")
    
    # remove oversaturated pixels
    start_ref_mask, ref_img = pcv.threshold.custom_range(ref_img, lower_thresh=[0,0,0], upper_thresh=[254,254,254], channel='RGB')
    start_ref_mask, ref_img = pcv.threshold.custom_range(ref_img, lower_thresh=[0,0,0], upper_thresh=[255,254,255], channel='HSV')
    
    
    ############### Colour correction ################

    # find colour card in reference image
    df, start, space = pcv.transform.find_color_card(rgb_img=ref_img)
    ref_mask = pcv.transform.create_color_card_mask(rgb_img=ref_img, radius=10, start_coord=start, spacing=space, ncols=4, nrows=6)

    # find colour card in the image to be analysed
    df, start, space = pcv.transform.find_color_card(rgb_img=img)
    img_mask = pcv.transform.create_color_card_mask(rgb_img=img, radius=10, start_coord=start, spacing=space, ncols=4, nrows=6)

    output_directory = "."

    # correct colour
    ref_matrix, img_matrix, transformation_matrix, corrected_img = pcv.transform.correct_color(ref_img, ref_mask, img, img_mask, output_directory)
    
    # check that the colour correction worked (source~target should be strictly linear)
    pcv.transform.quick_color_check(source_matrix = img_matrix, target_matrix = ref_matrix, num_chips = 24)
    
    ############### Fine segmentation ################
    
    # write the spacing of the colour card to file as size marker   
    with open(r'size_marker.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([filename, space[0]])

    # define a bounding rectangle around the colour card
    x_cc,y_cc,w_cc,h_cc = cv2.boundingRect(img_mask)
    x_cc = int(round(x_cc - 0.3 * w_cc))
    y_cc = int(round(y_cc - 0.3 * h_cc))
    h_cc = int(round(h_cc * 1.6))
    w_cc = int(round(w_cc * 1.6))

    # crop out colour card
    start_point = (x_cc, y_cc)
    end_point = (x_cc+w_cc, y_cc+h_cc)
    colour = (0, 0, 0)
    thickness = -1
    crop_img = cv2.rectangle(corrected_img, start_point, end_point, colour, thickness)
    
    # crop out QR-code
    start_point = (0, 3700)
    end_point = (6000, 4000)
    colour = (0, 0, 0)
    thickness = -1
    crop_img = cv2.rectangle(crop_img, start_point, end_point, colour, thickness)

    # convert RGB to HSV and extract the hue, saturation and value channels
    v = pcv.rgb2gray_hsv(corrected_img, "v")
    a = pcv.rgb2gray_lab(corrected_img, "a")
    
    # mask blue stick in the uncorrected image to avoid potential correction artifacts
    b = pcv.rgb2gray_lab(img, "b")
    no_blue = pcv.threshold.binary(b, 120, 255, "light")
    
    # Rough background subtraction in the uncorrected image to avoid potential correction artifacts
    v_raw = pcv.rgb2gray_hsv(img, "v")
    v_raw_thresh = pcv.threshold.binary(v, 10, 255, "light")
    
    # keep light areas, excluding colour corection artifacts from undersaturated ares
    v_thresh = pcv.threshold.binary(v, 30, 255, "light")
    v_thresh = pcv.logical_and(v_thresh, v_raw_thresh)
    
    # recover dark green areas
    a_thresh = pcv.threshold.binary(a, 120, 255, "dark")
    va_thresh = pcv.logical_or(v_thresh, a_thresh)
    
    # exclude bright blue areas (the stick)
    vba_thresh = pcv.logical_and(v_thresh, no_blue)

    # apply Mask (mask_color=white)
    masked = pcv.apply_mask(corrected_img, vba_thresh, "white")

    # fill small objects
    vba_fill = pcv.fill(vba_thresh, 250)

    # apply mask (mask_color=white)
    masked2 = pcv.apply_mask(masked, vba_fill, "white")

    # identify objects
    contours, hierarchy = pcv.find_objects(masked2, vba_fill)

    # define ROI
    roi_contour, roi_hierarchy= pcv.roi.rectangle(x=2500, y=1500, h=2000, w=1000, img=masked2)

    # decide which objects to keep
    filtered_contours, filtered_hierarchy, mask, area = pcv.roi_objects(img = masked2,
                                                                   roi_type = 'partial',
                                                                   roi_contour = roi_contour,
                                                                   roi_hierarchy = roi_hierarchy,
                                                                   object_contour = contours,
                                                                   obj_hierarchy = hierarchy)

    # combine kept objects
    obj, mask = pcv.object_composition(corrected_img, filtered_contours, filtered_hierarchy)

    ############### Analysis ################

    outfile=False
    if args.writeimg==True:
        outfile_black=args.outdir+"/"+filename+"_black"
        outfile_white=args.outdir+"/"+filename+"_white"
        outfile_analysed=args.outdir+"/"+filename+"_analysed"

    # analyse shape
    shape_img = pcv.analyze_object(corrected_img, obj, mask)
    pcv.print_image(shape_img, outfile_analysed)

    # analyse colour
    colour_img = pcv.analyze_color(corrected_img, mask, 'hsv')

    # keep the segmented plant for visualisation
    picture_mask = pcv.apply_mask(img, mask, "black")
    pcv.print_image(picture_mask, outfile_black)
    
    picture_mask = pcv.apply_mask(img, mask, "white")
    pcv.print_image(picture_mask, outfile_white)

    # print out results
    pcv.print_results(args.result)

if __name__ == '__main__':
    main()