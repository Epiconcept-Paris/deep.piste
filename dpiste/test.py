import random
import string
from datetime import datetime
import os
from typing import Type
import pydicom
import numpy as np
from dicom2png import dicom2narray, narray2dicom
from PIL import Image, ImageFont, ImageDraw
from p08_anonymize import *

PATH_DCM = '/home/williammadie/images/test20/dicom'
PATH_PNG = '/home/williammadie/images/test20/png'
PATH_FONTS = '/home/williammadie/images/fonts'

"""

This module aims at generating partially random texts and adding these texts to
test images and then treating them with the OCR module.

"""

def main(indir = PATH_DCM, outdir = PATH_PNG, font = 'random', size = 'auto', blur = 0):    
    #Default values
    if font == None:
        font = 'random'
    if size == None:
        size = 'auto'
    if blur == None:
        blur = 0

    sum_ocr_recognized_words, sum_total_words, nb_images_tested = 0, 0, 1
    tp, tn, fp, fn = 0, 0, 0, 0

    for file in sorted(os.listdir(indir)):
        if indir.endswith("/"):
            dicom = dicom2narray(indir + file)
            file_path = indir + file
        else:
            dicom = dicom2narray(indir + "/" + file)
            file_path = indir + '/' + file
        
        pixels = dicom[0]

        #Get ghost words (in order to calculate False Positives)
        ocr_data = get_text_areas(pixels)
        ghost_words = is_there_ghost_words(ocr_data)
        
        if pixels.size < 100000:
            #Security mechanism in the case where the image is too small to host 10 words of 10 char
            #Generate 0 to 1 random word of max 5 characters 
            test_words = generate_random_words(random.randint(0,1), 5)
        else:
            #Generate 0 to 10 random words of max 10 characters 
            test_words = generate_random_words(random.randint(0,10), 10)
            
        
        (pixels, words_array, test_words) = add_words_on_image(pixels, test_words, size, font=font, blur=blur)
        
        #TODO: remove this step (save preprocess PNG)
        img = Image.fromarray(pixels)
        if outdir.endswith('/'):
            print(file + "-->" + outdir + os.path.basename(file) + ".png")
            img.save(outdir + os.path.basename(file) + ".png")
            output_ds = outdir + os.path.basename(file) + ".txt"
        else:
            print(file + "-->" + outdir + "/" + os.path.basename(file) + ".png")
            img.save(outdir + "/" + os.path.basename(file) + ".png")
            output_ds = outdir + "/" + os.path.basename(file) + ".txt"
        
        ocr_data = get_text_areas(pixels)
        
        (ocr_recognized_words, total_words) = compare_ocr_data_and_reality(test_words, words_array, ocr_data)
        

        #Test numbers :
        sum_ocr_recognized_words += ocr_recognized_words
        sum_total_words += total_words

        #Calculate test model values
        (tp, tn, fp, fn) = calculate_test_values(ghost_words, total_words, ocr_recognized_words, tp, tn, fp, fn)        
        save_test_information(nb_images_tested, sum_ocr_recognized_words, sum_total_words, ocr_recognized_words, total_words, tp, tn, fp, fn, outdir)

        #Write the dataset of the image
        with open(output_ds,'a') as f:
            print(file_path)
            f.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n' + file_path + '\n' + str(dicom[1]) + '\n' + str(ocr_data))
            
        #pixels = hide_text(pixels, ocr_data)
        #narray2dicom(pixels, dicom[1], (pathPNG + "/dicom/de_identified" + str(count) + ".dcm"))
        
        nb_images_tested += 1



"""
Development function which prints useful information of the narray (@param pixels)
"""
def summarize_dcm_info(pixels, file, count):
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
            get_vmin_vmax(pixels),
            pydicom.read_file(PATH_DCM + "/" + file).PhotometricInterpretation
        )
    print("==================================================\n")
    print("Image n°" + str(count) + " : " + file + "\n" + strObtenue )



