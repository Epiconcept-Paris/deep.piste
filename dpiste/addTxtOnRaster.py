import random
from dicom2png import dicom2narray
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_color_lut, apply_modality_lut, apply_voi_lut
from p08_anonymize import *

pathDCM = '/home/williammadie/images/test30/dicom'
pathPNG = '/home/williammadie/images/test30/png'
pathFonts = '/home/williammadie/images/fonts'


"""

This module aimed at generating partially random texts and adding these texts to
test images before treating them with the OCR module.

"""



def main():
    #Converts the DICOM into a numpy array and manages the color problems linked to MONOCHROME2
    
    count = 1
    random_text = generateRandomTxt()
    for file in sorted(os.listdir(pathDCM)):
        pixels = dicom2narray(pathDCM + "/" + file)
        #summarizeDcmInfo(pixels, file, count)
        
        pixels = addTxt2Raster(random_text, random.randint(30,60), pixels, count)

        img = Image.fromarray(pixels)
        print(file + "-->" + pathPNG + "/preprocess" + str(count) + ".png")
        img.save(pathPNG + "/preprocess" + str(count) + ".png")
        count += 1

        get_text_on_picture_easyocr(pixels)


"""
Development function which prints useful information of the narray (@param pixels)
"""
def summarizeDcmInfo(pixels, file, count):
    strObtenue = """
Nbre de dimensions : {0},
Taille dim1, dim2 : {1},
Nbre total d'éléments : {2},
Taille dimension 1 : {3},
(vMin, vMax) contenu dans une cellule : {4},
MONOCHROME : {5}

==================================================
        """.format(
            pixels.ndim,
            pixels.shape,
            pixels.size,
            len(pixels),
            getVminVmax(pixels),
            pydicom.read_file(pathDCM + "/" + file).PhotometricInterpretation
        )
    print("==================================================\n")
    print("Image n°" + str(count) + " : " + file + "\n" + strObtenue )




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
Generates 20 random texts with sample information.
"""
def generateRandomTxt():
    patients = generateRandomPatients()
    textToAdd = []

    for patient in patients:
        txt = """
Patient n°{0},\n
{1},\n 
Âge : {2} ans,\n 
Adresse : {3}\n
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

    with open('/home/williammadie/images/sample_data/nom_patient.txt') as file:
        noms = file.readlines()

    with open('/home/williammadie/images/sample_data/adresse_patient.txt') as file:
        adresses = file.readlines()

    #Creates 20 new sample patients
    for i in range(20):
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
def addTxt2Raster(textToAdd, size, pixels, count):
    
    #Selects a font and sets font parameters (size...)
    target_font = os.listdir(pathFonts)[random.randint(0,len(os.listdir(pathFonts))-1)]
    print(target_font)
    img_font = ImageFont.truetype(target_font, size)

    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))
    #NB: The following line alters the initial colors. May be removed.
    #im.convert('RGB') 
    

    #Adds the text on the pillow image
    draw = ImageDraw.Draw(im)
    draw.text((2,5), textToAdd[count-1], fill=255, font=img_font)
    #draw.text((5,5), textToAdd[0], (255,255,255), font=font)
    #im.save(pathPNG + "/img_pillow.png")
    del draw

    #Converts the pillow image into a numpy array and returns it
    return np.asarray(im)


if __name__ == '__main__':
    main()