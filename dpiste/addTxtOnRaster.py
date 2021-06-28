import random
import numpy as np
from pydicom import *
from PIL import Image, ImageFont, ImageDraw
import matplotlib.pyplot as plt
from matplotlib import cm
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut

pathDCM = '/home/williammadie/images/test10/dicom'
pathPNG = '/home/williammadie/images/test10/png'
pathFonts = '/home/williammadie/images/fonts'


"""

This module aimed at generating partially random texts and adding these texts to
test images before treating them with the OCR module.

"""



def main():
    #ds = dcmread(pathDCM + "/test3.dcm")
    #pixels = ds.pixel_array
    pixels = read_xray(pathDCM + "/test3.dcm")
    print(pixels)

    img = Image.fromarray(pixels)
    img.save(pathPNG + "/preprocess.png")
    
    plt.imsave(pathPNG + "/img1.png", pixels)

    rasterWthTxt = addTxt2Raster("premier test", 24, pixels)
    #rasterWthTxt.save(pathPNG + "/img1.png")
    """
    count = 0
    for file in os.listdir(pathDCM):
        ds = dcmread(file)
        pixels = ds.pixel_array
        
        dicom2png(file, pathPNG + 'test' + count)
        count += 1
    """

    #textToAdd = generateRandomTxt()
    #addTxt2Png(textToAdd)



"""
Generates 10 random texts with sample information.
"""
def generateRandomTxt():
    patients = generateRandomPatients()
    textToAdd = []

    for patient in patients:
        txt = """
Patient n°{0},
{1}, 
Âge : {2} ans, 
Adresse : {3}
        """.format(
            patient.get('id'),
            patient.get('nom'),
            patient.get('age'),
            patient.get('adresse')
        )
        print(txt)
        textToAdd.append(txt)
    
    return textToAdd
        
    
    
"""
Generates each information for each patient (id, age, nom, adresse)
"""
def generateRandomPatients():

    patients = []

    with open('./sample_data/nom_patient.txt') as file:
        noms = file.readlines()

    with open('./sample_data/adresse_patient.txt') as file:
        adresses = file.readlines()

    #Creates 10 new sample patients
    for i in range(10):
        id_patient = random.randint(0, 99999999999)
        age = random.randint(0, 100)
        #Adds the name and removes the '\n' at each line
        nom = noms[i].replace('\n','')
        adresse = adresses[i]

        nouv_patient = {
            "id": id_patient,
            "nom": nom,
            "age": age,
            "adresse": adresse
        }

        patients.append(nouv_patient)
    return patients


"""
Writes text on each picture located in the folder path.
"""
def addTxt2Raster(textToAdd, size, pixels):
    
    #Selects a font and sets font parameters (size...)
    target_font = os.listdir(pathFonts)[0]
    img_font = ImageFont.truetype(target_font, size=size)

    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8(cm.bone(pixels)*255))
    im.convert('RGB')
    


    #Adds the text on the pillow image
    draw = ImageDraw.Draw(im)
    draw.text((5,5), textToAdd)
    #draw.text((5,5), textToAdd[0], (255,255,255), font=font)
    im.save(pathPNG + "/img_pillow.png")
    del draw

    #Converts the pillow image into a numpy array and returns it
    return np.asarray(im)



"""
Converts a DICOM into a NUMPY array. Manages the RGB problems happening during the conversion.
Returns a numpy array which can be handled by Pillow.
"""
def read_xray(path, voi_lut = True, fix_monochrome = True):
    dicom = pydicom.read_file(path)
    
    # VOI LUT (if available by DICOM device) is used to transform raw DICOM data to "human-friendly" view
    if voi_lut:
        data = apply_voi_lut(dicom.pixel_array, dicom)
    else:
        data = dicom.pixel_array
               
    # depending on this value, X-ray may look inverted - fix that:
    if fix_monochrome and dicom.PhotometricInterpretation == "MONOCHROME1":
        data = np.amax(data) - data
        
    data = data - np.min(data)
    data = data / np.max(data)
    data = (data * 255).astype(np.uint8)
        
    return data


if __name__ == '__main__':
    main()