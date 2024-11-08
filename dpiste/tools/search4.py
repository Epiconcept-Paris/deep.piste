#!/usr/bin/env python3

import os
import pydicom

from tqdm import tqdm

from deidcm.dicom.utils import log

from dpiste.dal.screening import depistage_pseudo
from dpiste.p08_mammogram_deidentification import build_studies
from dpiste.utils import cleandir
from dpiste.utils import get_home
from dpiste.dicom.get_dicom import get_dicom

CODING_SCHEME = {
    'R-10224': 'ml',
    'R-10226': 'mlo',
    'R-10228': 'lm',
    'R-10230': 'lmo',
    'R-10242': 'cc',
    'R-10244': 'fb',
    'R-102D0': 'sio',
    'R-40AAA': 'iso',
    'R-1022A': 'xccl',
    'R-1024B': 'xccm',
    'G-8310': '?',
}

MLO = 'R-10226'
CC = 'R-10242'

PATIENT_ID = 0x00100020
STUDY_DATE = 0x00080020


def search4ccmlo(indir: str, samples: int):
    log('Getting depistage_pseudo...')
    df = depistage_pseudo()
    log('Building studies...')
    studies = build_studies(df)
    ccmlo, total = 0, 0
    nbmam = len(studies.index)
    for imam, index in enumerate(studies.index):
        study_id = studies['study_id'][index]
        get_dicom(key=study_id, dest=indir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

        if isccmlo(indir):
            ccmlo += 1
        else:
            nb_files = len(os.listdir(indir))
            log(f'Not OK: {study_id} | Nb mammograms: {nb_files}')
        total += 1
        log(f'{ccmlo}/{total} mammograms where lcc, rcc, rmlo, lmlo are there')
        log(f'REMAINING: {nbmam-imam}')
        cleandir(indir)
        if total - samples == 0:
            break


def isccmlo(dirpath: str):
    """
    Return true if 4 images with the following respective types are found: 
    RCC, LCC, RMLO or LMLO in a study.
    """
    tags = {'rcc': 0, 'lcc': 0, 'rmlo': 0, 'lmlo': 0}
    for file in os.listdir(dirpath):
        ds = pydicom.dcmread(os.path.join(dirpath, file))
        try:
            code_value = ds[0x00540220][0][0x00080100].value
            img_laterality = ds[0x00200062].value.upper()
        except KeyError:
            continue
        ccmlo = ''
        if code_value == MLO:
            ccmlo = 'rmlo' if img_laterality == 'R' else 'lmlo'
        elif code_value == CC:
            ccmlo = 'rcc' if img_laterality == 'R' else 'lcc'
        else:
            continue
        tags[ccmlo] += 1

    def checkf(x): return True if x >= 1 else False
    res = all(map(checkf, tags.values()))
    for k, v in tags.items():
        if v < 1:
            log(f'Not present: {k.upper()}')
    return res


def isccmlo_view_position(dirpath: str):
    """
    Return true if 4 images with the following respective types are found: 
    RCC, LCC, RMLO or LMLO in a study.
    """
    tags = {'rcc': 0, 'lcc': 0, 'rmlo': 0, 'lmlo': 0}
    for file in os.listdir(dirpath):
        ds = pydicom.dcmread(os.path.join(dirpath, file))
        try:
            code_value = ds[0x00185101].value.upper()
            img_laterality = ds[0x00200062].value.upper()
        except KeyError:
            continue
        ccmlo = ''
        if code_value == "MLO":
            ccmlo = 'rmlo' if img_laterality == 'R' else 'lmlo'
        elif code_value == "CC":
            ccmlo = 'rcc' if img_laterality == 'R' else 'lcc'
        else:
            continue
        tags[ccmlo] += 1

    def checkf(x): return True if x >= 1 else False
    res = all(map(checkf, tags.values()))
    for k, v in tags.items():
        if v < 1:
            log(f'Not present: {k.upper()}')
    return res


def search_view_position(dirpath: str, view_position: bool = False) -> None:
    num = 0
    den = 0
    for root, dirs, files in os.walk(dirpath):
        for dir in dirs:
            if view_position:
                num += 1 if isccmlo_view_position(
                    os.path.join(root, dir)) else 0
            else:
                num += 1 if isccmlo(os.path.join(root, dir)) else 0
            den += 1
    print(f"{num}/{den} ccmlo")
    return


def get_detailed_viewcodes(indir: str, samples: int) -> None:
    log('Getting depistage_pseudo...')
    df = depistage_pseudo()
    log('Building studies...')
    studies = build_studies(df)
    ccmlo, total = 0, 0
    nbmam = len(studies.index)
    frequency = 0
    for imam, index in enumerate(studies.index):
        study_id = studies['study_id'][index]
        get_dicom(key=study_id, dest=indir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

        if countccmlo(indir, study_id):
            frequency += 1
        cleandir(indir)
        total += 1
        if total - samples == 0:
            break
    log(f'Frequency of overpopulated studies : {samples}')
    log(f'Number of overpopulated studies {frequency}')
    log(f'Frequency of overpopulated studies : {frequency/samples*100}%')


def countccmlo(dirpath: str, study_id: str) -> bool:
    """Search for RCC, LCC, RMLO or LMLO in a study"""
    tags = {'rcc': 0, 'lcc': 0, 'rmlo': 0, 'lmlo': 0}
    for file in os.listdir(dirpath):
        ds = pydicom.dcmread(os.path.join(dirpath, file))
        try:
            code_value = ds[0x00540220][0][0x00080100].value
            img_laterality = ds[0x00200062].value.upper()
        except KeyError:
            continue
        ccmlo = ''
        if code_value == 'R-10226':
            ccmlo = 'rmlo' if img_laterality == 'R' else 'lmlo'
        elif code_value == 'R-10242':
            ccmlo = 'rcc' if img_laterality == 'R' else 'lcc'
        else:
            continue
        tags[ccmlo] += 1
    log(f'Study {study_id} <=> {tags}')
    for v in tags.values():
        if v > 1:
            log(f'Too much values for study {study_id}')
            return True
    return False


def get_broken_studies(ref_file: str, broken_stud_dir: str):
    """Read each line of the ref_file, find Study UID and retrieve the study"""
    with open(ref_file, 'r') as f:
        content = f.readlines()
    study_ids = list(map(lambda x: x.split(' ')[4], content))
    for study_id in tqdm(study_ids):
        studir = os.path.join(broken_stud_dir, study_id)
        os.mkdir(studir)
        get_dicom(key=study_id, dest=studir, server='10.1.2.9',
                  port=11112, title='DCM4CHEE', retrieveLevel='STUDY', silent=True)


def see_broken_studies_details(broken_stud_dir: str):
    """Get all DICOM files and print ViewCodeSequence and IMGLat"""
    invalid_studies_filenumber = 0
    valid_studies_filenumber = 0
    us_mammograms = 0
    us_study = 0
    for root, dirs, files in os.walk(broken_stud_dir):
        for d in dirs:
            nb_files = len(os.listdir(os.path.join(root, d)))
            if nb_files < 4:
                invalid_studies_filenumber += 1
        one_per_study = True
        for file in files:
            ds = pydicom.dcmread(os.path.join(root, file))
            try:
                code_value = ds[0x00540220][0][0x00080100].value
                img_laterality = ds[0x00200062].value.upper()
                ccmlo = ''
            except KeyError:
                code_value, img_laterality = 'N/A', 'N/A'
                ccmlo = 'N/A'
            if ds[0x00080060].value == 'US':
                us_mammograms += 1
                us_study += 1 if one_per_study else 0
            if code_value == 'R-10226':
                ccmlo = 'rmlo' if img_laterality == 'R' else 'lmlo'
            elif code_value == 'R-10242':
                ccmlo = 'rcc' if img_laterality == 'R' else 'lcc'
            elif code_value != 'N/A':
                ccmlo = CODING_SCHEME[code_value]
            try:
                print(
                    f'{ds[0x00080018].value} => {ccmlo}|{code_value}|{img_laterality}|{ds[0x00080060].value}|{ds[0x00181400].value}|{ds[0x00185101]}')
            except KeyError:
                print(
                    f'{ds[0x00080018].value} => {ccmlo}|{code_value}|{img_laterality}|{ds[0x00080060].value}')
            one_per_study = False
        if len(files) >= 4:
            valid_studies_filenumber += 1
    print('\nMain invalidation causes:')
    print(f'Less than 4 mammograms: {invalid_studies_filenumber}')
    print(f'Other causes: {valid_studies_filenumber}')
    print('='*100)
    print(f'{us_mammograms} Ultrasound (= Echograph) found in {us_study} studies')


def find_all_studies_associated_with(patient_id: str = "4161741") -> set:
    test_path = "/space/Work/william2/deep.piste/home/data/input/dcm4chee/dicom_positive"
    associated_studies = set()
    for root, dirs, files in os.walk(test_path):
        for file in files:
            fullpath = os.path.join(root, file)
            ds = pydicom.dcmread(fullpath)
            if ds[PATIENT_ID].value == patient_id:
                study_directory = os.path.dirname(os.path.realpath(fullpath))
                print(f"date: {ds[STUDY_DATE].value}")
                print(ds[PATIENT_ID].value)
                print(isccmlo(study_directory))
                associated_studies.add(study_directory)
                break
    return associated_studies


if __name__ == '__main__':
    # search_view_position("/space/Work/william2/deep.piste/home/data/input/dcm4chee/dicom_positive")
    search_view_position(
        "/space/Work/william2/deep.piste/home/data/input/dcm4chee/dicom_positive", True)
    # search4ccmlo(get_home('data/input/dcm4chee/count'), 2000)
    # get_broken_studies(get_home('logs/69'), get_home('data/input/dcm4chee/broken'))
    see_broken_studies_details(get_home('data/input/dcm4chee/broken'))
    # get_detailed_viewcodes(get_home('data/input/dcm4chee/count'), 2000)
