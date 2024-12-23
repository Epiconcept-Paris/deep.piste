import glob
import os
import random
import time
from PIL import Image

from deidcm.deid_verification import (
    check_resources,
    search_false_positives,
    get_random_dicom_ds_array,
    generate_random_words,
    add_words_on_image,
    get_text_areas,
    compare_ocr_data_and_reality,
    calculate_test_values,
    save_test_information,
    save_dicom_info,
    run_test_deid_attributes
)
from deidcm.df2dicom_verification import df2dicom_test
from deidcm.dicom.deid_mammogram import hide_text
from deidcm import dicom2png
from deidcm.config import Config

from dpiste import utils
from dpiste.utils import log


def test_OCR(font, size, blur, repetition, indir=None, outdir=None, recipe_path=None, authorized_words_path=None):
    """
    Evaluates the OCR package abilities. It generates and adds random texts to 
    test images and then processes them with the OCR module.
    """
    start_time = time.time()
    deid_config = Config(recipe_path=recipe_path,
                         authorized_words_path=authorized_words_path)
    # Default values
    if indir is None:
        indir = utils.get_home('data', 'input', 'test_deid_ocr', '')
    if outdir is None:
        outdir = utils.get_home('data', 'output', 'test_deid_ocr', '')

    pkg_dir, _ = os.path.split(__file__)
    path_fonts = os.path.join(pkg_dir, 'data', 'resources', 'fonts')

    if font is None:
        font = ['FreeMono.ttf']
    if size is None:
        size = [2]
    if blur is None:
        blur = [0]
    if repetition is None:
        repetition = 1

    check_resources(path_fonts, font, size, blur)
    log(f'Words ignored by OCR: {deid_config.authorized_words}')
    sum_ocr_recognized_words, sum_total_words, nb_images_tested = 0, 0, 1
    tp, tn, fp, fn = 0, 0, 0, 0

    pathname = indir + "/**/*"
    list_dicom = glob.glob(pathname, recursive=True)
    list_dicom = sorted(list_dicom)

    if not list_dicom:
        raise ValueError(f'{indir} seems to be empty or does not exist')

    list_chosen, deleted_words = [], []
    result = ""

    # Tests for false positives

    (nb_images_tested, list_chosen, summary, fp, tn) = search_false_positives(
        indir, list_dicom, list_chosen, outdir, repetition, nb_images_tested, fp, tn)

    # Tests for criteria FONT, SIZE & BLUR
    nb_images_total = len(font)*len(size)*len(blur)*repetition + repetition
    summary += "\n\n\nTested with several FONT SIZE & BLUR parameters x" + \
        str(nb_images_total - 3) + "\n\n\n"
    for index_font, _ in enumerate(font):
        for index_size, _ in enumerate(size):
            for index_blur, _ in enumerate(blur):
                for r in range(repetition):
                    (pixels, ds, dicom, file_path, list_chosen) = get_random_dicom_ds_array(
                        list_dicom, indir, list_chosen
                    )

                    if pixels.size < 100000:
                        test_words = generate_random_words(
                            random.randint(1, 1), 5)
                    elif size[index_size] > 3:
                        test_words = generate_random_words(
                            random.randint(1, 5), 5)
                    else:
                        test_words = generate_random_words(
                            random.randint(1, 10), 10)
                    test_words_keep = test_words
                    (pixels, words_array, test_words) = add_words_on_image(
                        pixels, test_words, size[index_size],
                        font=(os.path.join(path_fonts, font[index_font])), blur=blur[index_blur]
                    )

                    img = Image.fromarray(pixels)
                    output_png = "{}/{}_{}_{}_{}_before".format(
                        outdir,
                        os.path.basename(dicom),
                        size[index_size],
                        os.path.basename(font[index_font]),
                        blur[index_blur]
                    )
                    dicom2png.narray2png(pixels, output_png)
                    # img.save(outdir + '/' + os.path.basename(dicom) + ".png")

                    ocr_data = get_text_areas(pixels)
                    if ocr_data is None:
                        ocr_data = []
                    else:
                        deleted_words.extend([data[1] for data in ocr_data])
                    (ocr_recognized_words, total_words) = compare_ocr_data_and_reality(
                        test_words, words_array, ocr_data
                    )

                    # Test numbers :
                    sum_ocr_recognized_words += ocr_recognized_words
                    sum_total_words += total_words

                    # Calculate test model values
                    (tp, tn, fn) = calculate_test_values(
                        total_words, ocr_recognized_words, tp, tn, fn
                    )

                    output_path = os.path.join(
                        outdir, os.path.basename(file_path))
                    output_ds = os.path.join(
                        outdir, f'{os.path.basename(file_path)}.txt')
                    output_summary = os.path.join(outdir, 'summary.log')

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
                            os.path.basename(font[index_font]),
                            blur[index_blur]
                        ),
                        file_path, ds, ocr_data, test_words_keep, total_words)

                    summary += "\n" + file_path + "\n↪parameters : F = " \
                        + str(os.path.basename(font[index_font])) + " | B = " \
                        + str(blur[index_blur]) + " | S = " + \
                        str(size[index_size])
                    nb_images_tested += 1

                    pixels = hide_text(pixels, ocr_data, color_value='white')
                    # narray2dicom(pixels, ds, output_path)

                    output_png = "{}/{}_{}_{}_{}_after".format(
                        outdir,
                        os.path.basename(dicom),
                        size[index_size],
                        os.path.basename(font[index_font]),
                        blur[index_blur]
                    )
                    dicom2png.narray2png(pixels, output_png)

    duration = int((time.time() - start_time) / 60)
    with open(os.path.join(outdir, 'test_summary.log'), 'w', encoding='utf8') as f:
        f.write(f"Duration of exexcution: {duration}.\n" + summary)
    with open(os.path.join(outdir, 'deleted_words'), 'w', encoding='utf8') as f:
        list(map(lambda x: f.write(f'{x}\n'), deleted_words))


def prep_test_df2dicom(indir, tmp_dir):
    """
    Calls the tests evaluating the performances of df2dicom() in the 
    df2dicom_verification.py module located in the library deidcm
    """
    indir = utils.get_home('data', 'input', 'dcm4chee', 'dicom', '')[
        :-1] if indir is None else indir
    tmp_dir = utils.get_home('data', 'transform', 'dcm4chee', 'test_dicom', '')[
        :-1] if tmp_dir is None else tmp_dir
    df2dicom_test(indir, tmp_dir)


def prep_test_deid_attributes(indir, outdir):
    run_test_deid_attributes(indir, outdir)
