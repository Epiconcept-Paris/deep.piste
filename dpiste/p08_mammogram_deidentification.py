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
from dpiste import utils, report
from kskit import dicom2png
from kskit.deid_mammogram import *


def deid_mammogram(indir = None, outdir = None):
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

    pkg_dir, this_filename = os.path.split(__file__)
    PATH_ATTRIBUTES_TO_KEEP = os.path.join(pkg_dir, "data/resources/deid_ref/attributes_to_keep.json")
    
    if indir == None:
        indir = utils.get_home('data', 'input', 'dcm4chee','dicom','')
    if outdir == None:
        outdir = utils.get_home('data','output','hdh', 'dicom-png', '')
    
    output_summary = outdir + "/summary.log"

    pathname = indir + "/**/*"
    list_dicom = glob.glob(pathname, recursive=True)

    list_dicom = sorted(list_dicom)
    print(f"hola!! {indir}")
    print(list_dicom)
    for file in list_dicom:
      if os.path.isfile(file):
        nb_files = len(list_dicom)
        input_path = file
        
        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir + os.path.basename(file) + ".txt"
            output_summary = outdir + "summary.log"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir + "/" + os.path.basename(file) + ".txt"
            output_summary = outdir + "/summary.log"

        (pixels, ds) = dicom2png.dicom2narray(input_path)

        ocr_data = get_text_areas(pixels)

        if len(ocr_data):
            print("\n___________A text area has been detected : " + input_path + "___________\n")
            pixels = hide_text(pixels, ocr_data)
            
        else:
            print("\nNo text area detected\n")
            print(input_path, "=>", output_path)
        
        ds = de_identify_ds(ds, PATH_ATTRIBUTES_TO_KEEP)
        
        dicom2png.narray2png(pixels, output_path)
        print(nb_images_processed, "/", nb_files, "DICOM(s) de-identified")

        with open(output_ds,'a') as f:
            file_path = indir + file
            text = input_path + '\n' + "Words recognized : " + \
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
