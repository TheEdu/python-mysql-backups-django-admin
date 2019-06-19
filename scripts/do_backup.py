import sys
import os
import time
import subprocess
import re
import paramiko
import django
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
import configparser
import argparse

import warnings
warnings.filterwarnings(action='ignore', module='.*paramiko.*')

sys.path.append(os.path.abspath('../'))
import mysite.settings as app_settings
settings.configure(INSTALLED_APPS=app_settings.INSTALLED_APPS, DATABASES=app_settings.DATABASES)
django.setup()

from backups.models import Task, Log

__CONF = configparser.ConfigParser()
__CONF.read('config.ini')


def send_mail_sistemas(subject, message):
    from_addr = __CONF['MAIL']['ADDRESS']
    to_addrs = "sistemas@zarate.gob.ar"
    password = __CONF['MAIL']['PASSWORD']
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addrs
    server = smtplib.SMTP(__CONF['MAIL']['SMTP_SERVER'], __CONF['MAIL']['SMTP_PORT'])
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addrs, msg.as_string())
    server.quit()


def do_mysql_backup(mysqldump_name, data_source):
    "Do the backup into temporary directory"

    # local temp names
    sql_tmp_path = __CONF['TEMPORAL']['BACKUP_PATH'] + mysqldump_name
    gzip_tmp_path = sql_tmp_path + ".gz"

    # backup command
    backup_cmd = ["mysqldump",
                  "-u", data_source.user,
                  "-p" + data_source.password,  # Inline password
                  "-h", data_source.host.ip, "-P", str(data_source.port),
                  "--single-transaction", "--quick", "--compress",
                  data_source.identificador_origen]

    # compress command
    compress_cmd = ["gzip", "-9", sql_tmp_path]

    # backup command execution, and store in /file/path/dabatase_(time).sql
    try:
        with open(sql_tmp_path, 'w') as out:
            subprocess.check_call(backup_cmd, stdout=out)
    except Exception as e:
        if (os.path.exists(sql_tmp_path)):
            os.remove(sql_tmp_path)
        raise Exception('An error occurred (do_mysql_backup->backup_cmd) : %s: %s' % (e.__class__, e))

    # compress command execution, and store in /file/path/dabatase_time.sql.gz
    try:
        subprocess.check_call(compress_cmd)
    except Exception as e:
        if (os.path.exists(gzip_tmp_path)):
            os.remove(gzip_tmp_path)
        raise Exception('An error occurred (do_mysql_backup->compress_cmd) : %s: %s' % (e.__class__, e))

    # After the success of the two commands above, return the gzip_tmp_path
    return gzip_tmp_path


def do_mysql_backup_2(mysqldump_name, data_source):
    "Do the backup into temporary directory (INSECURE WAY because the shell=True)"

    # local temp names
    gzip_tmp_path = __CONF['TEMPORAL']['BACKUP_PATH'] + mysqldump_name + ".gz"

    # backup command part
    backup_cmd = ("mysqldump" + " -u " + data_source.user + " -p" + data_source.password
                                + " -h " + data_source.host.ip + " -P " + str(data_source.port)
                                + " --single-transaction --quick --compress " + data_source.identificador_origen)

    # gzip command part
    gzip_cmd = "gzip -c > " + gzip_tmp_path

    # complete command (with pipe)
    complete_cmd = backup_cmd + " | " + gzip_cmd
    # print("command ==> " + complete_cmd)

    try:
        subprocess.check_call(complete_cmd, shell=True)
    except Exception as e:
        if (os.path.exists(gzip_tmp_path)):
            os.remove(gzip_tmp_path)
        raise Exception('An error occurred (do_mysql_backup_2) : %s: %s' % (e.__class__, e))

    # After a success command execution, return the gzip_tmp_path
    return gzip_tmp_path


