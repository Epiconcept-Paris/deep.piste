import os
import json
import time
import pytz
import pandas as pd
from paramiko.sftp_client import SFTPClient
from fabric import Connection
from datetime import datetime, timezone

from dpiste.p11_hdh_encryption import p11_encrypt_hdh, p11_decrypt_hdh
from dpiste.utils import sftp_cleandir, sftp_get_available_size, cleandir
from kskit.dicom.utils import log

ROOT_PATH = 'dpiste'
WORKER_FOLDER = os.path.join(ROOT_PATH, 'progress')
TMP_DIRNAME = os.path.join(ROOT_PATH, '.tmp')
OK_DIRNAME = os.path.join(ROOT_PATH, 'screening')
TIMEZONE = pytz.timezone("Europe/Paris")

def init_distant_root(sftp: SFTPClient) -> None:
    """Initializes dpiste/ and dpiste/progress"""
    sftp.mkdir(ROOT_PATH) if ROOT_PATH not in sftp.listdir(path='.') else None 
    sftp.mkdir(WORKER_FOLDER) if 'progress' not in sftp.listdir(path='dpiste') else None  


def get_progress(outdir: str, studies: pd.DataFrame, 
        id_worker: int, sftp: SFTPClient) -> int:
    """Retrieves progress.json and reads progress value if exists"""
    filename = f'worker{id_worker}_progress.json'
    log(f'Getting previous progress from {filename}')
    if filename not in sftp.listdir(path=WORKER_FOLDER):
        log('Nothing found: Starting from scratch')
        return 0
    else:
        local_path = os.path.join(outdir, filename)
        sftp.get(os.path.join(WORKER_FOLDER, filename), local_path)
        with open(local_path, 'r') as f:
            progress = json.loads(f.read())
        uploaded = progress['uploaded']
        study_id = studies['study_id'][uploaded]
        log([
            f'Found {filename}',
            f'Resuming to last uploaded study: {uploaded}th study n°{study_id}'
        ])
        return uploaded


def update_progress(uploaded: int, total: int, outdir: str, 
    id_worker: int, sftp: SFTPClient) -> None:
    """Updates progress.json with the current uploaded/total value"""
    filename = f'worker{id_worker}_progress.json'
    log(f'Updating {filename}')
    local_path = os.path.join(outdir, filename)
    remote_path = os.path.join(WORKER_FOLDER, os.path.basename(local_path))
    log(f'{uploaded}/{total} studies uploaded')
    d = {'uploaded': uploaded, 'total': total}
    with open(local_path, 'w') as f:
        f.write(json.dumps(d))
    sftp.put(local_path, remote_path)
    return


def renew_sftp(sftph: str, sftpu: str, sftp: SFTPClient=None, 
    c: Connection=None, trydelay=1200) -> Connection:
    """Closes given instances of SFTP and Connection and returns new ones"""
    sftp.close() if sftp is not None else None
    c.close() if c is not None else None
    c = Connection(host=sftph, user=sftpu, port=22, connect_timeout=200)
    sftp, display_warning_success = None, False
    sftp = connect_to_sftp(c, trydelay=trydelay)
    return c, sftp


def connect_to_sftp(c: Connection, trydelay) -> SFTPClient:
    sftp, display_warning_success = None, False
    while sftp is None:
        try:
            sftp = c.sftp()
            if display_warning_success:
                log('Successfully connected to SFTP!') 
        except Exception as e:
            log([
                'Unable to connect to the SFTP server at the moment.',
                f'Full Trace: {e}'
                f'Will try again in {trydelay} seconds...'
                ],
                logtype=2
            )
            time.sleep(trydelay)
            sftp = None
            display_warning_success = True
    return sftp


