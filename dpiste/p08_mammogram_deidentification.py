import os
import json
import time

from dpiste import utils
from dpiste.dal.screening import depistage_pseudo
from dpiste.p11_hdh_data_transfer import *
from dpiste.p11_hdh_encryption import p11_001_generate_transfer_keys

from kskit import dicom2png
from kskit.dicom.df2dicom import (df2dicom, df2hdh)
from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.deid_mammogram import *
from kskit.dicom.utils import (write_all_ds, log)


def deid_mammogram(indir = None, outdir = None):
    """
    Anonymize a complete directory of DICOM.

    @param

    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """
    start_time = time.time()
    nb_images_processed = 1
    summary = """\n\n\n
Here is a summary of the DICOMs that have been de-identified.\n\n\n
    """

    pkg_dir, this_filename = os.path.split(__file__)
    PATH_ATTRIBUTES_TO_KEEP = os.path.join(pkg_dir, "data/resources/deid_ref/attributes_to_keep.json")
    
    if indir == None:
        indir = utils.get_home('data', 'input', 'dcm4chee','dicom','')
    if outdir == None:
        outdir = utils.get_home('data','output','hdh', 'dicom-png', '')
    
    output_summary = outdir + "/summary.log"

    pathname = indir + "/**/*"
    list_dicom = glob.glob(pathname, recursive=True)

    list_dicom = sorted(list_dicom)
    print(f"hola!! {indir}")
    print(list_dicom)
    for file in list_dicom:
      if os.path.isfile(file):
        nb_files = len(list_dicom)
        input_path = file
        
        if outdir.endswith("/"):
            output_path = outdir  + os.path.basename(file)
            output_ds = outdir + os.path.basename(file) + ".txt"
            output_summary = outdir + "summary.log"
        else:
            output_path = outdir  + '/' + os.path.basename(file)
            output_ds = outdir + "/" + os.path.basename(file) + ".txt"
            output_summary = outdir + "/summary.log"

        (pixels, ds) = dicom2png.dicom2narray(input_path)

        ocr_data = get_text_areas(pixels)

        if len(ocr_data):
            print("\n___________A text area has been detected : " + input_path + "___________\n")
            pixels = hide_text(pixels, ocr_data)
            
        else:
            print("\nNo text area detected\n")
            print(input_path, "=>", output_path)
        
        dicom2png.narray2png(pixels, output_path)
        print(nb_images_processed, "/", nb_files, "DICOM(s) de-identified")

        with open(output_ds,'a') as f:
            file_path = indir + file
            text = input_path + '\n' + "Words recognized : " + \
               str(ocr_data) + '\n'
            f.write(text)

        summary = p08_005_update_summary(summary, file_path, ocr_data)
        nb_images_processed += 1

    
    time_taken = time.time() - start_time
    with open(output_summary, 'w') as f:
        f.write(
          str(round(time_taken/60)) + " minutes taken to de-identify all images.\n" + \
            summary
        )


def deid_mammogram2(indir = None, outdir = None):
    """
    Anonymize a complete directory of DICOM.
    @param
    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """
    
    if indir == None:
        indir = utils.get_home('data', 'input', 'dcm4chee', 'dicom', '')
    if outdir == None:
        outdir = utils.get_home('data', 'output','hdh', '')

    df = deidentify_attributes(indir, outdir)
    df.to_csv(os.path.join(outdir, 'meta.csv'))
    df2dicom(df, outdir, do_image_deidentification=True)


def deidentify_mammograms_hdh(indir: str, outdir: str, sftp: SFTPClient):
    df = deidentify_attributes(indir, outdir, erase_outdir=False)
    log('Deidentifying mammograms...')
    df2hdh(df, outdir)
    return


def p08_001_export_hdh(sftph: str, sftpu: str, batch_size: int,
    server_capacity: int, tmp_fol: str, id_worker: int, nb_worker: int) -> None:
    """Gets, deidentifies and sends mammograms to the HDH sftp"""
    indir, outdir = set_localenv(tmp_fol, nb_worker)
    log(f"Server capacity: {server_capacity} GB")
    server_capacity = server_capacity * 10**9
    c, sftp = renew_sftp(sftph, sftpu)
    # utils.sftp_reset(sftp)
    # exit()
    df = depistage_pseudo()
    studies = build_studies(df)
    total2upload = len(studies.index)
    deid_studies = deidentify_study_id(studies.copy())
    
    progress = get_progress(outdir, studies, id_worker, sftp)
    if progress != 0:
        wait4hdh(sftph, sftpu, sftp, c, batch_size, server_capacity)
    else:
        send2hdh_df(deid_studies, outdir, 'studies.csv', sftp)
        send2hdh_df(df.drop(columns='DICOM_Studies'), outdir, 'df.csv', sftp)

    c, sftp = renew_sftp(sftph, sftpu, sftp, c)
    create_tmp_and_ok_folders(sftp, indir, id_worker, nb_worker)

    for uploaded, index in enumerate(studies.index):
        if progress >= uploaded or abs(hash(studies['study_id'][index])) % nb_worker != id_worker:
            continue

        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        deid_study_id = gen_dicom_uid(id_random, study_id)

        worker_dir =  os.path.join(outdir, str(id_worker))
        study_dir = os.path.join(worker_dir, deid_study_id)
        worker_studies = os.listdir(os.path.join(worker_dir))
        os.mkdir(study_dir) if deid_study_id not in worker_studies else None
        create_study_dirs(deid_study_id, id_worker, sftp)

        log(f'Getting study n°{study_id}')
        get_dicom(key=study_id, dest=indir, server='10.1.2.9', port=11112,
            title='DCM4CHEE', retrieveLevel='STUDY', silent=True)
        deidentify_mammograms_hdh(indir, study_dir, sftp)
        send2hdh_study_content(study_dir, id_worker, sftp)
        update_progress(uploaded, total2upload, outdir, id_worker, sftp)

        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        utils.cleandir([indir, worker_dir])
        wait4hdh(sftph, sftpu, sftp, c, batch_size, server_capacity)
    return


def set_localenv(tmp_fol: str, nb_worker: int):
    """Prepare the local temporary folder used to store before sending to SFTP"""
    indir = os.path.join(tmp_fol, 'sensitive')
    outdir = os.path.join(tmp_fol, '.tmp')
    for folder in [indir, outdir]:
        os.mkdir(folder) if not os.path.isdir(folder) else None
    for id_worker in range(nb_worker):
        worker_folder = os.path.join(outdir, f'{id_worker}')
        os.mkdir(worker_folder) if not os.path.isdir(worker_folder) else None
    p11_001_generate_transfer_keys(os.environ['ENCKEY'])
    return indir, outdir


def deidentify_study_id(studies: pd.DataFrame) -> pd.DataFrame:
    """Deidentifies the column study_id of the DataFrame df"""
    for index in studies.index:
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        studies.at[index, 'study_id'] = gen_dicom_uid(id_random, study_id)
    return studies


def build_studies(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a DataFrame made of 3 columns [id_random, date, study_id]"""
    df = df[pd.notna(df['DICOM_Studies'])]
    data = []
    for index in df.index:
        dates = json.loads(df['DICOM_Studies'][index])
        for date in dates:
            for study_id in dates[date][0]:
                row = []
                row.extend([df['id_random'][index], date, study_id])
            data.append(row)
    studies = pd.DataFrame(data, columns = ['id_random', 'date', 'study_id'])
    return studies.drop_duplicates()
