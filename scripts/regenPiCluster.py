#!/usr/bin/python

import json
import os
import tarfile
import subprocess
import paramiko

def rebootHost(hostname):
    print('Rebooting '+hostname)
    key = paramiko.RSAKey.from_private_key_file(os.environ['HOME']+'/.ssh/id_rsa')
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect( hostname, username = 'pi', pkey = key )
    stdin , stdout, stderr = c.exec_command('sudo reboot -n')
    c.close()


with open('scripts/config.json') as f:
    config = json.load(f)

fsRoot = config["testMachines"]["NFSrootPath"] + '/sysRoots'

# Create a mount point for the boot images
if not os.path.exists('/tmp/mnt'):
    os.mkdir('/tmp/mnt')

for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            dirName = fsRoot+'/'+host["name"]
            existingDirName = dirName + '_old'
            newDirName = dirName + '_new'
            print(host["name"]+'.local')
            if os.path.exists(newDirName):
                os.system('rm -rf ' + newDirName)
            os.mkdir(newDirName)
            os.chdir(newDirName)
            tar = tarfile.open(fsRoot + '/' + sysType["fsImage"])
            tar.extractall()
            tar.close()
            # Fix up /etc/hostname
            file = open(newDirName+'/etc/hostname','w')
            file.write(host["name"])
            file.close()
            # Fix up /etc/hosts
            os.system("sed -i 's/raspberrypi/"+host["name"]+"/g' " +newDirName+"/etc/hosts")
            # Create the sd card image if doesn't exist
            imageName = dirName+'.img'
            if not os.path.isfile(imageName):
                os.system('cp ' + fsRoot + '/' + sysType["bootImage"] + ' ' + imageName+'.gz')
                os.system('gzip -d ' + imageName+'.gz')
                os.system('mount -o loop,offset=4194304 -t msdos ' + imageName + ' /tmp/mnt')
                file = open('/tmp/mnt/cmdline.txt', 'w')
                file.write('dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/' + host["name"] + ',vers=3 rw ip=dhcp elevator=deadline rootwait')
                file.close()
                os.system('umount /tmp/mnt')
            #If there is a current filesystem for host then rename to hostname_old
            # deleting previous one if it exist 
            if os.path.exists(existingDirName):
                os.system('rm -rf ' + existingDirName)
            if os.path.exists(dirName):
                os.system('mv ' + dirName + ' ' + existingDirName)
            #move newly created filesystem in place
            os.system('mv ' + newDirName + ' ' + dirName)
            rebootHost(host["IP"])

# remove the mount point
os.rmdir('/tmp/mnt')
