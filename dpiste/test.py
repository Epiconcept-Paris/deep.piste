import random
import string
from dicom2png import dicom2narray, narray2dicom
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_color_lut, apply_modality_lut, apply_voi_lut
from p08_anonymize import *

pathDCM = '/home/williammadie/images/test20/dicom'
pathPNG = '/home/williammadie/images/test20/png'
pathFonts = '/home/williammadie/images/fonts'


"""

This module aims at generating partially random texts and adding these texts to
test images and then treating them with the OCR module.

"""



def main():    
    count = 1
    for file in sorted(os.listdir(pathDCM)):
        dicom = dicom2narray(pathDCM + "/" + file)
        pixels = dicom[0]
        test_words = generate_random_words(50, 10)
        
        pixels = addTxt2Raster(random_text, random.randint(30,60), pixels, count)
        #TODO: remove this step (save preprocess PNG)
        img = Image.fromarray(pixels)
        print(file + "-->" + pathPNG + "/preprocess/preprocess" + str(count) + ".png")
        img.save(pathPNG + "/preprocess/preprocess" + str(count) + ".png")
        

        ocr_data = get_text_areas(pixels)
        pixels = hide_text(pixels, ocr_data)
        
        narray2dicom(pixels, dicom[1], (pathPNG + "/dicom/de_identified" + str(count) + ".dcm"))
        
        count += 1

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
Get the minimal and the maximal value in a two-dimensional array.
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
Generate 'nb_words' random words composed from 1 to 'nb_character_max' ASCII characters.
"""
def generate_random_words(nb_words, nb_character_max, nb_character_min = 3):
    words = []

    for i in range(nb_words):
        word = string.ascii_letters
        word = ''.join(random.choice(word) for i in range(random.randint(nb_character_min,nb_character_max)))
        words.append(word)
    
    return words
        


"""
Write text on each picture located in the folder path.
"""
def add_words_on_image(pixels, words, text_size, font = 'random', color = 255):
    
    if font == 'random':
        font = os.listdir(pathFonts)[random.randint(0,len(os.listdir(pathFonts))-1)]
    img_font = ImageFont.truetype(font, text_size)

    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))
    
    nb_rows = 40
    image_width = pixels.shape[0]
    image_height = pixels.shape[1]

    length_cell = image_width/nb_rows
    height_cell = image_height/nb_rows

    #Creates an array of 'nb_rows x nb_rows' filled with 0.
    words_array = words_array = np.full((nb_rows, nb_rows), 0)

    count = 0
    for word in words:
        #While the cell is occupied by a word, we keep looking for a free cell
        random_cell = -1
        x_cell = -1
        y_cell = -1
        while random_cell != 0:
            random_cell = random.randint(words_array.size)
            
            #Gets the x and the y of the random_cell
            num_cell = 0
            for x in range(nb_rows):
                for y in range(nb_rows):
                    num_cell += 1
                    if num_cell == random_cell:
                        x_cell = x
                        y_cell = y
        
        #The array memorizes the position of the word in the list 'words'
        words_array[x_cell][y_cell] = count
        

        x_cell = x_cell * length_cell
        y_cell = y_cell * height_cell
        #Position of the word on the image
        draw = ImageDraw.Draw(im)
        #x = (pixels.shape)[1]-200
        #y = (pixels.shape)[0]-200
        #x = random.randint(0, x)
        #y = random.randint(0, y)
        #color = random.randint(0, 255)
        x,y = 2,5
        print("X = ", x, " | Y = ",y)
        #Adds the text on the pillow image
        draw.text((x, y), words[count], fill=color, font=img_font)
        count += 1
        del draw

    #Test blur effect
    box = (x,y,x+650,y+650)            
    cut = im.crop(box)
    for i in range(random.randint(3,5)):
        cut = cut.filter(ImageFilter.BLUR)
    im.paste(cut, box)

    #Converts the pillow image into a numpy array and returns it
    return np.asarray(im)



"""
Refresh the words array 
"""
def add_word_in_words_array():
    
    image_width = 1200
    image_height = 800

    #image_width = pixels.shape[0]
    #image_height = pixels.shape[1]

    #Creates an array of 'nb_rows x nb_rows' cells filled with 0. 
    words_array = np.full((nb_rows, nb_rows), 0)
    print(words_array.shape)
    print(words_array.size)
    print(words_array)


"""
Write the dataset of all the DICOM in the directory_path in a text file.
"""
def getDataset(dataset):
    
    count = 1
    for file in sorted(os.listdir(path=pathDCM)):
        dicom = pydicom.read_file(file)

        with open(pathPNG + "/dataset/dataset" + str(count) + ".txt") as file:
            file.write(str(dataset))
        count += 1


if __name__ == '__main__':
    create_words_array(10)