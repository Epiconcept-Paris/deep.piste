import os
import json
import time
import pandas as pd
from paramiko.sftp_client import SFTPClient
from fabric import Connection

from dpiste.p11_hdh_encryption import p11_encrypt_hdh
from dpiste.utils import sftp_cleandir, sftp_calculate_size, cleandir
from kskit.dicom.utils import log

TMP_DIRNAME, OK_DIRNAME = '.tmp', 'studies' 

def get_progress(outdir: str, studies: pd.DataFrame, sftp: SFTPClient) -> int:
    """Retrieves progress.json and reads progress value if exists"""
    log('Getting previous progress...')
    if 'progress.json' not in sftp.listdir(path='.'):
        log('Nothing found: Starting from scratch')
        return 0
    else:
        local_path = os.path.join(outdir, 'progress.json')
        sftp.get('progress.json', local_path)
        with open(local_path, 'r') as f:
            progress = json.loads(f.read())
        uploaded = progress['uploaded']
        study_id = studies['study_id'][uploaded]
        log([
            'Found progress.json',
            f'Resuming to last uploaded study: {uploaded}th study n°{study_id}'
        ])
        return uploaded


def update_progress(uploaded: int, total: int, outdir: str, 
    sftp: SFTPClient) -> None:
    """Updates progress.json with the current uploaded/total value"""
    log(f'Updating progress.json')
    local_path = os.path.join(outdir, 'progress.json')
    remote_path = os.path.basename(local_path)
    log(f'{uploaded}/{total} studies uploaded')
    d = {'uploaded': uploaded, 'total': total}
    with open(local_path, 'w') as f:
        f.write(json.dumps(d))
    sftp.put(local_path, remote_path)
    return


def renew_sftp(sftph: str, sftpu: str, sftp: SFTPClient=None, 
    c: Connection=None, trydelay=10) -> Connection:
    """Closes given instances of SFTP and Connection and returns new ones"""
    sftp.close() if sftp is not None else None
    c.close() if c is not None else None
    c = Connection(host=sftph, user=sftpu, port=22)
    sftp, display_warning_success = None, False
    while sftp is None:
        try:
            sftp = c.sftp()
            if display_warning_success:
                log('Successfully connected to SFTP!') 
        except Exception:
            log([
                'Unable to connect to the SFTP server at the moment.',
                f'Will try again in {trydelay} seconds...'
                ],
                logtype=2
            )
            time.sleep(trydelay)
            sftp = None
            display_warning_success = True
    return c, sftp


def wait4hdh(sftph: str, sftpu: str, sftp: SFTPClient, c: Connection, 
    batch_size: int, server_capacity: int) -> None:
    """Calls wait_until if server_capacity >= 95% OR f_amount >= batch_size """
    c, sftp = renew_sftp(sftph, sftpu, sftp, c)
    folders_amount = len(sftp.listdir(path=OK_DIRNAME))
    sftp_size = sftp_calculate_size(sftp)
    cap = f'{round(sftp_size*10**-9, 2)}/{round(server_capacity*10**-9, 2)}'
    per = int(sftp_size/server_capacity*100)
    log(f'{per}% of server capacity used: {cap} GB', logtype=0)
    if folders_amount >= batch_size or sftp_size/server_capacity >= 0.9:
        wait_until(sftph, sftpu, sftp, c, batch_size,
        server_capacity, folders_amount, sftp_size)
    else:
        sftp.close()
        c.close()
    return


def wait_until(sftph: str, sftpu: str, sftp: SFTPClient, c: Connection, 
    batch_size: int, server_capacity: int, folders_amount: int, sftp_size: float):
    """Waits until sftp_size < 90% serv_cap and f_amount < batch_size"""
    display_max_msg = True
    while folders_amount >= batch_size or sftp_size/server_capacity >= 0.9:
        if display_max_msg:
            log('Waiting for files to be deleted in HDH SFTP', logtype=1)
            cap = f'{round(sftp_size*10**-9, 2)}/{round(server_capacity*10**-9, 2)}'
            per = int(sftp_size/server_capacity*100)
            if sftp_size >= server_capacity:
                log(f'{per}% of server capacity used: {cap} GB', logtype=1)
            else:
                log(f'{per}% of server capacity used: {cap} GB', logtype=0)
            display_max_msg = False
        sftp.close()
        c.close()
        time.sleep(10)
        c, sftp = renew_sftp(sftph, sftpu)
        folders_amount = len(sftp.listdir(path=OK_DIRNAME))
        sftp_size = sftp_calculate_size(sftp)
    sftp.close()
    c.close()
    return


def send2hdh_df(df: pd.DataFrame, outdir: str, filename: str,
                sftp: SFTPClient) -> None:
    """Transfers the DataFrame to the SFTP folder"""
    log(f'Transferring {filename} to HDH SFTP')
    filepath = os.path.join(outdir, filename)
    encrypted_filepath = os.path.join(outdir, f'{filename}.bz2')
    df.to_csv(filepath)
    p11_encrypt_hdh(filepath, encrypted_filepath, rmold=True)
    sftp.put(encrypted_filepath, os.path.basename(encrypted_filepath))
    return


def send2hdh_study_content(study_dir: str, sftp: SFTPClient) -> None:
    """Transfers study_dir files into the corresponding dir in the SFTP"""
    log(f'Transferring study data to HDH SFTP...')
    
    for file in os.listdir(study_dir):
        unencrypted_filepath = os.path.join(study_dir, file)
        encrypted_filepath = os.path.join(study_dir, f'{file}.bz2')
        p11_encrypt_hdh(unencrypted_filepath, encrypted_filepath, rmold=True)
        parent_dir = os.path.basename(study_dir)
        sftp_path = os.path.join(TMP_DIRNAME, parent_dir, f'{file}.bz2')
        sftp.put(encrypted_filepath, sftp_path)
    tmp2ok(os.path.basename(study_dir), sftp)
    sftp_cleandir(
        sftp, os.path.join(TMP_DIRNAME, os.path.basename(study_dir)), deldir=True)
    return


def tmp2ok(study_dir: str, sftp: SFTPClient) -> None:
    """Moves SFTP tmp/study_dir to ok/study_dir"""
    tmp_study_path = os.path.join(TMP_DIRNAME, study_dir)
    ok_study_path = os.path.join(OK_DIRNAME, study_dir)
    for f in sftp.listdir_attr(tmp_study_path):
        tmp_filepath = os.path.join(tmp_study_path, f.filename)
        ok_filepath = os.path.join(ok_study_path, f.filename)
        sftp.rename(tmp_filepath, ok_filepath)
    return


def create_tmp_and_ok_folders(sftp: SFTPClient, outdir: str) -> None:
    """Creates tmp/ and ok/ directories at the root of the SFTP server"""
    root_files = sftp.listdir(path='.')
    for f in [TMP_DIRNAME, OK_DIRNAME]:
        if f not in root_files:
            sftp.mkdir(f)
        elif f == TMP_DIRNAME:
            sftp_cleandir(sftp, f)
            cleandir(outdir)
    return


def create_study_dirs(deid_study_id: str, sftp: SFTPClient) -> None:
    """Creates study directories in .tmp/ and ok/"""
    for d in [TMP_DIRNAME, OK_DIRNAME]:
        if deid_study_id not in sftp.listdir(path=d):
                sftp.mkdir(os.path.join(d, deid_study_id))
    return
