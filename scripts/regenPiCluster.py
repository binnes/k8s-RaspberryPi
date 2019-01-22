#!/usr/bin/python

import json
import os
import tarfile
import paramiko

from pprint import pprint


def rebootHost(hostname):
    key = paramiko.RSAKey.from_private_key_file(os.environ['HOME']+'/.ssh/id_rsa')
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect( hostname = hostname, username = 'pi', pkey = key )
    stdin , stdout, stderr = c.exec_command('sudo reboot -n')
    c.close()


with open('scripts/config.json') as f:
    config = json.load(f)

fsRoot = config["testMachines"]["NFSrootPath"] + '/sysRoots'

pprint(config)

for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            print(host["name"]+'.local')
            os.mkdir(fsRoot+'/'+host["name"]+'_new')
            os.chdir(fsRoot+'/'+host["name"]+'_new')
            tar = tarfile.open(fsRoot + '/' + sysType["fsImage"])
            tar.extractall()
            tar.close()


#sudo mount -o loop,offset=4194304 -t msdos /mnt/ssd/sysRoots/raspbian_boot.img /mnt/img