def wait4hdh(sftph: str, sftpu: str, sftp: SFTPClient, c: Connection, 
    batch_size: int, sftp_limit: float) -> None:
    """Calls wait_until if server_capacity >= 95% OR f_amount >= batch_size """
    c, sftp = renew_sftp(sftph, sftpu, sftp, c)
    folders_amount = len(sftp.listdir(path=OK_DIRNAME))
    sftp.close()
    sftp_available_size = sftp_get_available_size()
    c, sftp = renew_sftp(sftph, sftpu, None, c)
    log(f'{sftp_available_size} GB available in SFTP')
    if folders_amount >= batch_size and batch_size != 0 or sftp_available_size < sftp_limit:
        wait_until(sftph, sftpu, sftp, c, batch_size,
        sftp_limit, sftp_available_size, folders_amount)
    else:
        sftp.close()
        c.close()
    return


def wait_until(sftph: str, sftpu: str, sftp: SFTPClient, c: Connection, 
    batch_size: int, sftp_limit: float, sftp_available_size: float, folders_amount: int):
    """Waits until sftp_available_size >= sftp_limit GB and f_amount < batch_size"""
    display_max_msg = True
    while folders_amount >= batch_size and batch_size != 0 or sftp_available_size < sftp_limit:
        if display_max_msg:
            log('Waiting for files to be deleted in HDH SFTP', logtype=1)
        sftp.close()
        sftp_available_size = sftp_get_available_size()
        c, sftp = renew_sftp(sftph, sftpu, None, c)
        logtype = 1 if sftp_available_size < sftp_limit else 0
        if display_max_msg:
            log(f'{sftp_available_size} GB available in SFTP', logtype=logtype)
            display_max_msg = False
        sftp.close()
        c.close()
        time.sleep(60*30)
        c, sftp = renew_sftp(sftph, sftpu)
        folders_amount = len(sftp.listdir(path=OK_DIRNAME))
    sftp.close()
    c.close()
    return


def send2hdh_df(df: pd.DataFrame, outdir: str, filename: str,
                sftp: SFTPClient) -> None:
    """Transfers the DataFrame to the SFTP folder"""
    log(f'Transferring {filename} to HDH SFTP')
    filepath = os.path.join(outdir, filename)
    encrypted_filepath = os.path.join(outdir, f'{filename}.gpg')
    df.to_csv(filepath)
    p11_encrypt_hdh(filepath, encrypted_filepath, rmold=True)
    sftp_fpath = os.path.join(OK_DIRNAME, os.path.basename(encrypted_filepath))
    print(sftp_fpath)
    sftp.put(encrypted_filepath, sftp_fpath)
    return


def send2hdh_study_content(study_dir: str, id_worker: int, sftp: SFTPClient) -> None:
    """Transfers study_dir files into the corresponding dir in the SFTP"""
    log(f'Transferring study data to HDH SFTP...')
    
    for file in os.listdir(study_dir):
        unencrypted_filepath = os.path.join(study_dir, file)
        encrypted_filepath = os.path.join(study_dir, f'{file}.gpg')
        p11_encrypt_hdh(unencrypted_filepath, encrypted_filepath, rmold=True)
        parent_dir = os.path.basename(study_dir)
        sftp_path = os.path.join(TMP_DIRNAME, str(id_worker), parent_dir, f'{file}.gpg')
        sftp.put(encrypted_filepath, sftp_path)
    tmp2ok(os.path.basename(study_dir), id_worker, sftp)
    sftp_cleandir(
        sftp, os.path.join(TMP_DIRNAME, str(id_worker), os.path.basename(study_dir)), deldir=True)
    return


def tmp2ok(study_dir: str, id_worker: int, sftp: SFTPClient) -> None:
    """Moves SFTP tmp/study_dir to ok/study_dir"""
    tmp_study_path = os.path.join(TMP_DIRNAME, str(id_worker), study_dir)
    ok_study_path = os.path.join(OK_DIRNAME, str(id_worker), study_dir)
    for f in sftp.listdir_attr(tmp_study_path):
      done = False
      tries = 2
      while tries >= 0 and not done:
        if tries < 2:
          log(f'Retrying moving file to {ok_study_path}. Tries remaining: {tries}')
        try:
          sftp.mkdir(os.path.join(OK_DIRNAME, f'{id_worker}'))
        except:
          pass
        try:
          sftp.mkdir(ok_study_path)
        except:
          pass
        try:
            tmp_filepath = os.path.join(tmp_study_path, f.filename)
            ok_filepath = os.path.join(ok_study_path, f.filename)
            sftp.rename(tmp_filepath, ok_filepath)
            done = True
        except:
          pass
        tries = tries - 1
    return


