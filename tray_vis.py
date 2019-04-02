#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!/home/leonard/Applications/anaconda3/bin/python
import sys, traceback
import cv2
import numpy as np
import argparse
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
	
	
	# In[3]:
	
	
	#Crop tray
	#Convert RGB to HSV and extract the value channel
	h = pcv.rgb2gray_hsv(img, "v")
	# Threshold the value image
	v_thresh = pcv.threshold.binary(h, 185, 255, "light")
	v_mblur = pcv.median_blur(v_thresh, 5)
	#roi_contour, roi_hierarchy = pcv.roi.from_binary_image(img=img, bin_img=v_thresh)
	#crop_img = pcv.auto_crop(img, id_objects[0], 20, 20, 'black')
	
	x,y,w,h = cv2.boundingRect(v_mblur)
	#box = cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
	#cv2.drawContours(img,[box],0,(0,0,255),2)
	roi_contour, roi_hierarchy = pcv.roi.rectangle(img=img, x=x, y=y, h=h, w=w)
	#print(roi_contour)
	#crop_img = img[tuple(roi_contour)]
	crop_img = img[y:y+h, x:x+w]
	
	crop_img = imutils.resize(crop_img, width=4500)
	
	
	#rect = cv2.minAreaRect(v_mblur)
	#box = cv2.boxPoints(rect)
	#box = np.int0(box)
	
	
	
	
	
	# In[4]:
	
	
	# Convert RGB to HSV and extract the hue channel
	h = pcv.rgb2gray_hsv(crop_img, "h")
	
	
	# In[5]:
	
	
	# Threshold the hue image
	h_thresh1_1 = pcv.threshold.binary(h, 10, 255, "light")
	h_thresh1_2 = pcv.threshold.binary(h, 80, 255, "dark")
	h_thresh1 = pcv.logical_and(h_thresh1_1, h_thresh1_2)
	h_thresh2_1 = pcv.threshold.binary(h, 125, 255, "light")
	h_thresh2_2 = pcv.threshold.binary(h, 170, 255, "dark")
	h_thresh2 = pcv.logical_and(h_thresh2_1, h_thresh2_2)
	
	h_thresh = pcv.logical_or(h_thresh1, h_thresh2)
	
	
	# In[6]:
	
	
	# Median Blur
	h_mblur = pcv.median_blur(h_thresh, 5)
	#h_cnt = pcv.median_blur(h_thresh, 5)
	
	
	# In[11]:
	
	
	# Convert RGB to LAB and extract the a channel
	a = pcv.rgb2gray_lab(crop_img, "a")
	#pcv.print_image(a, "a_channel.png")
	
	
	# In[10]:
	
	
	# Convert RGB to LAB and extract the b channel
	b = pcv.rgb2gray_lab(crop_img, "b")
	#pcv.print_image(b, "b_channel.png")
	
	
	# In[28]:
	
	
	# Threshold the blue image
	a_thresh = pcv.threshold.binary(a, 120, 255, "dark")
	a_cnt = pcv.threshold.binary(a, 120, 255, "dark")
	#pcv.print_image(a_cnt, "a_cnt.png")
	
	
	# In[29]:
	
	
	# Join the thresholded saturation and blue-yellow images
	# commented out, hue method too insensitive here
	#bh = pcv.logical_or(h_mblur, b_cnt)
	ah = a_cnt
	
	
	# In[30]:
	
	
	# Apply Mask (for VIS images, mask_color=white)
	masked = pcv.apply_mask(crop_img, ah, "white")
	
	
	# In[31]:
	
	
	
	# Convert RGB to LAB and extract the Green-Magenta and Blue-Yellow channels
	masked_a = pcv.rgb2gray_lab(masked, "a")
	masked_b = pcv.rgb2gray_lab(masked, "b")
	
	# Threshold the green-magenta and blue images
	maskeda_thresh = pcv.threshold.binary(masked_a, 115, 255, "dark")
	maskeda_thresh1 = pcv.threshold.binary(masked_a, 135, 255, "light")
	maskedb_thresh = pcv.threshold.binary(masked_b, 128, 255, "light")
	
	# Join the thresholded saturation and blue-yellow images (OR)
	ab1 = pcv.logical_or(maskeda_thresh, maskedb_thresh)
	ab = pcv.logical_or(maskeda_thresh1, ab1)
	
	# Fill small objects
	ab_fill = pcv.fill(ab, 100)
	
	# Apply mask (for VIS images, mask_color=white)
	masked2 = pcv.apply_mask(masked, ab_fill, "white")
	
	
	# In[32]:
	
	
	# STEP 8: Dilate so that you don't lose leaves (just in case)
	# Inputs:
	#    img    = input image
	#    kernel = integer
	#    i      = iterations, i.e. number of consecutive filtering passes
	
	dilated = pcv.dilate(ab_fill, 1, 1)
	#pcv.print_image(dilated, "dilated.png")
	
	
	# In[33]:
	
	
	# STEP 9: Find objects (contours: black-white boundaries)
	# Inputs:
	#    img  = image that the objects will be overlayed
	#    mask = what is used for object detection
	
	id_objects, obj_hierarchy = pcv.find_objects(crop_img, dilated)
	
	
	# In[34]:
	
	
	# STEP 10: Define region of interest (ROI)
	# Inputs:
	#    x     = The x-coordinate of the upper left corner of the rectangle.
	#    y     = The y-coordinate of the upper left corner of the rectangle.
	#    w     = The height of the rectangle.
	#    h     = The width of the rectangle.
	#    img   = An RGB or grayscale image to plot the ROI on.
	#    roi_contour, roi_hierarchy = pcv.roi.rectangle(5, 90, 200, 390, img1)                                                ^                ^
	#                                                  |______________|
	#                                            adjust these four values
	
	roi_contour, roi_hierarchy = pcv.roi.rectangle(crop_img, 0, 0, 2500, 4500)
	
	
	# In[35]:
	
	
	# STEP 11 (optional): Get the size of the marker. First make a region of interest around one of 
	# the toughspots. Then use `report_size_marker_area`. 
	
	marker_contour, marker_hierarchy = pcv.roi.rectangle(crop_img, 0,0,200,300)
	
	# Inputs:
	#   img - RGB or grayscale image to plot the marker object on 
	#   roi_contour = A region of interest contour 
	#   roi_hierarchy = A region of interest contour heirarchy 
	#   marker = 'define' (default) or 'detect', if 'define' then you set an area, if 'detect'
	#            it means you want to detect within an area 
	#   objcolor = Object color is 'dark' (default) or 'light', is the marker darker or lighter than 
	#               the background?
	#   thresh_channel = 'h', 's', 'v' for hue, saturation, or value. Default set to None. 
	#   thresh = Binary threshold value (integer), default set to None 
	#   
	marker_header, marker_data, analysis_images = pcv.report_size_marker_area(
		crop_img, marker_contour, marker_hierarchy, marker='detect', objcolor='light', 
		thresh_channel='v', thresh=230)
	#print(marker_data)
	
	
	# In[36]:
	
	
	# STEP 12: Keep objects that overlap with the ROI
	# Inputs:
	#    img            = img to display kept objects
	#    roi_type       = 'cutto' or 'partial' (for partially inside)
	#    roi_contour    = contour of roi, output from "View and Ajust ROI" function
	#    roi_hierarchy  = contour of roi, output from "View and Ajust ROI" function
	#    object_contour = contours of objects, output from "Identifying Objects" fuction
	#    obj_hierarchy  = hierarchy of objects, output from "Identifying Objects" fuction
	
	roi_objects, roi_obj_hierarchy, kept_mask, obj_area = pcv.roi_objects(crop_img, 'partial', roi_contour, roi_hierarchy,
					           id_objects, obj_hierarchy)
	
	
	# In[37]:
	
	
	# STEP 13: This function take a image with multiple contours and
	# clusters them based on user input of rows and columns
	
	# Inputs:
	#    img               = An RGB image
	#    roi_objects       = object contours in an image that are needed to be clustered.
	#    roi_obj_hierarchy = object hierarchy
	#    nrow              = number of rows to cluster (this should be the approximate  number of desired rows in the entire image even if there isn't a literal row of plants)
	#    ncol              = number of columns to cluster (this should be the approximate number of desired columns in the entire image even if there isn't a literal row of plants)
	
	clusters_i, contours, hierarchies = pcv.cluster_contours(crop_img, roi_objects, roi_obj_hierarchy, 3, 5)
	
	
	# In[38]:
	
	
	# STEP 14: This #function takes clustered contours and splits them into multiple images,
	# also does a check to make sure that the number of inputted filenames matches the number
	# of clustered contours. If no filenames are given then the objects are just numbered
	# Inputs:
	#    img                     = ideally a masked RGB image.
	#    grouped_contour_indexes = output of cluster_contours, indexes of clusters of contours
	#    contours                = contours to cluster, output of cluster_contours
	#    hierarchy               = object hierarchy
	#    outdir                  = directory for output images
	#    file                    = the name of the input image to use as a base name , output of filename from read_image function
	#    filenames               = input txt file with list of filenames in order from top to bottom left to right (likely list of genotypes)
	
	# Set global debug behavior to None (default), "print" (to file), or "plot" (Jupyter Notebooks or X11)
	# Un-comment the line below to see the split up contours print to the output directory 
	#pcv.params.debug = "print"
	
	out = args.outdir
	
	# If you have a list of treatments, genotypes, etc. You would input a .txt file with them to help save
	# the contours by names, add it to the options class and then add filenames=names to the 
	# splitimg function below.  
	#names = args.names
	
	output_path = pcv.cluster_contour_splitimg(crop_img, clusters_i, contours, 
			        hierarchies, path+"/single_plants", file=filename)
	
	# Make a grid of ROIs 
	rois1, roi_hierarchy1 = pcv.roi.multi(img=crop_img, coord=(500,450), radius=375, spacing=(825, 825), nrows=3, ncols=5)
	
	img_copy = np.copy(crop_img)

	for i in range(0, len(rois1)):
		roi = rois1[i]
		hierarchy = roi_hierarchy1[i]
		# Find objects
		filtered_contours, filtered_hierarchy, filtered_mask, filtered_area = pcv.roi_objects(
			img=crop_img, roi_type="partial", roi_contour=roi, roi_hierarchy=hierarchy, object_contour=id_objects, 
			obj_hierarchy=obj_hierarchy)

		# Combine objects together in each plant     
		plant_contour, plant_mask = pcv.object_composition(img=crop_img, contours=filtered_contours, hierarchy=filtered_hierarchy)        

		# Analyze the shape of each plant 
		shape_data_headers, shape_data, analysis_images = pcv.analyze_object(img=img_copy, obj=plant_contour, mask=plant_mask)
    
		# Save the image with shape characteristics 
		img_copy = analysis_images[0]
    
		# Determine color properties: Histograms, Color Slices, output color analyzed histogram (optional)
		#color_header, color_data, color_histogram = pcv.analyze_color(crop_img, plant_mask, 256, 'all')

		# Print out a text file with shape data for each plant in the image 
		pcv.print_results(filename = 'prefix_' + str(i) + '.txt')
		# Clear the measurements stored globally into the Ouptuts class
		pcv.outputs.clear()

	
if __name__ == '__main__':
	main()
		