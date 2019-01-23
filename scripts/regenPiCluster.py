#!/usr/bin/python

import json
import os
import tarfile
import shutil
import subprocess
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
# Create a mount point for the boot images
if not os.path.exists('/tmp/mnt'):
    os.mkdir('/tmp/mnt')

for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            print(host["name"]+'.local')
            if os.path.exists(fsRoot+'/'+host["name"]+'_new'):
                shutil.rmtree(fsRoot+'/'+host["name"] + '_new')
            os.mkdir(fsRoot+'/'+host["name"]+'_new')
            os.chdir(fsRoot+'/'+host["name"]+'_new')
            tar = tarfile.open(fsRoot + '/' + sysType["fsImage"])
            tar.extractall()
            tar.close()
            # Fix up /etc/hostname
            file = open(fsRoot+'/'+host["name"]+'_new'+'/etc/hostname','w')
            file.write(host["name"])
            file.close()
            # Fix up /etc/hosts
            os.system("sed -i 's/raspberrypi/"+host["name"]+"/g' " +fsRoot+"/"+host["name"]+"_new"+"/etc/hosts")
            # Create the sd card image if doesn't exist
            imageName = fsRoot+'/'+host["name"]+'.img'
            if not os.path.isfile(imageName):
                os.system('cp ' + fsRoot + '/' + sysType["bootImage"] + ' ' + imageName+'.gz')
                os.system('gzip -d ' + imageName+'.gz')
                os.system('kpartx -a ' + imageName)
                p = subprocess.Popen('ls /dev/mapper | grep loop', stdout=subprocess.PIPE, shell=True)
                (loopDev, err) = p.communicate()
                p_status = p.wait()
                print('mapper device is ' + loopDev)
                os.system('mount -o loop -t msdos /dev/mapper/' + loopDev + ' /tmp/mnt')
                file = open('/tmp/mnt/cmdline.txt', 'w')
                file.write('dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/' + host["name"] + ',vers=3 rw ip=dhcp elevator=deadline rootwait')
                file.close()
                os.system('umount /tmp/mnt')
                os.system('kpartx -d ' + imageName)
            #If there is a current filesystem for host then rename to hostname_old
            # deleting previous one if it exist 
            if os.path.exists(fsRoot+'/'+host["name"] + '_old'):
                shutil.rmtree(fsRoot+'/'+host["name"] + '_old')
            if os.path.exists(fsRoot+'/'+host["name"]):
                os.system('mv ' + fsRoot+'/'+host["name"] + ' ' + fsRoot+'/'+host["name"]+'_old')
            #move newly created filesystem in place
            os.system('mv ' + fsRoot+'/'+host["name"]+'_new ' + fsRoot+'/'+host["name"])

# remove the mount point
os.rmdir('/tmp/mnt')
