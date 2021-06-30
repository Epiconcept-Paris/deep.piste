from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
import pydicom
import numpy as np
from PIL import Image

def dicom2png(infile, outfile):
  pixels = dicom2narray(infile)
  img = Image.fromarray(pixels)
  img.save(outfile + ".png")
  print(f"file {outfile} written")



"""
Converts a DICOM into a NUMPY array and returns this array.
"""
def dicom2narray(path, voi_lut = True, fix_monochrome = True):
    dicom = pydicom.read_file(path)

    # VOI LUT (if available by DICOM device) is used to transform raw DICOM data to "human-friendly" view
    if voi_lut:
        #If the modality is CT (Scanner Image) we have to convert the values of the image first with apply_modality
        #It uses the values of RescaleSlope and RescaleIntercept to convert the values or the attribute LUT Sequence
        if dicom.Modality == "CT":
            data = apply_modality_lut(dicom.pixel_array, dicom)
            data = apply_voi_lut(data, dicom)
        else:
            data = apply_voi_lut(dicom.pixel_array, dicom)
    else:
        data = dicom.pixel_array

    # depending on this value, X-ray may look inverted - fix that:
    if fix_monochrome and dicom.PhotometricInterpretation == "MONOCHROME1":
        data = np.amax(data) - data

    #If the DICOM are not in one of these two formats, it can bring new problems.
    if dicom.PhotometricInterpretation != "MONOCHROME2" and dicom.PhotometricInterpretation != "MONOCHROME1":
        raise ValueError("Photométrie imprévue : " + dicom.PhotometricInterpretation)
    
    data = data - np.min(data)
    data = data / np.max(data)
    data = (data * 255).astype(np.uint8)
        
    return data


dicom2png('/home/williammadie/images/test20/dicom/image_1.dcm','/home/williammadie/images/test20/png/image_1.png')