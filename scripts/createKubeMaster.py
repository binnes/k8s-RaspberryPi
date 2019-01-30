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
    os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} """{}"""'.format(host, cmd)) 

def runRemoteCommandWithReturn(host, cmd):
    sys.stdout.write('Running remote command <<{}>> on host {}\n'.format(cmd, host)) ; sys.stdout.flush()
    return subprocess.check_output('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "{}"'.format(host, cmd), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)

def createKubeMaster(host):
    runRemoteCommand(host, "curl -sSL get.docker.com | sh && sudo usermod pi -aG docker")
    runRemoteCommand(host, "sudo dphys-swapfile swapoff && sudo dphys-swapfile uninstall && sudo update-rc.d dphys-swapfile remove")
    runRemoteCommand(host, "echo -n ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory' | sudo tee -a /boot/cmdline.txt)
    runRemoteCommand(host, "sudo reboot -n")
    waitForReboot(host)
    runRemoteCommand(host, "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -")
    runRemoteCommand(host, "echo 'deb http://apt.kubernetes.io/ kubernetes-xenial main' | sudo tee /etc/apt/sources.list.d/kubernetes.list")
    runRemoteCommand(host, "sudo apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy kubeadm")
    runRemoteCommand(host, "sudo kubeadm config images pull")
    initOutput = runRemoteCommandWithReturn(host, "sudo kubeadm init --token-ttl=0 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=$KUBEHOST")
    runRemoteCommand(host, "mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config")
    runRemoteCommand(host, "sudo mkdir -p $NFSRootPath/sysRoots/kube && sudo cp -i /etc/kubernetes/admin.conf $NFSRootPath/sysRoots/kube/config")
    runRemoteCommand(host, """kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')" """)
    runRemoteCommand(host, "sudo sysctl net.bridge.bridge-nf-call-iptables=1")
    return initOutput


with open('scripts/config.json') as f:
    config = json.load(f)

for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'M':
                joinText = createKubeMaster(host["IP"])
                sys.stdout.write('Join text =  <<{}>> on host {}\n'.format(joinText)) ; sys.stdout.flush()
                os.system("echo {} >> {}".format(joinText, config['testMachines']['NFSrootPath']+'/sysRoots/joinLog.txt'))
                break