def move_mysqldump_to_storage(gzip_tmp_path, mysqldump_name, data_storage):
    "Move the local mysqlump.sql.gz to remote data_storage"
    sftp = None
    ssh = None
    try:
        # Open SSH y SFTP
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(data_storage.host.ip, data_storage.host.ssh_port, data_storage.host.user, data_storage.host.password)
        sftp = ssh.open_sftp()  # Using the SSH client, create a SFTP client.
        sftp.sshclient = ssh  # Keep a reference to the SSH client in the SFTP client to prevent connection from being closed.

        # Get database_name and remote file path
        match = re.search("(.*)_(.*).sql$", mysqldump_name)
        database_name = match.group(1)
        filepath_compress = data_storage.boveda_path + mysqldump_name + '.gz'

        # Move to the remote directory, adn delete from the tmp Directory
        sftp.put(gzip_tmp_path, filepath_compress)
        if (os.path.exists(gzip_tmp_path)):
            os.remove(gzip_tmp_path)

        files_list = sftp.listdir(path=data_storage.boveda_path)

        # List all remote backups for the given task
        backups_list = []
        for entry in files_list:
            match_string = database_name + "_(.*).sql.gz$"
            match = re.search(match_string, entry)
            if (match):
                b = {
                    'name': entry,
                    'timestamp': int(match.group(1))
                }
                backups_list.append(b)

        # sort backlist by timestamp
        backups_list.sort(key=lambda b: b['timestamp'])

        # Delete old backups
        while(len(backups_list) > task.max_quantity):
            backup_to_delete = backups_list.pop(0)  # first element
            backup_to_delete_path = data_storage.boveda_path + backup_to_delete['name']
            sftp.remove(backup_to_delete_path)

    except Exception as e:
        raise Exception('An error occurred (move_mysqldump_to_storage) : %s: %s' % (e.__class__, e))
    finally:
        if sftp is not None:
            sftp.close()
        if ssh is not None:
            ssh.close()


def do_backup(task):
    "Do the backup of the given task (Django Object)"
    # Data Source (Database) and Data Storage (Storage)
    data_source = task.data_source
    data_storage = task.data_storage
    timestamp = str(int(time.time()))
    mysqldump_name = data_source.identificador_origen + '_' + timestamp + ".sql"

    # gzip_tmp_path = do_mysql_backup(mysqldump_name, data_source)
    gzip_tmp_path = do_mysql_backup_2(mysqldump_name, data_source)
    move_mysqldump_to_storage(gzip_tmp_path, mysqldump_name, data_storage)
    return gzip_tmp_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Genera el Backup de la tarea dada. ej: python do_backup.py -taskID 1')

    parser.add_argument('-taskID',
                        help='El ID de la tarea requerida',
                        required=True,
                        type=int,)

    task_id = parser.parse_args().taskID

    backup_name = ''
    description = ''
    task = None

    try:
        task = Task.objects.get(pk=task_id)
    except Exception as e:
        print(e)  # Imprimir Error por consola (DEBUG propourse)
        send_mail_sistemas("Error de base de datos (Imposible obtener la tarea)", str(e))
        exit()

    retry = task.max_retry
    while(retry >= 0):
        try:
            result = do_backup(task)
            backup_name = task.data_source.identificador_origen
            Log.objects.create(exit_code=0,
                               backup_name=backup_name,
                               description=description,
                               task=task)

            print(result)
            break  # Exit the loop
        except Exception as e:
            if (retry == 0):
                print(e)  # Imprimir Error por consola (DEBUG propourse)
                retry = -1  # Exit on the next loop

                subject = "Backup - MuniZar Script " + time.strftime('%Y-%m-%d-%I:%M')
                message = "El Backup '" + backup_name + "' ha fallado\n ERROR ==>  " + str(e)
                send_mail_sistemas(subject, message)

                Log.objects.create(exit_code=1,
                                   backup_name=backup_name,
                                   description=e,
                                   task=task)
            else:
                retry = retry - 1