"""
Get the minimal and the maximal value in a two-dimensional array.
Returns a tuple with (Minimal value, Maximal value)
"""
def get_vmin_vmax(two_dim_array):
    v_min, v_max = 0, 0

    for x in range(len(two_dim_array)):
        for y in range(len(two_dim_array[x])):
            if two_dim_array[x][y] > v_max:
                v_max = two_dim_array[x][y]
            if two_dim_array[x][y] < v_min:
                v_min = two_dim_array[x][y]
    return (v_min, v_max)



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
    nb_rows = 15
    
    #No words = empty array
    if len(words) == 0:
        words_array = words_array = np.full((nb_rows, nb_rows), 0)
        return (pixels, words_array, words)

    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))


    if font == 'random':
        font = os.listdir(PATH_FONTS)[random.randint(0,len(os.listdir(PATH_FONTS))-1)]
    
    #Auto-scale the size of the text according to the image width
    if text_size == 'auto':
        text_size = auto_scale_font_size(pixels, words, font)
        print(text_size)
    img_font = ImageFont.truetype(font, text_size)
    
    #Intialize the information for 'words_array' 
    image_width, image_height = pixels.shape[1], pixels.shape[0]
    length_cell, height_cell = image_width/nb_rows, image_height/nb_rows

    #Creates an array of 'nb_rows x nb_rows' filled with 0.
    words_array = words_array = np.full((nb_rows, nb_rows), 0)

    count = 0
    for word in words:
        #While the cell is occupied by a word or too luminous, we keep looking for anoter free cell
        random_cell, x_cell, y_cell, nb_tries = -1, -1, -1, 0
        is_null = False
        while not is_null:
            random_cell = random.randint(0, words_array.size)
            
            #Gets the x and the y of the random_cell
            num_cell = 0
            for x in range(nb_rows):
                for y in range(nb_rows):
                    if num_cell == random_cell:
                        x_cell, y_cell = x, y
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

            #If the number of tries exceeds the limit, we remove the word from the list
            if nb_tries >= 120:
                break
           
        if nb_tries < 120:
            #x and y coordinates on the image
            x_cell = x_cell * length_cell
            y_cell = y_cell * height_cell
            
            #Position of the word on the image
            draw = ImageDraw.Draw(im)
            
            #Adds the text on the pillow image
            draw.text((x_cell, y_cell), words[count], fill=color, font=img_font)
            
            #Blur effect
            if blur != 0:
                im = blur_it(im, blur, x_cell, y_cell, length_cell, height_cell)
            
            count += 1
            del draw

    #Converts the pillow image into a numpy array and returns it
    return (np.asarray(im), words_array, words)



"""
Rescale the text depending on the the width of an image.
Parameters : pixels (narray of the image)
words : a list of the words to add on the picture
font : the path of the font to use 
"""
def auto_scale_font_size(pixels, words, font):
    text_size = 1
    img_font = ImageFont.truetype(font, text_size)
    img_fraction = 0.1
    
    while img_font.getsize(max(words, key=len))[0] < img_fraction*pixels.shape[1]:
        text_size += 1
        img_font = ImageFont.truetype(font, text_size)
    text_size -= 1

    if text_size < 18:
        text_size = 18

    return text_size



