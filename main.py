#!/usr/bin/env python3

import configparser
import os
import shutil
import subprocess
import sys
import tempfile


def handle_snapshot(path, target_dir):
    lo_path = subprocess.check_output(['sudo', 'losetup', '-P', '--find', '--show', path]).decode().strip()
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.check_call(['sudo', 'mount', lo_path + 'p1', temp_dir])
        recent_clips_dir = os.path.join(temp_dir, 'TeslaCam', 'RecentClips')
        if os.path.exists(recent_clips_dir):
            for entry in os.listdir(recent_clips_dir):
                if not entry.endswith('.mp4'):
                    continue

                date, ignored, name = entry.partition('_')
                target_path = os.path.join(target_dir, date, entry)
                source_path = os.path.join(recent_clips_dir, entry)
                if os.path.exists(target_path) and os.stat(target_path).st_size >= os.stat(source_path).st_size:
                    continue

                print('Copying ' + entry + '...')
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copyfile(source_path, target_path)
    finally:
        subprocess.check_call(['sudo', 'umount', temp_dir])
        os.rmdir(temp_dir)
        subprocess.check_call(['sudo', 'losetup', '-d', lo_path])


def process_dir(dir_path, target_dir):
    for entry in os.listdir(os.path.join(dir_path, 'snapshots')):
        snap_path = os.path.join(dir_path, 'snapshots', entry, 'snap.bin')
        handle_snapshot(snap_path, target_dir)


def main():
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))
    # Mount SMB share
    subprocess.check_call([
        'sudo', 'mount',
        '-t', 'cifs',
        '-o', 'username=%s,password=%s' % (parser.get('SMB', 'Username'), parser.get('SMB', 'Password')),
        '-o', 'user,rw,uid=%i' % os.getuid(),
        '//%s/%s' % (parser.get('SMB', 'Host'), parser.get('SMB', 'Share')),
        parser.get('Paths', 'TempMount')
    ])
    try:
        dest = os.path.join(parser.get('Paths', 'TempMount'), 'RecentClips')
        process_dir(parser.get('Paths', 'Source'), dest)
    finally:
        subprocess.call(['sudo', 'umount', parser.get('Paths', 'TempMount')])


if __name__ == '__main__':
    main()
