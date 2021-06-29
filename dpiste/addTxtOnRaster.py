import random
import numpy as np
from pydicom import *
from PIL import Image, ImageFont, ImageDraw
import matplotlib.pyplot as plt
from matplotlib import cm
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_color_lut, apply_modality_lut, apply_voi_lut
import cv2 as cv

pathDCM = '/home/williammadie/images/test10/dicom'
pathPNG = '/home/williammadie/images/test10/png'
pathFonts = '/home/williammadie/images/fonts'


"""

This module aimed at generating partially random texts and adding these texts to
test images before treating them with the OCR module.

"""



def main():
    #Converts the DICOM into a numpy array and manages the color problems linked to MONOCHROME2
    count = 0
    for file in os.listdir(pathDCM):
        print(file)
        pixels = read_xray(pathDCM + "/" + file, count=count)
        strObtenue = """
Nbre de dimensions : {0},
Taille dim1, dim2 : {1},
Nbre total d'éléments : {2},
Taille dimension 1 : {3},
(vMin, vMax) contenu dans une cellule : {4},
MONOCHROME : {5}
        """.format(
            pixels.ndim,
            pixels.shape,
            pixels.size,
            len(pixels),
            getVminVmax(pixels),
            pydicom.read_file(pathDCM + "/" + file).PhotometricInterpretation
        )

        print("Image n°" + str(count) + "\n" + strObtenue)
        
        img = Image.fromarray(pixels)
        print(file + "-->" + pathPNG + "/preprocess" + str(count) + ".png")
        img.save(pathPNG + "/preprocess" + str(count) + ".png")
        count += 1

    #rasterWthTxt = addTxt2Raster("premier test", 24, pixels)
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
Gets the minimal and the maximal value in a two-dimensional array.
Returns a tuple with (Minimal value, Maximal value)
"""
def getVminVmax(TwoDimArray):
    vMax = 0
    vMin = 0
    for x in range(len(TwoDimArray)):
        for y in range(len(TwoDimArray[x])):
            if TwoDimArray[x][y] > vMax:
                vMax = TwoDimArray[x][y]
            if TwoDimArray[x][y] < vMin:
                vMin = TwoDimArray[x][y]
    return (vMin, vMax)



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
    #NB: The following line alters the initial colors. May be removed.
    #im.convert('RGB') 
    

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
def read_xray(path, count, voi_lut = True, fix_monochrome = True):
    dicom = pydicom.read_file(path)
    
    #TODO remove the 2 following lines
    #with open(pathPNG + "/dataset" + str(count) + ".txt", 'w') as file:
    #    file.write(str(dicom))
    
    # VOI LUT (if available by DICOM device) is used to transform raw DICOM data to "human-friendly" view
    if voi_lut:
        data = apply_voi_lut(dicom.pixel_array, dicom)
    else:
        data = dicom.pixel_array
        

    #TODO remove the 2 following lines
    #with open(pathPNG + "/img" + str(count) + ".txt", 'w') as file:
    #    file.write(str(data))

    # depending on this value, X-ray may look inverted - fix that:
    if fix_monochrome and dicom.PhotometricInterpretation == "MONOCHROME1":
        data = np.amax(data) - data

    #If the DICOM are not in one of these two formats, it can bring new problems.
    if dicom.PhotometricInterpretation != "MONOCHROME2" and dicom.PhotometricInterpretation != "MONOCHROME1":
        raise ValueError("Photométrie imprévue : " + dicom.PhotometricInterpretation)
    

    #np.seterr(divide='ignore', invalid='ignore')    <-- blocks the warning raised by DivisonByZero
    if dicom.Modality == "CT":
        try:
            slope = float(dicom.RescaleSlope)
            intercept = float(dicom.RescaleIntercept)
        except Exception:
            slope = 1
            intercept = 0
        if slope != 1 or intercept != 0:
            data = data * slope
            data = data + intercept
        
        data = data.astype(float)
        data = (np.maximum(data,0) / data.max()) * 255.0
        data = np.uint8(data)
        
    else:    
        data = data - np.min(data)
        data = data / np.max(data)
        data = (data * 255).astype(np.uint8)
        
    return data


if __name__ == '__main__':
    main()