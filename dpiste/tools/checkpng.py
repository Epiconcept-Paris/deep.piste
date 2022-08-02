#!/usr/bin/env python3

import os
import pydicom
import numpy as np
from PIL import Image
from tqdm import tqdm
from dpiste.utils import recursive_count_files
from dpiste.utils import get_home

def checkfiles(path: str, tmpdir: str) -> None:
    mean, nb_files = 0, 0
    total_files = recursive_count_files(path)
    pbar = tqdm(total=total_files)
    for root, dirs, files in os.walk(path):
        for file in files:
            pixels = get_nparray(os.path.join(root, file))
            saved_pixels = write_and_get_png(pixels, tmpdir)
            mean += compare_arrays(pixels, saved_pixels)
            nb_files += 1
            pbar.update(1)
    print(f'Mean: {mean / nb_files * 100}')
    return


def get_nparray(dcmpath: str) -> np.ndarray:
    ds = pydicom.dcmread(dcmpath)
    return ds.pixel_array


def write_and_get_png(pixels: np.ndarray, tmpdir: str) -> np.ndarray:
    saved_img_path = os.path.join(tmpdir, 'check.png')
    Image.fromarray(pixels).save(saved_img_path)
    im = Image.open(saved_img_path)
    return np.asarray(im)


def compare_arrays(original: np.ndarray, saved: np.ndarray) -> None:
    return 1 if np.array_equal(original, saved) else 0


if __name__ == '__main__':
    checkfiles(
        get_home("data/input/dcm4chee/dicom_negative"),
        get_home("data/input/dcm4chee/checkfiles")
    )
