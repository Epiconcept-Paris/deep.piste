import time
import dpiste
import pydicom
import numpy as np
from dpiste.p08_mammogram_deidentification import *
from dpiste import utils
from kskit.dicom2png import dicom2narray, narray2dicom
from kskit.test_deid_mammogram import *



"""

This module aims at evaluating the OCR package abilities. 
It generates and adds random texts to test images and then treats them with 
the OCR module.

"""

def test_OCR(font, size, blur, repetition, indir = None, outdir = None):    
    start_time = time.time()
    #Default values
    utils.get_home('data', 'input', 'test_deid_ocr','')
    utils.get_home('data','output','test_deid_ocr','')
    utils.get_home('data','transform','test_deid_ocr','')
    if indir == None:
        indir = os.environ.get('DP_HOME') + '/data/input/test_deid_ocr'
    if outdir == None:
        outdir = os.environ.get('DP_HOME') + '/data/output/test_deid_ocr'

    pkg_dir, this_filename = os.path.split(__file__)
    PATH_FONTS = os.path.join(pkg_dir, "data/resources/fonts/")
    PATH_ATTRIBUTES_TO_KEEP = os.path.join(pkg_dir, "data/resources/deid_ref/attributes_to_keep.json")
    
    if font is None:
        font = [PATH_FONTS + 'FreeMono.ttf']
    if size is None:
        size = [2]
    if blur is None:
        blur = [0]
    if repetition is None:
        repetition = 1

    check_resources(PATH_FONTS, font, size, blur)

    sum_ocr_recognized_words, sum_total_words, nb_images_tested = 0, 0, 1
    tp, tn, fp, fn = 0, 0, 0, 0
    
    pathname = indir + "/**/*"
    list_dicom = glob.glob(pathname, recursive=True)
    list_dicom = sorted(list_dicom)
    
    if not list_dicom:
        raise ValueError(indir + " seems to be empty or does not exist") 
    
    list_chosen = []
    result = ""

    #Tests for false positives
    
    (nb_images_tested, list_chosen, summary, fp, tn) = search_false_positives(
        indir, list_dicom, list_chosen, outdir, repetition, nb_images_tested, fp, tn)
    
    #Tests for criteria FONT, SIZE & BLUR
    nb_images_total = len(font)*len(size)*len(blur)*3 + 3
    summary += "\n\n\nTested with several FONT SIZE & BLUR parameters x" + \
    str(nb_images_total - 3) + "\n\n\n"
    for index_font in range(len(font)):
        for index_size in range(len(size)):
            for index_blur in range(len(blur)):
                for r in range(repetition):
                    (pixels, ds, dicom, file_path, list_chosen) = get_random_dicom_ds_array(
                        list_dicom, indir, list_chosen
                        )
                    
                    if pixels.size < 100000:
                        test_words = generate_random_words(random.randint(1,1), 5)
                    elif size[index_size] > 3:
                        test_words = generate_random_words(random.randint(1,5), 5)
                    else:
                        test_words = generate_random_words(random.randint(1,10), 10)
                    test_words_keep = test_words
                    (pixels, words_array, test_words) = add_words_on_image(
                        pixels, test_words, size[index_size], 
                        font=(PATH_FONTS + font[index_font]), blur=blur[index_blur]
                        )

                    img = Image.fromarray(pixels)
                    output_png = "{}/{}_{}_{}_{}_before".format(
                        outdir,
                        os.path.basename(dicom), 
                        size[index_size], 
                        font[index_font], 
                        blur[index_blur]
                    )
                    dicom2png.narray2png(pixels, output_png)
                    #img.save(outdir + '/' + os.path.basename(dicom) + ".png")

                    ocr_data = get_text_areas(pixels)
            
                    (ocr_recognized_words, total_words) = compare_ocr_data_and_reality(
                        test_words, words_array, ocr_data
                        )

                    #Test numbers :
                    sum_ocr_recognized_words += ocr_recognized_words
                    sum_total_words += total_words

                    #Calculate test model values
                    (tp, tn, fn) = calculate_test_values(
                        total_words, ocr_recognized_words, tp, tn, fn
                        )

                    if outdir.endswith("/"):
                        output_path = outdir  + os.path.basename(file_path)
                        output_ds = outdir + os.path.basename(file_path) + ".txt"
                        output_summary = outdir + "summary.log"
                    else:
                        output_path = outdir  + '/' + os.path.basename(file_path)
                        output_ds = outdir + "/" + os.path.basename(file_path) + ".txt"
                        output_summary = outdir + "/summary.log"
                    
                    output_path = file_path.replace(indir, outdir)
                    output_ds = file_path.replace(indir, outdir)
                    output_summary = file_path.replace(indir, outdir)

                    result = save_test_information(
                        nb_images_tested, nb_images_total, sum_ocr_recognized_words, sum_total_words, 
                        ocr_recognized_words, total_words, tp, tn, fp, fn, outdir, file_path, result
                        )
                    save_dicom_info(
                        "{}/{}_{}_{}_{}.txt".format(
                            outdir,
                            os.path.basename(dicom), 
                            size[index_size], 
                            font[index_font], 
                            blur[index_blur]
                        ), 
                        file_path, ds, ocr_data, test_words_keep, total_words)
                    
                    summary += "\n" + file_path + "\n↪parameters : F = " \
                         + str(os.path.basename(font[index_font])) + " | B = " \
                             + str(blur[index_blur]) + " | S = " + str(size[index_size])
                    nb_images_tested += 1


                    pixels = hide_text(pixels, ocr_data, color_value = 'white')
                    #narray2dicom(pixels, ds, output_path)

                    output_png = "{}/{}_{}_{}_{}_after".format(
                        outdir,
                        os.path.basename(dicom), 
                        size[index_size], 
                        font[index_font], 
                        blur[index_blur]
                    )
                    dicom2png.narray2png(pixels, output_png)



    time_taken = time.time() - start_time
    with open(outdir + '/test_summary.log', 'w') as f:
        f.write(
          str(round(time_taken/60)) + " minutes taken to process all images.\n" + \
          summary)
            
