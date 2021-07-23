import cv2
from PIL import Image
import imutils
import csv
import argparse
import matplotlib
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

    ############### Image read-in ################

    # Read target image
    img, path, filename = pcv.readimage(filename = img_file, mode = "rgb")
    
    ############### Find scale and crop ################
    
    # find colour card in the image to be analysed
    df, start, space = pcv.transform.find_color_card(rgb_img = img)
    #if int(start[0]) < 2000:
    #        img = imutils.rotate_bound(img, -90)
    #        rotated = 1
    #        df, start, space = pcv.transform.find_color_card(rgb_img = img)
    #else: rotated = 0
    if img.shape[0] > 6000:
        rotated = 1
    else: rotated = 0
    img_mask = pcv.transform.create_color_card_mask(rgb_img = img, radius = 10, start_coord = start, spacing = space, ncols = 4, nrows = 6)
    
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
    crop_img = cv2.rectangle(img, start_point, end_point, colour, thickness)
    
    ############### Fine segmentation ################
    
    # Threshold A and B channels of the LAB colourspace and the Hue channel of the HSV colourspace
    l_thresh, _ = pcv.threshold.custom_range(img=crop_img, lower_thresh=[70,0,0], upper_thresh=[255,255,255], channel='LAB')
    a_thresh, _ = pcv.threshold.custom_range(img=crop_img, lower_thresh=[0,0,0], upper_thresh=[255,145,255], channel='LAB')
    b_thresh, _ = pcv.threshold.custom_range(img=crop_img, lower_thresh=[0,0,123], upper_thresh=[255,255,255], channel='LAB')
    h_thresh_low, _ = pcv.threshold.custom_range(img=crop_img, lower_thresh=[0,0,0], upper_thresh=[130,255,255], channel='HSV')
    h_thresh_high, _ = pcv.threshold.custom_range(img=crop_img, lower_thresh=[150,0,0], upper_thresh=[255,255,255], channel='HSV')
    h_thresh = pcv.logical_or(h_thresh_low, h_thresh_high)

    # Join the thresholded images to keep only consensus pixels
    ab = pcv.logical_and(b_thresh, a_thresh)
    lab = pcv.logical_and(l_thresh, ab)
    labh = pcv.logical_and(lab, h_thresh)

    # Fill small objects
    labh_clean = pcv.fill(labh, 200)

    # Dilate to close broken borders
    #labh_dilated = pcv.dilate(labh_clean, 4, 1)
    labh_dilated = labh_clean

    # Apply mask (for VIS images, mask_color=white)
    masked = pcv.apply_mask(crop_img, labh_dilated, "white")

    # Identify objects
    contours, hierarchy = pcv.find_objects(crop_img, labh_dilated)

    # Define ROI

    if rotated == 1:
        roi_height = 3000
        roi_lwr_bound = y_cc + (h_cc * 0.5) - roi_height
        roi_contour, roi_hierarchy= pcv.roi.rectangle(x=1000, y=roi_lwr_bound, h=roi_height, w=2000, img=crop_img)
    else:
        roi_height = 1500
        roi_lwr_bound = y_cc + (h_cc * 0.5) - roi_height
        roi_contour, roi_hierarchy= pcv.roi.rectangle(x=2000, y=roi_lwr_bound, h=roi_height, w=2000, img=crop_img)

    # Decide which objects to keep
    filtered_contours, filtered_hierarchy, mask, area = pcv.roi_objects(img = crop_img,
                                                                roi_type = 'partial',
                                                                roi_contour = roi_contour,
                                                                roi_hierarchy = roi_hierarchy,
                                                                object_contour = contours,
                                                                obj_hierarchy = hierarchy)
    # Combine kept objects
    obj, mask = pcv.object_composition(crop_img, filtered_contours, filtered_hierarchy)

    ############### Analysis ################

    outfile=False
    if args.writeimg==True:
        outfile_black=args.outdir+"/"+filename+"_black"
        outfile_white=args.outdir+"/"+filename+"_white"
        outfile_analysed=args.outdir+"/"+filename+"_analysed"

    # analyse shape
    shape_img = pcv.analyze_object(crop_img, obj, mask)
    pcv.print_image(shape_img, outfile_analysed)

    # analyse colour
    colour_img = pcv.analyze_color(crop_img, mask, 'hsv')

    # keep the segmented plant for visualisation
    picture_mask = pcv.apply_mask(crop_img, mask, "black")
    pcv.print_image(picture_mask, outfile_black)
    
    picture_mask = pcv.apply_mask(crop_img, mask, "white")
    pcv.print_image(picture_mask, outfile_white)

    # print out results
    pcv.outputs.save_results(filename=args.result, outformat="json")

if __name__ == '__main__':
    main()
