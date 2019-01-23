#!/bin/bash

echo "*****Waiting for raspberrypi.local to appear on network"
while ! ping -c 1 raspberrypi.local &>/dev/null; do sleep 1; done
sleep 30

echo "*****Updating Raspberry Pi"
sshpass -p raspberry ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo apt-get update & sudo apt-get upgrade'

echo "*****Adding remote login ssh keys"
[ -f $HOME/.ssh/id_rsa ] || ssh-keygen -f $HOME/.ssh/id_rsa -t rsa -N ''
sshpass -p raspberry ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'mkdir -p .ssh'
cat .ssh/id_rsa.pub | sshpass -p raspberry ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'cat >> .ssh/authorized_keys'

echo "*****Creating base image for NFS share"
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo mkdir -p /nfs/base'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo apt-get install -y rsync'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo rsync -xa --progress --exclude /nfs / /nfs/base'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'cd /nfs/base/etc && sudo sed -i '/ext4/d' ./fstab'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'cd /nfs/base && sudo tar -zcpf /nfs/base-raspbian-stretch-lite.tgz .'
[ -d "/mnt/ssd/sysRoots" ] || sudo mkdir -p /mnt/ssd/sysRoots
scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local:/nfs/base-raspbian-stretch-lite.tgz $HOME/base-raspbian-stretch-lite.tgz
sudo mv $HOME/base-raspbian-stretch-lite.tgz /mnt/ssd/sysRoots/

echo "*****Generating NFS filesystem for raspberrypi.local"
sudo mkdir -p /mnt/ssd/sysRoots/raspberrypi
cd /mnt/ssd/sysRoots/raspberrypi
sudo tar -zxvf /mnt/ssd/sysRoots/base-raspbian-stretch-lite.tgz

echo "*****Rebooting pi to use NFS filesystem"
# Update the boot filesystem on host raspberry pi to use the NFS file system and reboot the host
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local  'echo "dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.190:/mnt/ssd/sysRoots/raspberrypi,vers=3 rw ip=dhcp elevator=deadline rootwait" | sudo dd of=/boot/cmdline.txt'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local  'sudo reboot -n'

echo "*****Generating SD card image for raspberrypi.local"
sleep 60 # let the pi shutdown
while ! ping -c 1 raspberrypi.local &>/dev/null; do sleep 1; done
sleep 60
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo umount /boot'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo fdisk /dev/mmcblk0 <<EOF
d
2
w
EOF
'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo dd bs=1M if=/dev/mmcblk0 of=/raspbian_boot.img count=60'
sudo gzip /mnt/ssd/sysRoots/raspberrypi/raspbian_boot.img
sudo mv /mnt/ssd/sysRoots/raspberrypi/raspbian_boot.img.gz /mnt/ssd/sysRoots/raspbian_boot.img.gz
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@raspberrypi.local 'sudo mount /boot'