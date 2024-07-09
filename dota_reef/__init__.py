#!/usr/bin/env python3

import os
import sys
import hashlib
import argparse
from functools import partial
from tempfile import TemporaryDirectory

import vpk

def content_md5(path):
    with open(path, 'rb') as f:
        md5 = hashlib.md5()
        for data in iter(partial(f.read, 4096), b''):
            md5.update(data)
    return md5.hexdigest()

def run(maps_path):
    dota_vpk_path = os.path.join(maps_path, 'dota.vpk')
    cur_md5 = content_md5(dota_vpk_path)
    dota_vpk_md5_path = os.path.join(maps_path, 'dota.vpk.md5')
    if os.path.exists(dota_vpk_md5_path):
        with open(dota_vpk_md5_path, 'rb') as f:
            prev_md5 = f.read().decode('utf-8')
        if cur_md5 == prev_md5:
            print('hash matches, no need to update')
            return
    dota_vpk = vpk.open(dota_vpk_path)
    dota_reef_vpk = vpk.open(os.path.join(maps_path, 'dota_reef.vpk'))
    outdir = TemporaryDirectory()
    outdirpath = outdir.name
    def save(path, vpkfile):
        # fixme, just assuming we are on windows, must be a better way?
        path = path.replace('/', '\\')
        outpath = os.path.join(outdirpath, path)
        dirpath, filename = os.path.split(path)
        if dirpath:
            os.makedirs(os.path.join(outdirpath, dirpath), exist_ok=True)
        vpkfile.save(outpath)
    # take maps/dota/* and a (renamed) dota_reef.vmap_c from dota_reef.vpk
    # and everything else from dota.vpk
    map_from_reef = {}
    for path, metadata in dota_reef_vpk.read_index_iter():
        if path.startswith('maps/dota/'):
            map_from_reef[path] = path
        elif path == 'maps/dota_reef.vmap_c':
            map_from_reef[path] = 'maps/dota.vmap_c'
    would_overwrite = set(map_from_reef.values())
    for path, metadata in dota_vpk.read_index_iter():
        if path in would_overwrite:
            continue
        with dota_vpk.get_vpkfile_instance(path, metadata) as vpkfile:
            save(path, vpkfile)
    for path, metadata in dota_reef_vpk.read_index_iter():
        if path not in map_from_reef:
            continue
        with dota_reef_vpk.get_vpkfile_instance(path, metadata) as vpkfile:
            save(map_from_reef[path], vpkfile)
    new_vpk = vpk.new(outdirpath, path_enc='utf-8')
    new_vpk.version = 2
    new_vpk.save(dota_vpk_path)
    with open(dota_vpk_md5_path, 'wb') as f:
        f.write(content_md5(dota_vpk_path).encode('utf-8'))
    outdir.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Steal the Reef')
    parser.add_argument('maps', type=str, help='Path to dota2 maps dir (containing dota.vpk)', nargs='?',
                        default=r"D:\SteamLibrary\steamapps\common\dota 2 beta\game\dota\maps")
    args = parser.parse_args()
    run(args.maps)

if __name__ == '__main__':
    main()
