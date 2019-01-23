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

os.mkdir('/tmp/mnt')
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            print(host["name"]+'.local')
            if os.path.exists(fsRoot+'/'+host["name"]+'_new'):
                os.system('rmdir -rf ' + fsRoot+'/'+host["name"] + '_new')
            os.mkdir(fsRoot+'/'+host["name"]+'_new')
            os.chdir(fsRoot+'/'+host["name"]+'_new')
            tar = tarfile.open(fsRoot + '/' + sysType["fsImage"])
            tar.extractall()
            tar.close()
            # Fix up /etc/hostname
            file = open(fsRoot+'/'+host["name"]+'_new'+'/etc/hostname','w')
            file.write(host)
            file.close()
            # Fix up /etc/hosts
            fileIn = open(fsRoot+'/'+host["name"]+'_new'+'/etc/hosts')
            fileOut = open(fsRoot+'/'+host["name"]+'_new'+'/etc/hosts', 'w')
            for s in fileIn:
                fileOut.write(s.replace('raspberrypi', host["name"]))
            fileIn.close()
            fileOut.close()
            # Create the sd card image if doesn't exist
            imageName = fsRoot+'/'+host["name"]+'.img'
            if not os.path.isfile(imageName):
                os.system('cp ' + fsRoot + '/' + sysType["bootImage"] + ' ' + imageName)
                os.system('mount -o loop,offset=4194304 -t msdos ' + imageName + ' /tmp/mnt')
                file = open('/tmp/mnt/cmdline.txt', 'w')
                file.write('dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/' + host["name"] + ',vers=3 rw ip=dhcp elevator=deadline rootwait')
                file.close()
                os.system('umount /tmp/mnt')
            #If there is a current filesystem for host then rename to hostname_old
            # deleting previous one if it exist 
            if os.path.exists(fsRoot+'/'+host["name"] + '_old'):
                os.system('rmdir -rf ' + fsRoot+'/'+host["name"] + '_old')
            if os.path.exists(fsRoot+'/'+host["name"]):
                os.system('mv ' + fsRoot+'/'+host["name"] + ' ' + fsRoot+'/'+host["name"]+'_old')
            #move newly created filesystem in place
            os.system('mv ' + fsRoot+'/'+host["name"]+'_new_ ' + fsRoot+'/'+host["name"])
# remove the mount point
os.rmdir('/tmp/mnt')
