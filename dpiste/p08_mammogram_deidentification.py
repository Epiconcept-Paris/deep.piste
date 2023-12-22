"""
Mammogram Deidentifier (Images + Attributes)
"""

from datetime import datetime

import os
import json
import time
import glob
import hashlib
import pandas as pd

from kskit import dicom2png
from kskit.dicom.df2dicom import (df2dicom, df2hdh)
from kskit.dicom.get_dicom import get_dicom
from kskit.dicom.deid_mammogram import (
    gen_dicom_uid,
    load_authorized_words,
    deidentify_attributes,
    hide_text,
    get_text_areas,
    p08_005_update_summary
)
from kskit.dicom.utils import log

from dpiste import utils
from dpiste.dal.screening import depistage_pseudo
from dpiste.p06_mammogram_extraction import (
    get_acr5,
    get_positive_studies_only,
    filter_depistage_pseudo,
    keep_only_studies_with_images,
    calculate_l1_l2_result,
)
from dpiste.p11_hdh_data_transfer import (
    renew_sftp,
    init_distant_root,
    init_distant_files,
    get_progress,
    wait4hdh,
    send2hdh_df,
    create_study_dirs,
    send2hdh_study_content,
    cleandir,
    WORKER_FOLDER,
    read_progress_files,
    get_all_modifications,
    update_progress,
    get_folder_content
)
from dpiste.p11_hdh_encryption import p11_001_generate_transfer_keys


def deid_mammogram(indir=None, outdir=None):
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

    if indir is None:
        indir = utils.get_home('data', 'input', 'dcm4chee', 'dicom', '')
    if outdir is None:
        outdir = utils.get_home('data', 'output', 'hdh', 'dicom-png', '')

    output_summary = outdir + "/summary.log"

    pathname = indir + "/**/*"
    list_dicom = glob.glob(pathname, recursive=True)

    list_dicom = sorted(list_dicom)
    for file in list_dicom:
        if os.path.isfile(file):
            nb_files = len(list_dicom)
            input_path = file

            if outdir.endswith("/"):
                output_path = outdir + os.path.basename(file)
                output_ds = outdir + os.path.basename(file) + ".txt"
                output_summary = outdir + "summary.log"
            else:
                output_path = outdir + '/' + os.path.basename(file)
                output_ds = outdir + "/" + os.path.basename(file) + ".txt"
                output_summary = outdir + "/summary.log"

            (pixels, ds) = dicom2png.dicom2narray(input_path)

            ocr_data = get_text_areas(pixels)

            if len(ocr_data):
                print("\n___________A text area has been detected : " +
                      input_path + "___________\n")
                pixels = hide_text(pixels, ocr_data)

            else:
                print("\nNo text area detected\n")
                print(input_path, "=>", output_path)

            dicom2png.narray2png(pixels, output_path)
            print(nb_images_processed, "/", nb_files, "DICOM(s) de-identified")

            with open(output_ds, 'a', encoding="utf-8") as f:
                file_path = indir + file
                text = input_path + '\n' + "Words recognized : " + \
                    str(ocr_data) + '\n'
                f.write(text)

            summary = p08_005_update_summary(summary, file_path, ocr_data)
            nb_images_processed += 1

    time_taken = time.time() - start_time
    with open(output_summary, 'w', encoding="utf-8") as f:
        f.write(
            str(round(time_taken/60)) + " minutes taken to de-identify all images.\n" +
            summary
        )


def deid_mammogram2(org_root, indir=None, outdir=None):
    """
    Anonymize a complete directory of DICOM.
    @param
    indir = the initial directory of DICOM to de-identify
    outdir = the final director of DICOM which have been de-identied
    """

    if indir is None:
        indir = utils.get_home('data', 'input', 'dcm4chee', 'dicom', '')
    if outdir is None:
        outdir = utils.get_home('data', 'output', 'hdh', '')

    df = deidentify_attributes(indir, outdir, org_root)
    df.to_csv(os.path.join(outdir, 'meta.csv'))
    df2dicom(df, outdir, do_image_deidentification=True)


