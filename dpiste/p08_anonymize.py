import os
import numpy as np

from PIL import Image, ImageDraw, ImageFilter
from easyocr import Reader

from dpiste import dicom2png



"""
Anonymize a complete directory of DICOM.

@param

indir = the initial directory of DICOM to de-identify
outdir = the final director of DICOM which have been de-identied
"""
def anonymize_folder(indir, outdir):
    count = 1
    for file in sorted(os.listdir(indir)):
    
        if indir.endswith("/"):
            input_path = indir + file
        else:
            input_path = indir + '/' + file
        
        dicom = dicom2png.dicom2narray(input_path)
        pixels = dicom[0]

        ocr_data = get_text_areas(pixels)
        pixels = hide_text(pixels, ocr_data)
        

        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir + os.path.basename(file) + ".txt"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir + "/" + os.path.basename(file) + ".txt"

        with open(output_ds,'a') as f:
            file_path = indir + file
            print(file_path)
            f.write(file_path)
            f.write('/n')
            f.write(str(dicom[1]))
            f.write('/n')
            f.write(str(ocr_data))
            f.write('/n')
            f.write()

        dicom2png.narray2dicom(pixels, dicom[1], output_path)



"""
Easy OCR Test function. Gets an image at the path below and gets the text of the picture. 
"""
def get_text_areas(pixels):
    reader = Reader(['fr'])
    result = reader.readtext(pixels)
    
    #Orders the output (= the different text area found in the picture)
    count = 0
    for found in result:
        #print("Zone n°{} | ".format(count), found[1])
        #print("Zone n°{} | ".format(count), found[0])
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


