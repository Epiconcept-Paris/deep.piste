from PIL import Image
from easyocr import Reader  #easyocr package
import pytesseract          #pytesseract package
from pytesseract import Output  #pytesseract package
import argparse
import os
import cv2      #opencv-python
import dicom2png

"""
At the moment, this module only contains test functions.
"""

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
def get_text_on_picture_easyocr():
    #Converts the DICOM into PNG
    #dicom2png.dicom2png('/home/williammadie/images/image-valide.dcm','/home/williammadie/images/1-0.png')
    
    reader = Reader(['fr'])
    result = reader.readtext('/home/williammadie/images/test_5.png')
    
    #Orders the output (= the different text area found in the picture)
    count = 0
    for found in result:
        print("Zone n°{} | ".format(count), found)
        count += 1




#Adds new arguments (temporary)
"""
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to input image to be OCR'd")
    
ap.add_argument("-p", "--preprocess", type=str, default="thresh",
	help="type of preprocessing to be done")
args = vars(ap.parse_args())
"""

if __name__ == '__main__':
    #get_text_on_picture_py()
    highlight_text_on_picture_pytesseract()

