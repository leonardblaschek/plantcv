#!/home/leonard/Applications/anaconda3/bin/python
import sys, traceback
import os
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
    parser = argparse.ArgumentParser(
        description="Imaging processing with PlantCV.")
    parser.add_argument("-i",
                        "--image",
                        help="Input image file.",
                        required=True)
    parser.add_argument("-r", "--result", help="Result file.", required=True)
    parser.add_argument("-o",
                        "--outdir",
                        help="Output directory for image files.",
                        required=False)
    parser.add_argument("-w",
                        "--writeimg",
                        help="Write out images.",
                        default=True,
                        action="store_true")
    parser.add_argument("-D",
                        "--debug",
                        help="Turn on debug, prints intermediate images.")
    args = parser.parse_args()
    return args


def main():
    # Get options
    args = options()

    # Set variables
    pcv.params.debug = args.debug  # Replace the hard-coded debug with the debug flag
    pcv.params.debug_outdir = args.outdir  # set output directory

    ### Main pipeline ###

    # Read image (readimage mode defaults to native but if image is RGBA then specify mode='rgb')
    img, path, filename = pcv.readimage(args.image, mode='rgb')

    #ref_img, ref_path, ref_filename = pcv.readimage(
    #    "/home/leonard/Dropbox/2020-01_LAC_phenotyping/images/top/renamed/20200128_2.jpg",
    #    mode="rgb")

    # Find colour cards
    #df, start, space = pcv.transform.find_color_card(rgb_img=ref_img)
    #ref_mask = pcv.transform.create_color_card_mask(rgb_img=ref_img, radius=10, start_coord=start, spacing=space, ncols=4, nrows=6)

    df, start, space = pcv.transform.find_color_card(rgb_img=img)
    img_mask = pcv.transform.create_color_card_mask(rgb_img=img,
                                                    radius=10,
                                                    start_coord=start,
                                                    spacing=space,
                                                    ncols=4,
                                                    nrows=6)

    output_directory = "."

    # Correct colour
    #target_matrix, source_matrix, transformation_matrix, corrected_img = pcv.transform.correct_color(ref_img, ref_mask, img, img_mask, output_directory)

    # Check that the colour correction worked (source~target should be strictly linear)
    #pcv.transform.quick_color_check(source_matrix = source_matrix, target_matrix = target_matrix, num_chips = 24)

    # Write the spacing of the colour card to file as size marker
    with open(os.path.join(path, 'size_marker_trays.csv'), 'a') as f:
        writer = csv.writer(f)
        writer.writerow([filename, space[0]])

    ### Crop tray ###

    # Define a bounding rectangle around the colour card
    x_cc, y_cc, w_cc, h_cc = cv2.boundingRect(img_mask)
    x_cc = int(round(x_cc - 0.3 * w_cc))
    y_cc = int(round(y_cc - 0.3 * h_cc))
    h_cc = int(round(h_cc * 1.6))
    w_cc = int(round(w_cc * 1.6))

    # Crop out colour card
    start_point = (x_cc, y_cc)
    end_point = (x_cc + w_cc, y_cc + h_cc)
    colour = (0, 0, 0)
    thickness = -1
    crop_img = cv2.rectangle(img, start_point, end_point, colour, thickness)

    # Convert RGB to HSV and extract the value channel
    v = pcv.rgb2gray_hsv(crop_img, "v")

    # Threshold the value image
    v_thresh = pcv.threshold.binary(v, 150, 255, "light")

    # Fill out bright imperfections
    v_thresh = pcv.fill(v_thresh, 500)

    # Create bounding rectangle around the tray
    x, y, w, h = cv2.boundingRect(v_thresh)

    # Crop image to tray
    crop_img = card_crop_img[y:y+h, x:x+int(w - (w * 0.03))] # crop extra 3% from right because of tray labels

    # Save cropped image for quality control
    pcv.print_image(crop_img,
                    filename=path + "/" + "cropped" + filename + ".png")

    ### Threshold plants ###

    # Threshold the green-magenta, blue, and hue channels
    a_thresh, _ = pcv.threshold.custom_range(img=crop_img,
                                             lower_thresh=[0, 0, 0],
                                             upper_thresh=[255, 113, 255],
                                             channel='LAB')
    b_thresh, _ = pcv.threshold.custom_range(img=crop_img,
                                             lower_thresh=[0, 0, 135],
                                             upper_thresh=[255, 255, 255],
                                             channel='LAB')
    h_thresh, _ = pcv.threshold.custom_range(img=crop_img,
                                             lower_thresh=[35, 0, 0],
                                             upper_thresh=[70, 255, 255],
                                             channel='HSV')

    # Join the thresholds (AND)
    ab = pcv.logical_and(b_thresh, a_thresh)
    abh = pcv.logical_and(ab, h_thresh)

    # Fill small objects depending on expected plant size based on DPG
    match = re.search("(\d+).(\d)\.JPG$", filename)

    if int(match.group(1)) < 10:
        abh_clean = pcv.fill(abh, 50)
        print("50")
    elif int(match.group(1)) < 15:
        abh_clean = pcv.fill(abh, 200)
        print("200")
    else:
        abh_clean = pcv.fill(abh, 500)
        print("500")

    # Dilate to close broken borders
    abh_dilated = pcv.dilate(abh_clean, 3, 1)

    # Close holes
    # abh_fill = pcv.fill_holes(abh_dilated) # silly -- removed
    abh_fill = abh_dilated

    # Apply mask (for VIS images, mask_color=white)
    masked = pcv.apply_mask(crop_img, abh_fill, "white")

    # Save masked image for quality control
    pcv.print_image(masked, filename=path + "/" + "masked" + filename + ".png")

    ### Filter and group contours ###

    # Identify objects
    id_objects, obj_hierarchy = pcv.find_objects(crop_img, abh_fill)

    # Create bounding box with margins to avoid border artifacts
    roi_y = 0 + crop_img.shape[0] * 0.05
    roi_x = 0 + crop_img.shape[0] * 0.05
    roi_h = crop_img.shape[0] - (crop_img.shape[0] * 0.1)
    roi_w = crop_img.shape[1] - (crop_img.shape[0] * 0.1)
    roi_contour, roi_hierarchy = pcv.roi.rectangle(crop_img, roi_y, roi_x,
                                                   roi_h, roi_w)

    # Keep all objects in the bounding box
    roi_objects, roi_obj_hierarchy, kept_mask, obj_area = pcv.roi_objects(
        img = crop_img,
        roi_type = 'partial',
        roi_contour = roi_contour,
        roi_hierarchy = roi_hierarchy,
        object_contour = id_objects,
        obj_hierarchy = obj_hierarchy)

    # Cluster the objects by plant
    clusters, contours, hierarchies = pcv.cluster_contours(
        crop_img, roi_objects, roi_obj_hierarchy, 3, 5)

    # Split image into single plants
    out = args.outdir
    output_path, imgs, masks = pcv.cluster_contour_splitimg(crop_img,
                                                            clusters,
                                                            contours,
                                                            hierarchies,
                                                            out,
                                                            file = filename)

    ### Analysis ###

    # Approximate the position of the top left plant as grid start
    coord_y = int(round(((crop_img.shape[0] / 3) * 0.5) + (crop_img.shape[0] * 0.025)))
    coord_x = int(round(((crop_img.shape[1] / 5) * 0.5) + (crop_img.shape[1] * 0.025)))

    # Set the ROI spacing relative to image dimensions
    spc_y = int((round(crop_img.shape[0] - (crop_img.shape[0] * 0.05)) / 3))
    spc_x = int((round(crop_img.shape[1] - (crop_img.shape[1] * 0.05)) / 5))

    # Set the ROI radius relative to image width
    r = int(round(crop_img.shape[1] / 12.5))

    # Make a grid of ROIs at the expected positions of plants
    # This allows for gaps due to dead/not germinated plants, without messing up the plant numbering
    imgs, masks = pcv.roi.multi(img=crop_img,
                                nrows=3,
                                ncols=5,
                                coord=(coord_x, coord_y),
                                radius=r,
                                spacing=(spc_x, spc_y))

    # Loop through the ROIs in the grid
    for i in range(0, len(imgs)):
        # Find objects within the ROI
        filtered_contours, filtered_hierarchy, filtered_mask, filtered_area = pcv.roi_objects(
            img = crop_img,
            roi_type = "partial",
            roi_contour = imgs[i],
            roi_hierarchy = masks[i],
            object_contour = id_objects,
            obj_hierarchy = obj_hierarchy)
        # Continue only if not empty
        if len(filtered_contours) > 0:
            # Combine objects within each ROI
            plant_contour, plant_mask = pcv.object_composition(
                img = crop_img,
                contours = filtered_contours,
                hierarchy = filtered_hierarchy)

            # Analyse the shape of each plant
            analysis_images = pcv.analyze_object(img = crop_img,
                                                 obj = plant_contour,
                                                 mask = plant_mask)

            # Determine color properties
            color_images = pcv.analyze_color(crop_img, plant_mask, "hsv")

            # Watershed plant area to count leaves
            watershed_images = pcv.watershed_segmentation(crop_img, plant_mask, 15)

            # Print out a .json file with the analysis data for the plant
            pcv.outputs.save_results(filename = path + "/" + filename + "_" + str(i) + '.json')

            # Clear the measurements stored globally into the Ouptuts class
            pcv.outputs.clear()


if __name__ == '__main__':
    main()
