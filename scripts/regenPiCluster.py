#!/usr/bin/python

import json
import os
import string
import subprocess
import time
import socket
import tarfile

retCode = 0
with open('scripts/config.json') as f:
    config = json.load(f)

fsRoot = config["testMachines"]["NFSrootPath"] + '/sysRoots'

# Create a mount point for the boot images
if not os.path.exists('/tmp/mnt'):
    os.mkdir('/tmp/mnt')

def waitForReboot(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    time.sleep(60)
    while True:
        try:
            s.connect((host, 22))
            break
        except socket.error as e:
            time.sleep(1)
    # continue
    s.close()
    # let OS boot fully before continuing
    time.sleep(60)
    
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            dirName = fsRoot+'/'+host["name"]
            existingDirName = dirName + '_old'
            newDirName = dirName + '_new'
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
            # Fix up networking and configure static IP address
            file = open(newDirName + '/etc/dhcpcd.conf', "a+")
            file.write("interface eth0\n")
            file.write("static ip_address=%s/%s\n" % (host["IP"], config["testMachines"]["network"]["subnetBits"]))
            file.write("static routers=%s\n" % config["testMachines"]["network"]["routerIP"])
            file.write("static domain_name_servers=%s\n" % config["testMachines"]["network"]["nameservers"])
            file.close()
            # Create the sd card image if doesn't exist and reset boot command on SD card in host, finally fixup /etc/fstab
            cmdline = 'dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/{},vers=3 rw ip={}::{}:{}:{}:eth0:off elevator=deadline rootwait'.format(host["name"], host["IP"], config["testMachines"]["network"]["routerIP"], config["testMachines"]["network"]["netmask"], host["name"])
            os.system("""ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'echo -n "{}" | sudo tee /boot/cmdline.txt'""".format(host["IP"], cmdline)) 
            os.system("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'sudo sed -i '/ext4/d' /etc/fstab'".format(host["IP"]))
            imageName = dirName+'.img'
            if not os.path.isfile(imageName):
                os.system('cp ' + fsRoot + '/' + sysType["bootImage"] + ' ' + imageName+'.gz')
                os.system('gzip -d ' + imageName+'.gz')
                os.system('mount -o loop,offset=4194304 -t msdos ' + imageName + ' /tmp/mnt')
                file = open('/tmp/mnt/cmdline.txt', 'w')
                file.write(cmdline)
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
            os.system("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'sudo reboot -n'".format(host["IP"]))
            waitForReboot(host["IP"])
            #determine number of partitions on SD card
            partitions = subprocess.check_output("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} grep -c 'mmcblk0p[0-9]' /proc/partitions".format(host["IP"]), shell=True, executable='/bin/bash').decode("utf-8")
            if partitions == 1:
                #only 1 partitions, so create second partition
                os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "echo -e \'n\np\n\n98046\n\nw\n\' | sudo fdisk /dev/mmcblk0"'.format(host["IP"]))
            # create filesystem (deleting any existing fs on the card)
            os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "sudo mkfs.ext4 -F -F /dev/mmcblk0p2"'.format(host["IP"]))
            # create a copy of the clean, NFS mounted filesystem on the SD card    
            os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "sudo mkdir /mnt/tmp"'.format(host["IP"]))
            os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "sudo mount /dev/mmcblk0p2 /mnt/tmp"'.format(host["IP"]))
            os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "sudo rsync -xa  --exclude /mnt / /mnt/tmp"'.format(host["IP"]))
            # prepare to boot from the sd card image by adding line in fstab to mount root fs and switching /boot/cmdline.txt to original
            partitionUUID = subprocess.check_output("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} sudo udevadm info -n mmcblk0p2 -q property | sed -n 's/^ID_PART_ENTRY_UUID=//p'".format(host["IP"]), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)
            os.system("""ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'echo "PARTUUID={}  /               ext4    defaults,noatime  0       1" | sudo tee -a /mnt/tmp/etc/fstab'""".format(host["IP"], partitionUUID))
            cmdline = 'dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=PARTUUID={} rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles'.format(partitionUUID)
            os.system("""ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'echo -n "{}" | sudo tee /boot/cmdline.txt'""".format(host["IP"], cmdline))
            os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "sudo umount /mnt/tmp && sudo rmdir /mnt/tmp"'.format(host["IP"]))
            os.system("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} 'sudo sync && sudo reboot -n'".format(host["IP"]))
# remove the mount point
os.rmdir('/tmp/mnt')
