import random
import string
from dicom2png import dicom2narray, narray2dicom
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_color_lut, apply_modality_lut, apply_voi_lut
from p08_anonymize import *

pathDCM = '/home/williammadie/images/test1/dicom'
pathPNG = '/home/williammadie/images/test1/png'
pathFonts = '/home/williammadie/images/fonts'


"""

This module aims at generating partially random texts and adding these texts to
test images and then treating them with the OCR module.

"""



def main():    
    count = 1
    sum_ocr_recognized_words = 0
    sum_total_words = 0
    for file in sorted(os.listdir(pathDCM)):
        dicom = dicom2narray(pathDCM + "/" + file)
        pixels = dicom[0]

        #Gets False Positives
        ocr_data = get_text_areas(pixels)
        ocr_ghost_words = calculate_false_positive(ocr_data)

        test_words = generate_random_words(50, 10)
        
        (pixels, words_array) = add_words_on_image(pixels, test_words, random.randint(30,40), blur=0)
        #TODO: remove this step (save preprocess PNG)
        img = Image.fromarray(pixels)
        print(file + "-->" + pathPNG + "/preprocess/preprocess" + str(count) + ".png")
        img.save(pathPNG + "/preprocess/preprocess" + str(count) + ".png")
        
        ocr_data = get_text_areas(pixels)
        
        (ocr_recognized_words, total_words) = compare_ocr_data_and_reality(test_words, words_array, ocr_data)
        sum_ocr_recognized_words += ocr_recognized_words
        sum_total_words += total_words

        tp = sum_ocr_recognized_words
        fn = sum_total_words - sum_ocr_recognized_words
        fp = ocr_ghost_words

        print("TOTAL : ", sum_ocr_recognized_words, "/", sum_total_words, " words recognized")
        print("True positive (recognized words): ", tp)
        print("False negative (unrecognized words): ", fn)
        print("False positive (ghost words) : ", fp)
        accuracy = (tp) / (tp + fn + fp)*100
        precision = tp / (tp+fp)
        recall = tp / (tp+fn)
        f1_score = (2 * precision * recall) / (precision + recall)
        print("Precision : ", round(precision,1))
        print("Recall : ", round(recall,1))
        print("F1_Score : ", round(f1_score,1))
        print("Accuracy : ", round(accuracy, 1), "%")
        #pixels = hide_text(pixels, ocr_data)
        
        #narray2dicom(pixels, dicom[1], (pathPNG + "/dicom/de_identified" + str(count) + ".dcm"))
        
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
def add_words_on_image(pixels, words, text_size, font = 'random', color = 255, blur = 0):
    
    if font == 'random':
        font = os.listdir(pathFonts)[random.randint(0,len(os.listdir(pathFonts))-1)]
    img_font = ImageFont.truetype(font, text_size)

    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))
    
    nb_rows = 15
    image_width = pixels.shape[1]
    image_height = pixels.shape[0]

    length_cell = image_width/nb_rows
    height_cell = image_height/nb_rows

    #Creates an array of 'nb_rows x nb_rows' filled with 0.
    words_array = words_array = np.full((nb_rows, nb_rows), 0)

    count = 0
    for word in words:
        #While the cell is occupied by a word or too luminous, we keep looking for anoter free cell
        random_cell = -1
        x_cell = -1
        y_cell = -1
        is_null = False
        nb_tries = 0
        while not is_null:
            random_cell = random.randint(0, words_array.size)
            
            #Gets the x and the y of the random_cell
            num_cell = 0
            for x in range(nb_rows):
                for y in range(nb_rows):
                    if num_cell == random_cell:
                        x_cell = x
                        y_cell = y
                    num_cell += 1

            #The array memorizes the position of the word in the list 'words'
            if words_array[x_cell][y_cell] == 0 and x_cell < nb_rows-2 and is_the_background_black_enough(x_cell, y_cell, length_cell, height_cell, im):
                if words_array[x_cell+2][y_cell] == 0:
                    if words_array[x_cell+1][y_cell] == 0:
                        words_array[x_cell][y_cell] = count+1
                        words_array[x_cell+1][y_cell] = count+1
                        words_array[x_cell+2][y_cell] = count+1
                        is_null = True
                        nb_tries = 0
            nb_tries += 1

            if nb_tries >= 120:
                break
                    
        if nb_tries < 120:
            #x and y coordinates on the image
            x_cell = x_cell * length_cell
            y_cell = y_cell * height_cell
            
            #Position of the word on the image
            draw = ImageDraw.Draw(im)
            
            print("X = ", x_cell, " | Y = ",y_cell)
            #Adds the text on the pillow image
            draw.text((x_cell, y_cell), words[count], fill=color, font=img_font)
            
            #Blur effect
            box = (int(x_cell), int(y_cell), int(x_cell + 2 * length_cell), int(y_cell + height_cell))            
            cut = im.crop(box)
            for i in range(blur):
                cut = cut.filter(ImageFilter.BLUR)
            im.paste(cut, box)
        
            count += 1
            del draw

    #Converts the pillow image into a numpy array and returns it
    return (np.asarray(im), words_array)



"""
Checks if the area chosen for the text is black enough to set white text on it.
returns True if the area is correct. Returns False in other cases.
"""
def is_the_background_black_enough(x_cell, y_cell, length_cell, height_cell, im):
    
    if x_cell == -1 and y_cell == -1:
        return False

    x_im = x_cell * length_cell
    y_im = y_cell * height_cell

    box = (x_im, y_im, x_im+length_cell, y_im+height_cell)
    cut = im.crop(box)

    area_array = np.asarray(cut)

    avg = 0
    for x in range(len(area_array)):
        for y in range(len(area_array[x])):
            avg += area_array[x][y]
    avg /= area_array.size

    return avg < 20



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



"""
Calculates the amount of false positive
"""
def calculate_false_positive(ocr_data):
    #Get the number of ghost words (which are inexistant)
    ocr_ghost_words = 0
    for found in ocr_data:
            ocr_ghost_words += 1
    return ocr_ghost_words



"""
Calculates the amount of true positive
"""
def compare_ocr_data_and_reality(test_words, words_array, ocr_data):
    indices_words_reality = []
    ocr_recognized_words = 0

    #If the array contains an indice different than 0, we add it to a list.
    for x in range(len(words_array)):
        for y in range(len(words_array[x])):
            if words_array[x][y] != 0:
                indices_words_reality.append(words_array[x][y])

    #Remove duplicates
    indices_words_reality = list(dict.fromkeys(indices_words_reality))

    #Get the number of words present on the picture
    total_words = 0
    for word in indices_words_reality:
        total_words += 1

    #Get the number of words recognized 
    for found in ocr_data:
        if found[1] in test_words:
            ocr_recognized_words += 1
    print(ocr_recognized_words, "/", total_words)
    return (ocr_recognized_words, total_words)

if __name__ == '__main__':
    main()