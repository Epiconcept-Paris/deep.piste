from PIL import Image
import pytesseract
from pytesseract import Output
import argparse
import os
import cv2

def highlight_text_on_picture():
    #Reads the targeted image
    img = cv2.imread('/home/williammadie/Downloads/radioHD.jpg')
    
    #Converting the image into a gray only version
    img =cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #Applies a filter in order for the algorithm to see easily the text
    cv2.medianBlur(img, 3)

    #Converts the image into a data format
    data = pytesseract.image_to_data(img, output_type=Output.DICT)
    print(data.keys())

    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > 60:
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow('img', img)
    cv2.waitKey(0)

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
    highlight_text_on_picture()

