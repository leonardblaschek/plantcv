#!/home/leonard/Applications/anaconda3/bin/python
import sys, traceback
import cv2
import numpy as np
import argparse
import re
import csv
import matplotlib.pyplot as plt
import string
import imutils
from plantcv import plantcv as pcv

def options():
    parser = argparse.ArgumentParser(description="Imaging processing with PlantCV.")
    parser.add_argument("-i", "--image", help="Input image file.", required=True)
    parser.add_argument("-r","--result", help="Result file.", required=True )
    parser.add_argument("-o", "--outdir", help="Output directory for image files.", required=False)
    parser.add_argument("-w","--writeimg", help="Write out images.", default=True, action="store_true")
    parser.add_argument("-D", "--debug", help="Turn on debug, prints intermediate images.")
    args = parser.parse_args()
    return args

def main():
    # Get options
    args = options()
    
    # Set variables
    pcv.params.debug = args.debug        # Replace the hard-coded debug with the debug flag
    pcv.params.debug_outdir = args.outdir  # set output directory
    
    ### Main pipeline
    
    # Read image (readimage mode defaults to native but if image is RGBA then specify mode='rgb')
    img, path, filename = pcv.readimage(args.image, mode='rgb')
    
    ref_img, ref_path, ref_filename = pcv.readimage("/home/leonard/Dropbox/2020-01_LAC_phenotyping/images/top/renamed/20200128_2.jpg", mode = "rgb")
    
    # resize image if made with a different camera
    if img.shape[1] == 5504:
        img = img[0:0+3096, 0:0+4638]
        ref_img = imutils.resize(ref_img, width=4638)
        
        
    df, start, space = pcv.transform.find_color_card(rgb_img=ref_img)
    ref_mask = pcv.transform.create_color_card_mask(rgb_img=ref_img, radius=10, start_coord=start, spacing=space, ncols=4, nrows=6)

    df, start, space = pcv.transform.find_color_card(rgb_img=img)
    img_mask = pcv.transform.create_color_card_mask(rgb_img=img, radius=10, start_coord=start, spacing=space, ncols=4, nrows=6)

    output_directory = "."

    # correct colour
    #target_matrix, source_matrix, transformation_matrix, corrected_img = pcv.transform.correct_color(ref_img, ref_mask, img, img_mask, output_directory)
    
    # check that the colour correction worked (source~target should be strictly linear)
    #pcv.transform.quick_color_check(source_matrix = source_matrix, target_matrix = target_matrix, num_chips = 24)
    
    # write the spacing of the colour card to file as size marker   
    with open(r'size_marker_trays.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([filename, space[0]])
        
    ### Crop tray ###
    
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
    crop_img = cv2.rectangle(img, start_point, end_point, colour, thickness)
    
    #Convert RGB to HSV and extract the value channel
    v = pcv.rgb2gray_hsv(crop_img, "v")
    
    # Threshold the value image
    v_thresh = pcv.threshold.binary(v, 150, 255, "light")
    
    # create bounding rectangle around the tray
    x,y,w,h = cv2.boundingRect(v_thresh)

    #crop image to tray minus the label on the right
    short_w = w - (w * 0.05)
    crop_img = crop_img[y:y+h, x:x+int(short_w)]

    # save cropped image for quality control
    pcv.print_image(crop_img, filename = path + "/" +"cropped" + filename + ".png")

    # Convert RGB to LAB and extract the a channel
    a = pcv.rgb2gray_lab(crop_img, "a")

    # Convert RGB to LAB and extract the b channel
    b = pcv.rgb2gray_lab(crop_img, "b")

    # Threshold the a channel
    a_thresh = pcv.threshold.binary(a, 120, 255, "dark")
    
    # Apply Mask (for VIS images, mask_color=white)
    masked = pcv.apply_mask(crop_img, a_thresh, "white")
    
    # Convert RGB to LAB and extract the Green-Magenta and Blue-Yellow channels from the inital mask
    masked_a = pcv.rgb2gray_lab(masked, "a")
    masked_b = pcv.rgb2gray_lab(masked, "b")

    # Threshold the green-magenta and blue images
    maskeda_thresh = pcv.threshold.binary(masked_a, 112, 255, "dark")
    maskedb_thresh = pcv.threshold.binary(masked_b, 130, 255, "light")

    # Join the thresholded saturation and blue-yellow images
    ab = pcv.logical_and(maskedb_thresh, maskeda_thresh)

    # Fill small objects
    ab_fill = pcv.fill(ab, 250)

    # Apply mask (for VIS images, mask_color=white)
    masked2 = pcv.apply_mask(masked, ab_fill, "white")

    # dilate to avoid losing leaves
    dilated = pcv.dilate(ab_fill, 3, 1)

    # identify objects
    id_objects, obj_hierarchy = pcv.find_objects(crop_img, dilated)
   
    # create bounding box with margins to avoid border artifacts
    roi_y = 0 + crop_img.shape[0] * 0.05
    roi_x = 0 + crop_img.shape[0] * 0.05
    roi_h = crop_img.shape[0] - (crop_img.shape[0] * 0.1)
    roi_w = crop_img.shape[1] - (crop_img.shape[0] * 0.1)
    roi_contour, roi_hierarchy = pcv.roi.rectangle(crop_img, roi_y, roi_x, roi_h, roi_w)
       
    # keep all objects in the bounding box
    roi_objects, roi_obj_hierarchy, kept_mask, obj_area = pcv.roi_objects(img = crop_img, 
                                                                          roi_type = 'partial', 
                                                                          roi_contour = roi_contour,
                                                                          roi_hierarchy = roi_hierarchy, 
                                                                          object_contour = id_objects, 
                                                                          obj_hierarchy = obj_hierarchy)
    
    # cluster the objects by plant (in this case the expected number of rows depends on tray number)
    if re.search("3\.jpg$", filename):
        clusters, contours, hierarchies = pcv.cluster_contours(crop_img, roi_objects, roi_obj_hierarchy, 1, 5)
    else: 
        clusters, contours, hierarchies = pcv.cluster_contours(crop_img, roi_objects, roi_obj_hierarchy, 3, 5)
    
    # split image into single plants  
    out = args.outdir    
    output_path, imgs, masks = pcv.cluster_contour_splitimg(crop_img, clusters, contours, hierarchies, out, file=filename)
    
    # analyse single plants
    for i in range(0, len(imgs)):              
        contours, hierarchy = pcv.find_objects(imgs[i], masks[i])
        obj, mask = pcv.object_composition(imgs[i], contours, hierarchy)
        
        # Analyze the shape of each plant 
        analysis_images = pcv.analyze_object(img=imgs[i], obj=obj, mask=masks[i])

        # Determine color properties
        color_images = pcv.analyze_color(imgs[i], masks[i], "hsv")

        # Watershed plant area to count leaves
        watershed_images = pcv.watershed_segmentation(imgs[i], masks[i], 15)

        # Print out a text file with shape data for each plant in the image 
        pcv.print_results(filename = path + "/" + filename + "_" + str(i) + '.json')
        
        # Clear the measurements stored globally into the Ouptuts class
        pcv.outputs.clear()

    
if __name__ == '__main__':
    main()
        
