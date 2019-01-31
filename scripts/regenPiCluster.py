#!/usr/bin/python

import json
import os
import sys
import string
import subprocess
import threading
import time
import socket

def waitForReboot(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    time.sleep(30)
    while True:
        try:
            s.connect((host, 22))
            break
        except socket.error as e:
            time.sleep(1)
    # continue
    s.close()
    # let OS boot fully before continuing
    time.sleep(30)

def runRemoteCommand(host, cmd):
    sys.stdout.write('Running remote command <<{}>> on host {}\n'.format(cmd, host)) ; sys.stdout.flush()
    os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "{}"'.format(host, cmd)) 

def runRemoteCommandWithReturn(host, cmd):
    sys.stdout.write('Running remote command <<{}>> on host {}\n'.format(cmd, host)) ; sys.stdout.flush()
    return subprocess.check_output('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "{}"'.format(host, cmd), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)

class resetPi3BThread (threading.Thread):
    def __init__(self, conf, sysType, host):
        threading.Thread.__init__(self)
        self.config = conf
        self.sysType = sysType
        self.host = host
    def run(self):
        fsRoot = self.config["testMachines"]["NFSrootPath"] + '/sysRoots'
        # Create a mount point for the boot images
        mountPoint = '/tmp/mnt/'+self.host["name"]
        if not os.path.exists(mountPoint):
            os.mkdir(mountPoint)
        dirName = fsRoot+'/'+self.host["name"]
        existingDirName = dirName + '_old'
        newDirName = dirName + '_new'
        if os.path.exists(newDirName):
            os.system('rm -rf ' + newDirName)
        os.mkdir(newDirName)
        os.chdir(newDirName)
        os.system('tar -zxpf '+fsRoot + '/' + self.sysType["fsImage"] +' --same-owner -C ' + newDirName)
        # Fix up /etc/hostname
        file = open(newDirName+'/etc/hostname','w')
        file.write(self.host["name"])
        file.close()
        # Fix up /etc/hosts
        os.system("sed -i 's/raspberrypi/"+self.host["name"]+"/g' " +newDirName+"/etc/hosts")
        # Fix up networking and configure static IP address
        file = open(newDirName + '/etc/dhcpcd.conf', "a+")
        file.write("interface eth0\n")
        file.write("static ip_address=%s/%s\n" % (self.host["IP"], self.config["testMachines"]["network"]["subnetBits"]))
        file.write("static routers=%s\n" % self.config["testMachines"]["network"]["routerIP"])
        file.write("static domain_name_servers=%s\n" % self.config["testMachines"]["network"]["nameservers"])
        file.close()
        # Setup apt cache if configured
        try:
            os.system("""echo 'Acquire::http {{ proxy "http://{}:3142"; }};' | sudo tee ()/etc/apt/apt.conf.d/02proxy""".format(config['testMachines']['AptCache'], newDirName))
        except KeyError:
            sys.stdout.write('Apt Cache option not specified\n') ; sys.stdout.flush()

        # Fix up file system mounts
        runRemoteCommand(self.host["IP"], "sudo sed -i '/ext4/d' /etc/fstab")
        # Create the sd card image if doesn't exist and reset boot command on SD card in host
        cmdline = 'dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/{},vers=3 rw ip={}::{}:{}:{}:eth0:off elevator=deadline rootwait'.format(self.host["name"], self.host["IP"], self.config["testMachines"]["network"]["routerIP"], self.config["testMachines"]["network"]["netmask"], self.host["name"])
        runRemoteCommand(self.host["IP"], "echo -n '{}' | sudo tee /boot/cmdline.txt".format(cmdline))
        imageName = dirName+'.img'
        if not os.path.isfile(imageName):
            os.system('cp ' + fsRoot + '/' + self.sysType["bootImage"] + ' ' + imageName+'.gz')
            os.system('gzip -d ' + imageName+'.gz')
            os.system('mount -o loop,offset=4194304 -t msdos ' + imageName + ' ' + mountPoint)
            file = open(mountPoint + '/cmdline.txt', 'w')
            file.write(cmdline)
            file.close()
            os.system('umount ' + mountPoint)
        #If there is a current filesystem for host then rename to hostname_old
        # deleting previous one if it exist 
        if os.path.exists(existingDirName):
            os.system('rm -rf ' + existingDirName)
        if os.path.exists(dirName):
            os.system('mv ' + dirName + ' ' + existingDirName)
        #move newly created filesystem in place
        os.system('mv ' + newDirName + ' ' + dirName)
        #determine number of partitions on SD card
        partitions = runRemoteCommandWithReturn(self.host["IP"], "grep -c 'mmcblk0p[0-9]' /proc/partitions")
        sys.stdout.write('sdcard has {} partitions\n'.format(partitions)) ; sys.stdout.flush()
        if partitions == '1':
            #only 1 partitions, so create second partition
            runRemoteCommand(self.host["IP"], "echo -e 'n\np\n\n98046\n\nw\n' | sudo fdisk /dev/mmcblk0")
        runRemoteCommand(self.host["IP"], "sudo reboot -n")
        waitForReboot(self.host["IP"])
        # create filesystem (deleting any existing fs on the card)
        runRemoteCommand(self.host["IP"], "sudo mkfs.ext4 -F -F /dev/mmcblk0p2")
        
        # create a copy of the base raspbian filesystem on the SD card    
        runRemoteCommand(self.host["IP"], "sudo mkdir /mnt/tmp")
        runRemoteCommand(self.host["IP"], "sudo mount /dev/mmcblk0p2 /mnt/tmp")

        os.system('scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {}/{} pi@{}:/home/pi/{}'.format(fsRoot, self.sysType["fsImage"], self.host["IP"], self.sysType["fsImage"]))
        runRemoteCommand(self.host["IP"], "cd /mnt/tmp && sudo tar -zxpf /home/pi/{} -C .".format(self.sysType["fsImage"]))
        runRemoteCommand(self.host["IP"], "rm /home/pi/{}".format(self.sysType["fsImage"]))

        # Fix up /etc/hostname
        runRemoteCommand(self.host["IP"], "echo {} | sudo tee /mnt/tmp/etc/hostname".format(self.host["name"]))
        # Fix up /etc/hosts
        runRemoteCommand(self.host["IP"], "sudo sed -i 's/raspberrypi/{}/g' /mnt/tmp/etc/hosts".format(self.host["name"]))
        # Fix up networking and configure static IP address
        runRemoteCommand(self.host["IP"], """echo '''
interface eth0
static ip_address={}/{}
static routers={}
static domain_name_servers={}
''' | sudo tee -a /mnt/tmp/etc/dhcpcd.conf""".format(self.host["IP"], self.config["testMachines"]["network"]["subnetBits"], self.config["testMachines"]["network"]["routerIP"], self.config["testMachines"]["network"]["nameservers"]))

        # Fix up file system mounts
        runRemoteCommand(self.host["IP"], "sudo sed -i '/ext4/d' /mnt/tmp/etc/fstab")

        # Setup apt cache if configured
        try:
            runRemoteCommand(self.host["IP"], """echo 'Acquire::http {{ proxy "http://{}:3142"; }};' | sudo tee /mnt/tmp/etc/apt/apt.conf.d/02proxy""".format(config['testMachines']['AptCache']))
        except KeyError:
            sys.stdout.write('Apt Cache option not specified\n') ; sys.stdout.flush()

        # prepare to boot from the sd card image by adding line in fstab to mount root fs and switching /boot/cmdline.txt to original
        partitionUUID = runRemoteCommandWithReturn(self.host["IP"], "sudo udevadm info -n mmcblk0p2 -q property | sed -n 's/^ID_PART_ENTRY_UUID=//p'")
        runRemoteCommand(self.host["IP"], "echo 'PARTUUID={}  /               ext4    defaults,noatime  0       1' | sudo tee -a /mnt/tmp/etc/fstab".format(partitionUUID))
        cmdline = 'dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=PARTUUID={} rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles'.format(partitionUUID)
        runRemoteCommand(self.host["IP"], "echo -n '{}' | sudo tee /boot/cmdline.txt".format(cmdline))
        runRemoteCommand(self.host["IP"], "sudo umount /mnt/tmp && sudo rmdir /mnt/tmp")
        runRemoteCommand(self.host["IP"], "sudo sync && sudo reboot -n")
        os.rmdir(mountPoint)
        # wait for host to come back on line - so future deploy stages don't fail
        waitForReboot(self.host["IP"])


# Create a mount point for the boot images
if not os.path.exists('/tmp/mnt'):
    os.mkdir('/tmp/mnt')
with open('scripts/config.json') as f:
    config = json.load(f)

threads = []

for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            sys.stdout.write('Resetting host {}\n'.format(host)) ; sys.stdout.flush()
            thread = resetPi3BThread(config, sysType, host)
            thread.start()
            threads.append(thread)
for t in threads:
    t.join()