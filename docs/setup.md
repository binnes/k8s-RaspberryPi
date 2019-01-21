# Setup

This is a one time setup needed to create the base image which will be used to reset the test machine back to a base image using a filesystem served from an NFS server.

## Setting up a controller system

You need a linux controller system to run the automation.  This could be a virtual machine, but ideally another system in the cluster.  This machine will be the central controller for the automation and in my case is also the NFS server for the cluster.  I chose not to use a Raspberry Pi, as the network throughput and USB throughput of a Raspberry Pi are limited due to the internal architecture of the hardware.  For my controller I an using an [Up squared](https://up-board.org/upsquared/specifications/) board runninf Ubuntu 18.04.1LTS version and with a 1TB SSD external drive attached, which will be the NFS share for my cluster.

Before running the setup script on the controller you need to do some preparation on the controller system:

- User command ```sudo visudo``` to add the line:

  ```text
  user    ALL=(ALL) NOPASSWD: ALL
  ```

  to the end of the /etc/sudoers file, replacing **user** with your username on the controller system.  This allows the use of sudo without prompting for a password
- install **sshpass** package with command ```sudo apt-get install sshpass```.  This allows scripting of ssh, passing in the password.
- Have an NFS mount exported (doesn't need to be on the controller machine, but if not exported from the controller machine then the NFS share needs to be mounted on the controller machine).  My NFS is exported with the following line in the /etc/exports file on the controller (modify the subnet if you are not using 192.168.0.0/24 for your network):

    ```text
    /mnt/ssd	192.168.0.0/24(rw,sync,no_subtree_check,no_root_squash)
    ```

- If you are not exporting the NFS filesystem from the controller, then the NFS file system needs to be mounted on the controller system at the same location it is exported from (e.g. /mnt/ssd)
- clone the git repo onto the controller system with command ```git clone https://github.com/binnes/k8s-RaspberryPi.git``` then change into the git root directory with command ```cd k8s-RaspberryPi```

## Prepare the pi image

1. Download the latest [Raspbian lite image](https://downloads.raspberrypi.org/raspbian_lite_latest)
2. Flash the image to a micro-SD card
3. Enable ssh by creating an empty file called ssh in the **boot** partition of the SD card (on Linux and mac use command ```touch ssh``` on windows use command ```type NUL >> ssh``` in the folder where the boot partition is mounted).
4. Eject the SD card from your laptop and insert into the Rspberry Pi, then power on the Pi.
5. On the controller system run the script **createBaseImage.sh** in the scripts folder.  This must be done uing your normal user (not root).  The script does the following:
   - Update the software on the pi
   - Add ssh keys to allow password-less logon from the controller
   - Creates an image of the RaspberryPi file system to use on the NFS server
   - Updates the Pi system to use an NFS file system
   - Creates a filesystem on the NFS share for the pi, then reboots the Pi so it uses the NFS based filesystem
   - Creates a micro-SD card image to boot using the NFS hosted filesystem
