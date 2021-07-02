from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader  #easyocr package
import pytesseract          #pytesseract package
from pytesseract import Output  #pytesseract package
import argparse
import os
import cv2      #opencv-python
import dicom2png
import numpy as np

"""
At the moment, this module only contains test functions.
"""

pathDCM = '/home/williammadie/images/test30/dicom'
pathPNG = '/home/williammadie/images/test30/png'
pathFonts = '/home/williammadie/images/fonts'

"""
Pytesseract Test function. Gets an image a the path below and gets the text of the picture.
It also add a green line all around the text areas. 
"""
def highlight_text_on_picture_pytesseract():
    #Reads the targeted image
    img = cv2.imread('/home/williammadie/images/test_5.png')
    
    #Converting the image into a gray only version
    #img =cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #Applies a filter in order for the algorithm to recognize easily the text
    #cv2.medianBlur(img, 3)

    #Converts the image into a data format
    data = pytesseract.image_to_data(img, output_type=Output.DICT)
    print(data.keys())

    #Get the text areas and draw green rectangle around them
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > 60:
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow('img', img)
    cv2.waitKey(0)


"""
Easy OCR Test function. Gets an image at the path below and gets the text of the picture. 
"""
def get_text_areas(pixels):
    reader = Reader(['fr'])
    result = reader.readtext(pixels)
    
    #Orders the output (= the different text area found in the picture)
    count = 0
    for found in result:
        print("Zone n°{} | ".format(count), found[1])
        print("Zone n°{} | ".format(count), found[0])
        count += 1

    return result


"""
Get a NUMPY array, a list of the coordinates of the different text areas in this array
and (optional) a mode which can be : "blur" or "black". It returns the modified NUMPY array.

MODES (optional):

"black" mode (default) ==> add a black rectangle on the text areas
"blur" mode            ==> blur the text areas
"""
def hide_text(pixels, ocr_data, mode = "black"):
    #Create a pillow image from the numpy array
    pixels = pixels/255
    im = Image.fromarray(np.uint8((pixels)*255))

    #Gets the coordinate of the top-left and the bottom-right points
    for found in ocr_data:
        #This condition avoids common false positives
        if found[1] != "" and len(found[1]) > 1:
            #TODO: remove the following (debug info) 
            print("Tous les points : ", found[0])
            x1, y1 = int(found[0][0][0]), int(found[0][0][1])
            x2, y2 = int(found[0][2][0]), int(found[0][2][1])
            print("Point en haut à gauche : ", x1, y1)
            print("Point en bas à droite : ", x2, y2)

            box = (x1,y1,x2,y2)
            
            #Applies a hiding effect
            if mode == "blur":
                cut = im.crop(box)
                for i in range(30):
                    cut = cut.filter(ImageFilter.BLUR)
                im.paste(cut, box)
            else:
                #Add a black rectangle on the targeted text
                draw = ImageDraw.Draw(im)

                #If the value is a tuple, the color has to be a tuple (RGB image)
                if type(pixels[0][0]) == tuple:
                    color = (0,0,0)
                else:
                    color = 0
                draw.rectangle([x1, y1, x2, y2], fill=color)
                del draw

    return np.asarray(im)




if __name__ == '__main__':
    print("test")