def init_distant_files(sftp: SFTPClient, id_worker: int) -> None:
    """Creates or Cleans dpiste/ tmp/, studies/ & workers directories on the SFTP server"""
    root_files = sftp.listdir(path=ROOT_PATH)
    for f in [TMP_DIRNAME, OK_DIRNAME]:
        if os.path.basename(f) not in root_files:
            sftp.mkdir(f)

    worker_indir = os.path.join(TMP_DIRNAME, str(id_worker))
    worker_outdir = os.path.join(OK_DIRNAME, str(id_worker))

    worker_indir_files = sftp.listdir(path=TMP_DIRNAME)
    worker_outdir_files = sftp.listdir(path=OK_DIRNAME)
    if str(id_worker) not in worker_indir_files:
        sftp.mkdir(worker_indir)
    else:
        sftp_cleandir(sftp, worker_indir)
    
    if str(id_worker) not in worker_outdir_files:
        sftp.mkdir(worker_outdir)
    return


def create_study_dirs(deid_study_id: str, id_worker: int, sftp: SFTPClient) -> None:
    """Creates study directories in .tmp/id_worker/"""
    tmp_worker_path = os.path.join(TMP_DIRNAME, str(id_worker))
    if deid_study_id not in sftp.listdir(path=tmp_worker_path):
        path = os.path.join(tmp_worker_path, deid_study_id)
        sftp.mkdir(path)
    return


def get_all_studies(sftp: SFTPClient, destination: str, id_worker: int = 0, specific_file: str = None) -> None:
    """Gets all studies from specific worker and put them in destination folder"""
    worker_studies = os.path.join(OK_DIRNAME, str(id_worker))
    for study in sftp.listdir(path=worker_studies):
        study_remote_path = os.path.join(worker_studies, study)
        study_local_path = destination
        get_folder_content(sftp, study_remote_path, study_local_path, specific_file)
    return


def read_progress_files(tmp_folder) -> dict:
    progress = {}
    total = 0
    for file in os.listdir(tmp_folder):
        file_path = os.path.join(tmp_folder, file)
        with open(file_path, 'r') as f:
            content = json.loads(f.read())
            for i in range(4):
                if str(i) in file:
                    worker_name = f'worker-{i}'
        progress[worker_name] = content['uploaded']
        total += content['uploaded']
    progress['total-uploaded'] = total
    progress['total-to-upload'] = content['total']
    return progress


def get_all_modifications(sftp) -> dict:
    modifications = {}
    for attr in sftp.listdir_attr(path=WORKER_FOLDER):
        for i in range(4):
            if str(i) in attr.filename:
                worker_name = f'worker-{i}'
        date = datetime.fromtimestamp(attr.st_mtime, tz=TIMEZONE)
        modifications[worker_name] = datetime.strftime(date, '%d-%m-%Y %H:%M:%S')
    return modifications


def get_folder_content(sftp: SFTPClient, folder: str, destination: str, specific_file: str, verbose=False) -> None:
    """Gets a whole folder from SFTP and put it in destination folder"""
    folder_remote_path = folder
    folder_local_path = os.path.join(destination, os.path.basename(folder))
    os.mkdir(folder_local_path)
    for file in sftp.listdir(path=folder_remote_path):
        if specific_file == None or specific_file in file:
            file_remote_path = os.path.join(folder_remote_path, file)
            file_local_path = os.path.join(folder_local_path, file)
            log(f"Getting {file_local_path}...") if verbose else None
            sftp.get(file_remote_path, file_local_path)
    return


def decrypt_whole_folder(folder: str) -> None:
    for file in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, file)):
            decrypt_whole_folder(os.path.join(folder, file))
        else:
            local_enc_path = os.path.join(folder, file)
            unenc_local_path, extension = os.path.splitext(local_enc_path)
            p11_decrypt_hdh(local_enc_path, unenc_local_path)
            os.remove(local_enc_path)
    return 