def deidentify_mammograms_hdh(indir: str, outdir: str, org_root: str, exclude_images: bool = False):
    """Call attributes and mammogram deidentification before transfering data"""
    df = deidentify_attributes(indir, outdir, org_root, erase_outdir=False)
    log('Deidentifying mammograms...')
    df2hdh(df, outdir, exclude_images)


def p08_001_export_hdh(sftph: str, sftpu: str, batch_size: int, sftp_limit: float,
                       tmp_fol: str, id_worker: int, nb_worker: int, org_root: str,
                       reset_sftp=False, screening_filter=False,
                       exclude_images=False, only_positive=False) -> None:
    """Gets, deidentifies and sends mammograms to the HDH sftp"""
    indir, outdir = init_local_files(tmp_fol, id_worker)
    worker_indir = os.path.join(indir, str(id_worker))
    worker_outdir = os.path.join(outdir, str(id_worker))

    log(f'{utils.sftp_get_available_size()} GB available in SFTP')
    c, sftp = renew_sftp(sftph, sftpu)
    if reset_sftp:
        log('-r option enabled : erasing all information on SFTP', logtype=1)
        utils.sftp_reset(sftp)
    df = depistage_pseudo()
    df = filter_screening(df) if screening_filter else df

    if only_positive:
        df_with_study_id = filter_depistage_pseudo(df)
        df_with_study_id_and_lecture_results = calculate_l1_l2_result(
            df_with_study_id)
        df_with_positive_only = get_positive_studies_only(
            df_with_study_id_and_lecture_results)
        df = keep_only_studies_with_images(df_with_positive_only)

    studies = build_studies(
        df, date_mammo_only=True) if screening_filter else build_studies(df)
    total2upload = len(studies.index)
    deid_studies = deidentify_study_id(studies.copy(), org_root)

    init_distant_root(sftp)
    progress = get_progress(outdir, studies, id_worker, sftp)
    uploaded = progress
    if progress != 0:
        wait4hdh(sftph, sftpu, sftp, c, batch_size, sftp_limit)
    else:
        utils.reset_local_files(worker_indir)
        if id_worker == 0:
            init_distant_files(sftp, id_worker)
            send2hdh_df(deid_studies, worker_outdir, 'studies.csv', sftp)
            send2hdh_df(df.drop(columns='DICOM_Studies'),
                        worker_outdir, 'screening.csv', sftp)

    c, sftp = renew_sftp(sftph, sftpu, sftp, c)
    if id_worker != 0:
        init_distant_files(sftp, id_worker)

    count = 0
    log(f'Words ignored by OCR: {load_authorized_words()}')
    for index in studies.index:
        study_id = studies['study_id'][index]
        study_hash = int(hashlib.sha512(
            study_id.encode('utf-8')).hexdigest(), 16)
        if abs(study_hash) % nb_worker == id_worker:
            count += 1
        if progress >= count or \
                abs(study_hash) % nb_worker != id_worker:
            continue

        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        id_random = studies['id_random'][index]
        deid_study_id = gen_dicom_uid(id_random, study_id, org_root)

        study_dir = os.path.join(worker_outdir, deid_study_id)
        worker_studies = os.listdir(os.path.join(worker_outdir))
        if deid_study_id not in worker_studies:
            os.mkdir(study_dir)
        create_study_dirs(deid_study_id, id_worker, sftp)

        log(f'Getting study n°{study_id}')
        get_dicom(key=study_id, dest=worker_indir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

        deidentify_mammograms_hdh(
            worker_indir, study_dir, org_root, exclude_images=exclude_images)
        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        send2hdh_study_content(study_dir, id_worker, sftp)
        uploaded = 1 if uploaded == 0 else uploaded
        update_progress(uploaded, total2upload, outdir, id_worker, sftp)

        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        utils.cleandir(worker_indir)
        utils.cleandir(worker_outdir)
        update_progress(uploaded, total2upload, outdir, id_worker, sftp)
        wait4hdh(sftph, sftpu, sftp, c, batch_size, sftp_limit)
        uploaded += 1
    sftp.close()
    c.close()
    log('All done!')


def p08_001_export_local(tmp_fol: str, id_worker: int, nb_worker: int, org_root: str, screening_filter=False) -> None:
    """Gets, deidentifies and writes mammograms locally"""
    indir, outdir = init_local_files(tmp_fol, id_worker)
    worker_indir = os.path.join(indir, str(id_worker))
    worker_outdir = os.path.join(outdir, str(id_worker))
    final_dir = os.path.join(tmp_fol, "final")
    if not os.path.exists(final_dir):
        os.mkdir(final_dir)
    else:
        cleandir(final_dir)

    screening_df = depistage_pseudo()
    screening_df = filter_screening(
        screening_df) if screening_filter else screening_df
    studies = build_studies(
        screening_df, date_mammo_only=True) if screening_filter else build_studies(screening_df)
    deid_studies = deidentify_study_id(studies.copy(), org_root)

    utils.reset_local_files(worker_indir)
    if id_worker == 0:
        deid_studies.to_csv(os.path.join(final_dir, 'studies.csv'))
        screening_df.drop(columns='DICOM_Studies').to_csv(
            os.path.join(final_dir, 'screening.csv'))

    progress = 0
    count = 0
    log(f'Words ignored by OCR: {load_authorized_words()}')
    for index in studies.index:
        study_id = studies['study_id'][index]
        study_hash = int(hashlib.sha512(
            study_id.encode('utf-8')).hexdigest(), 16)
        if abs(study_hash) % nb_worker == id_worker:
            count += 1
        if progress >= count or \
                abs(study_hash) % nb_worker != id_worker:
            continue

        id_random = studies['id_random'][index]
        deid_study_id = gen_dicom_uid(id_random, study_id, org_root)

        study_dir = os.path.join(worker_outdir, deid_study_id)
        worker_studies = os.listdir(os.path.join(worker_outdir))
        if deid_study_id not in worker_studies:
            os.mkdir(study_dir)

        log(f'Getting study n°{study_id}')
        get_dicom(key=study_id, dest=worker_indir, server='10.1.2.9', port=11112,
                  title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

        deidentify_mammograms_hdh(worker_indir, study_dir, org_root)
        move_all_files_to_final(study_dir, final_dir)
        utils.cleandir(worker_indir)
        utils.cleandir(worker_outdir)
    log('All done!')


def move_all_files_to_final(study_dir: str, final_dir: str) -> None:
    """For local export: move output files to final subdir"""
    final_study_dir = os.path.join(final_dir, os.path.basename(study_dir))
    os.mkdir(final_study_dir)
    for file in os.listdir(study_dir):
        os.rename(os.path.join(study_dir, file),
                  os.path.join(final_study_dir, file))


def p08_002_status_hdh(sftph: str, sftpu: str, nb_worker: int) -> None:
    """Display HDH SFTP metrics"""
    tmp_folder = utils.get_home('reports', '')
    progress_folder = os.path.join(tmp_folder, 'progress')
    c, sftp = renew_sftp(sftph, sftpu)

    if os.path.exists(progress_folder):
        utils.cleandir(progress_folder, deldir=True)

    get_folder_content(sftp, WORKER_FOLDER, tmp_folder, None, verbose=False)
    status = {'progress': None, 'last_modifications': None}
    status['progress'] = read_progress_files(progress_folder)
    status['last_modifications'] = get_all_modifications(sftp)

    for i in range(nb_worker):
        worker_name = f'worker-{i}'
        last_mod = status['last_modifications'][worker_name]
        progress = status['progress'][worker_name]
        # total_to_upload = status['progress']['total-to-upload']
        log(f'WORKER {i}: Last mod. {last_mod} | Number of studies uploaded: {progress}')
    total_uploaded = status['progress']['total-uploaded']
    log(f'Total number of studies uploaded: {total_uploaded}')
    sftp.close()
    c.close()
    utils.cleandir(progress_folder, deldir=True)


def p08_003_reset_sftp(sftph: str, sftpu: str) -> None:
    """Erase all files inside SFTP"""
    c, sftp = renew_sftp(sftph, sftpu)
    utils.sftp_reset(sftp)
    c.close()
    sftp.close()


def init_local_files(tmp_fol: str, id_worker: int):
    """Prepare the local temporary folder used to store before sending to SFTP"""
    indir = os.path.join(tmp_fol, 'sensitive')
    outdir = os.path.join(tmp_fol, '.tmp')
    for folder in [indir, outdir]:
        if not os.path.exists(folder):
            os.mkdir(folder)
        else:
            cleandir(folder)

    # Creates workers' folders
    # sensitive/id_worker folders
    worker_indir = os.path.join(indir, str(id_worker))
    if not os.path.exists(worker_indir):
        os.mkdir(worker_indir)

    # .tmp/id_worker folders
    worker_folder = os.path.join(outdir, str(id_worker))
    if not os.path.isdir(worker_folder):
        os.mkdir(worker_folder)

    p11_001_generate_transfer_keys(os.environ['DP_KEY_PASSPHRASE'])
    return indir, outdir


def deidentify_study_id(studies: pd.DataFrame, org_root: str) -> pd.DataFrame:
    """Deidentifies the column study_id of the DataFrame df"""
    for index in studies.index:
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        studies.at[index, 'study_id'] = gen_dicom_uid(
            id_random, study_id, org_root)
    studies = studies.rename(columns={'study_id': 'study_pseudo_id'})
    return studies


def build_studies(df: pd.DataFrame, date_mammo_only=False) -> pd.DataFrame:
    """
    Extracts study information from a dataframe and returns a new dataframe
    with 3 columns [id_random, date, study_id].

    Args:
    - df: A pandas dataframe containing studies information.
    - date_mammo_only: A boolean that indicates whether to filter only studies
    whose date is equal to the date in the 'Date_Mammo' column.

    Returns:
    - A new pandas dataframe with 3 columns [id_random, date, study_id].
    """
    df = df[pd.notna(df['DICOM_Studies'])]
    data = []
    for index in df.index:
        dates = json.loads(df['DICOM_Studies'][index])
        if not date_mammo_only:
            # Method n°1: Keep all studies
            for date in dates:
                for study_id in dates[date][0]:
                    row = []
                    row.extend([df['id_random'][index], date, study_id])
                data.append(row)
        else:
            # Method n°2: Keep only studies whose date is equal to the date in the 'Date_Mammo' col (~1month)
            for key, value in dates.items():
                for study_id in value[0]:
                    row = []
                    key_date = datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                    key_date = key_date.replace(hour=0, minute=0, second=0)
                    date_mammo = df["Date_Mammo"][index]
                    month_delta = (date_mammo.year - key_date.year) * \
                        12 + date_mammo.month - key_date.month
                    if abs(month_delta) <= 1:
                        row.extend(
                            [int(df['id_random'][index]), key, study_id])
                data.append(row)
    studies = pd.DataFrame(data, columns=['id_random', 'date', 'study_id'])
    studies = studies.drop_duplicates()
    studies = studies.sort_values(by=['study_id'], ignore_index=True)
    return studies.dropna()


def filter_screening(screening_df: pd.DataFrame) -> pd.DataFrame:
    """Premade filter for testing purposes only"""
    print('Filtering dataframe...')
    df_without_na = screening_df[screening_df['DICOM_Studies'].notnull()]
    df_acr5 = get_acr5(df_without_na)
    df_acr5_age = df_acr5[df_acr5['Age_Mammo'] == 69]
    return df_acr5_age
