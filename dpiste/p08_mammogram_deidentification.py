import os
import glob
import string
import time
import shutil
import json
import pydicom
from datetime import datetime
import numpy as np
from pydicom.sequence import Sequence
from pydicom.dataset import Dataset
from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader
from dpiste import dicom2png, utils, report
from kskit.deid_mammogram import *


def deid_mammogram():
    """
    Anonymize a complete directory of DICOM.

    @param

    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """
    start_time = time.time()
    nb_images_processed = 1
    summary = """\n\n\n
Here is a summary of the DICOMs that have been de-identified.\n\n\n
    """

    PATH_ATTRIBUTES_TO_KEEP = '/home/williammadie/GitHub/deep.piste/dpiste/data/attributes_to_keep.json'

    indir = utils.get_home('data', 'input', 'hdh','')
    outdir = utils.get_home('data','output','hdh','')
    outdir_intermediate = utils.get_home('data','transform','hdh','')
    output_summary = outdir_intermediate + "/summary.log"

    pathname = indir + "/**/*.dcm"
    list_dicom = glob.glob(pathname, recursive=True)

    list_dicom = sorted(list_dicom)
    
    for file in list_dicom:
    
        nb_files = len(list_dicom)
        input_path = file
        
        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir_intermediate + os.path.basename(file) + ".txt"
            output_summary = outdir_intermediate + "summary.log"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir_intermediate + "/" + os.path.basename(file) + ".txt"
            output_summary = outdir_intermediate + "/summary.log"
        
        output_path = input_path.replace(indir, outdir)
        output_ds = input_path.replace(indir, outdir_intermediate)
        output_summary = input_path.replace(indir, outdir_intermediate)
        try:
            os.makedirs(output_path.replace(os.path.basename(file), ""))
        except FileExistsError as error:
            print('\n')
        try:
            os.makedirs(output_ds.replace(os.path.basename(file), ""))
        except FileExistsError as error:
            print('\n')
        try:
            os.makedirs(output_summary.replace(os.path.basename(file),""))
        except FileExistsError as error:
            print('\n')

        (pixels, ds) = dicom2png.dicom2narray(input_path)

        ocr_data = get_text_areas(pixels)

        if len(ocr_data):
            print("\n___________A text area has been detected : " + input_path + "___________\n")
            pixels = hide_text(pixels, ocr_data)
            
            
        else:
            print("\nNo text area detected\n")
            print(input_path, output_path)
        
        ds = de_identify_ds(ds, PATH_ATTRIBUTES_TO_KEEP)
        dicom2png.narray2dicom(pixels, ds, output_path)
        print(nb_images_processed, "/", nb_files, "DICOM(s) de-identified")

        with open(output_ds,'a') as f:
            file_path = indir + file
            text = input_path + '\n' + str(ds) + '\n' + "Words recognized : " + \
               str(ocr_data) + '\n'
            f.write(text)

        summary = p08_005_update_summary(summary, file_path, ocr_data)
        nb_images_processed += 1

    
    time_taken = time.time() - start_time
    with open(output_summary, 'w') as f:
        f.write(
          str(round(time_taken/60)) + " minutes taken to de-identify all images.\n" + \
            summary
        )