"""
Blur a specified rectangle area on a picture. Parameters :
Image to blur, strength of the blur effect, x and y of the top-left corner of the area,
length_cell and height_cell : length and height of the rectangle.  
"""
def blur_it(image, blur, x, y, length_cell, height_cell):
    box = (int(x), int(y), int(x + 2 * length_cell), int(y + height_cell))            
    cut = image.crop(box)
    for i in range(blur):
        cut = cut.filter(ImageFilter.BLUR)
    image.paste(cut, box)

    return image



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
Export the dataset in text files for each the DICOM in the directory_path.
"""
def getDataset(dataset):
    
    count = 1
    for file in sorted(os.listdir(path=PATH_DCM)):
        dicom = pydicom.read_file(file)

        with open(PATH_PNG + "/dataset/dataset" + str(count) + ".txt") as file:
            file.write(str(dataset))
        count += 1



"""
Check if there is a difference of max two letters between two words of the same size OR
a difference of two letters plus an extra letter for one of the two words.
"""
def has_a_two_letters_difference(word_1, word_2):
    word_1, word_2 = str(word_1), str(word_2)

    #Word_1 has to be the shortest for this function and has to be one char max bigger than word_2
    if len(word_1) > len(word_2):
        word_1, word_2 = word_2, word_1
    
    if len(word_1)+1 < len(word_2):
        return False

    differences = []
    count = 0
    for letter in word_1:
        if word_2[count] == letter:
            differences.append('*')
        else:
            differences.append(letter)
        count += 1
    
    nb_differences = 0
    for letter in differences:
        if nb_differences > 2:
            return False

        if letter != '*':
            nb_differences += 1

    return True
        


"""
Calculates the amount of ghost words on the image.
Ghost words refers to words or letters recognized by the OCR module where there is actually
no word or letter. 
"""
def is_there_ghost_words(ocr_data):
    for found in ocr_data:
            return True



"""
Calculates the model test values :
TP : True Positive  (There are words and every word has been recognized)
TN : True Negative  (There is no word and no word has been recognized)
FP : False Positive (There is no word but a word (or more) has been recognized)
FN : False Negative (There are words and NOT every word has been recognized)
"""
def calculate_test_values(ghost_words, total_words, ocr_recognized_words, tp, tn, fp, fn): 
    if ghost_words:
        fp += 1
    else:
        if total_words == 0:
            tn += 1
        else:
            if ocr_recognized_words/total_words == 1:
                tp += 1
            else:
                fn += 1
    return (tp, tn, fp, fn)



"""
Calculates the amount of recognized words compared to the total of words on the image
"""
def compare_ocr_data_and_reality(test_words, words_array, ocr_data):
    indices_words_reality = []
    ocr_recognized_words = 0

    print(test_words)

    for found in ocr_data:
        if ' ' in found[1]:
            print(found[1])
            new_tuple = (found[0], found[1].replace(' ',''), found[2])
            ocr_data.remove(found)
            ocr_data.append(new_tuple)
        print(found[1])
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

    #Set each word to lower case
    for word in range(len(test_words)):
        test_words[word] = test_words[word].lower()

    #Get the number of words recognized 
    for found in ocr_data:
        if found[1].lower() in test_words:
            ocr_recognized_words += 1
        #The OCR module has a tendency to confuse i and l or o and q. We help it because it does not matter for our work. 
        else:
            for word_pos in range(len(test_words)):
                if has_a_two_letters_difference(found[1].lower(), test_words[word_pos]):
                    print(found[1].lower(), "&&", test_words[word_pos], 
                    "==", has_a_two_letters_difference(found[1].lower(), test_words[word_pos]))
                    ocr_recognized_words += 1
                    break

    return (ocr_recognized_words, total_words)



"""
Save the test information in a .txt file. It contains main values linked to the past test.
"""
def save_test_information(nb_images_tested, sum_ocr_recognized_words, sum_total_words, 
ocr_recognized_words, total_words, tp, tn, fp, fn, outdir):
    #Counter Division by zero
    if tp != 0 or fp != 0:
        accuracy = (tp + tn) / (tp + tn + fn + fp)*100
        precision = tp / (tp+fp)
        recall = tp / (tp+fn)
        if precision == 0 and recall == 0:
            f1_score = -1
        else:
            f1_score = (2 * precision * recall) / (precision + recall)
    else:
        accuracy, precision, recall, f1_score = -1, -1, -1, -1

    accuracy, precision = round(accuracy, 1), round(precision, 1)
    recall, f1_score = round(recall, 1), round(f1_score, 1)
    result = """
\n
===========================================================================
Amount of images tested: {nb_images_tested}
TOTAL: {ocr_recognized_words}/{total_words} words recognized (last image)
GRAND TOTAL: {sum_ocr_recognized_words}/{sum_total_words} words recognized
True Positive (totally recognized images): {tp}
False Negative (NOT totally recognized images): {fn}
False Positive (Images with ghost words): {fp}
True Negative (Images with NO ghost words): {tn}
Precision: {precision}
Recall: {recall}
F1_Score: {f1_score}
Accuracy: {accuracy} % 
===========================================================================
\n
    """.format(
        nb_images_tested = nb_images_tested,
        ocr_recognized_words = ocr_recognized_words,
        total_words = total_words,
        sum_ocr_recognized_words = sum_ocr_recognized_words, 
        sum_total_words = sum_total_words,
        tp = tp,
        fn = fn, 
        fp = fp,
        tn = tn, 
        precision = precision, 
        recall = recall, 
        f1_score = f1_score, 
        accuracy = accuracy)
    print(result)

    if outdir.endswith('/'):
        file_path = outdir + "test_info.txt" 
    else:
        file_path = outdir + "/test_info.txt"
        
    with open(file_path, 'a') as f:
        f.write(result)



if __name__ == '__main__':
    main()