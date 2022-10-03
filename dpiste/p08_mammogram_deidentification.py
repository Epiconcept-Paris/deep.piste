import os
import shutil
import json
import time

from dpiste import utils
from dpiste.dal.screening import depistage_pseudo
from dpiste.p06_mammogram_extraction import get_acr5
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


def p08_001_export_hdh(sftph: str, sftpu: str, batch_size: int, sftp_limit: float,
    tmp_fol: str, id_worker: int, nb_worker: int, reset_sftp=False, screening_filter=False, test=False) -> None:
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
    studies = build_studies(df, date_mammo_only=True) if screening_filter else build_studies(df)
    total2upload = len(studies.index)
    deid_studies = deidentify_study_id(studies.copy())
    
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
            send2hdh_df(df.drop(columns='DICOM_Studies'), worker_outdir, 'screening.csv', sftp)

    c, sftp = renew_sftp(sftph, sftpu, sftp, c)
    if id_worker != 0:
        init_distant_files(sftp, id_worker)

    count = 0
    log(f'Words ignored by OCR: {load_authorized_words()}')
    for index in studies.index:
        study_id = studies['study_id'][index]
        study_hash = int(hashlib.sha512(study_id.encode('utf-8')).hexdigest(), 16)
        if abs(study_hash) % nb_worker == id_worker:
            count += 1
        if progress >= count or \
            abs(study_hash) % nb_worker != id_worker:
            continue

        c, sftp = renew_sftp(sftph, sftpu, sftp, c)
        id_random = studies['id_random'][index]
        deid_study_id = gen_dicom_uid(id_random, study_id)

        study_dir = os.path.join(worker_outdir, deid_study_id)
        worker_studies = os.listdir(os.path.join(worker_outdir))
        os.mkdir(study_dir) if deid_study_id not in worker_studies else None
        create_study_dirs(deid_study_id, id_worker, sftp)

        log(f'Getting study n°{study_id}')
        get_dicom(key=study_id, dest=worker_indir, server='10.1.2.9', port=11112,
            title='DCM4CHEE', retrieveLevel='STUDY', silent=True)

        deidentify_mammograms_hdh(worker_indir, study_dir, sftp)
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
    return


def p08_002_status_hdh(sftph: str, sftpu: str, nb_worker: int) -> None:
    tmp_folder = utils.get_home('reports', '')
    progress_folder = os.path.join(tmp_folder, 'progress')
    c, sftp = renew_sftp(sftph, sftpu)
    utils.cleandir(progress_folder, deldir=True) if os.path.exists(progress_folder) else None
    get_folder_content(sftp, WORKER_FOLDER, tmp_folder, None, verbose=False)
    status = {'progress': None, 'last_modifications': None}
    status['progress'] = read_progress_files(progress_folder)
    status['last_modifications'] = get_all_modifications(sftp)
    
    for i in range(nb_worker):
        worker_name = f'worker-{i}'
        last_mod = status['last_modifications'][worker_name]
        progress = status['progress'][worker_name]
        total_to_upload = status['progress']['total-to-upload']
        log(f'WORKER {i}: Last mod. {last_mod} | Number of studies uploaded: {progress}')
    total_uploaded = status['progress']['total-uploaded']
    log(f'Total number of studies uploaded: {total_uploaded}')
    sftp.close()
    c.close()
    utils.cleandir(progress_folder, deldir=True)
    return


def p08_003_reset_sftp(sftph: str, sftpu: str) -> None:
    c, sftp = renew_sftp(sftph, sftpu)
    utils.sftp_reset(sftp)
    c.close()
    sftp.close()


def init_local_files(tmp_fol: str, id_worker: int):
    """Prepare the local temporary folder used to store before sending to SFTP"""
    indir = os.path.join(tmp_fol, 'sensitive')
    outdir = os.path.join(tmp_fol, '.tmp')
    for folder in [indir, outdir]:
        os.mkdir(folder) if not os.path.exists(folder) else cleandir(folder)
    
    # Creates workers' folders
    # sensitive/id_worker folders
    worker_indir = os.path.join(indir, str(id_worker))
    os.mkdir(worker_indir) if not os.path.exists(worker_indir) else None
    
    # .tmp/id_worker folders
    worker_folder = os.path.join(outdir, str(id_worker))
    os.mkdir(worker_folder) if not os.path.isdir(worker_folder) else None

    p11_001_generate_transfer_keys(os.environ['DP_KEY_PASSPHRASE'])
    return indir, outdir


def deidentify_study_id(studies: pd.DataFrame) -> pd.DataFrame:
    """Deidentifies the column study_id of the DataFrame df"""
    for index in studies.index:
        study_id = studies['study_id'][index]
        id_random = studies['id_random'][index]
        studies.at[index, 'study_id'] = gen_dicom_uid(id_random, study_id)
    studies = studies.rename(columns={'study_id': 'study_pseudo_id'})
    return studies


def build_studies(df: pd.DataFrame, date_mammo_only=False) -> pd.DataFrame:
    """Returns a DataFrame made of 3 columns [id_random, date, study_id]"""
    df = df[pd.notna(df['DICOM_Studies'])]
    #df = df[df['BDI_Echographie'] == False]    # Removes echography from studies list
    data = []
    for index in df.index:
        dates = json.loads(df['DICOM_Studies'][index])
        if not date_mammo_only:
            # Normal loop 
            for date in dates:
                for study_id in dates[date][0]:
                    row = []
                    row.extend([df['id_random'][index], date, study_id])
                data.append(row)
        else:
            # Integration Test loop
            for k, v in dates.items():
                for study_id in v[0]:
                    row = []
                    key_date = datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
                    key_date = key_date.replace(hour=0, minute=0, second=0)
                    if key_date in list(map(lambda d: datetime.strptime(str(d)[0:10], '%Y-%m-%d'), df['Date_Mammo'].values)):
                        row.extend([df['id_random'][index], k, study_id])
                data.append(row)
    studies = pd.DataFrame(data, columns = ['id_random', 'date', 'study_id'])
    studies = studies.drop_duplicates()
    studies = studies.sort_values(by=['study_id'])
    return studies.dropna()


def filter_screening(df: pd.DataFrame) -> pd.DataFrame:
    print('Filtering dataframe...')
    df_without_na = df[df['DICOM_Studies'].notnull()]
    df_acr5 = get_acr5(df_without_na)
    df_acr5_age = df_acr5[df_acr5['Age_Mammo'] == 69]
    return df_acr5_age

