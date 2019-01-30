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
    os.system("""ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} '''{}'''""".format(host, cmd)) 

def runRemoteCommandWithReturn(host, cmd):
    sys.stdout.write('Running remote command <<{}>> on host {}\n'.format(cmd, host)) ; sys.stdout.flush()
    return subprocess.check_output('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@{} "{}"'.format(host, cmd), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)

def prepareKubeHost(config, host):
    runRemoteCommand(host, "curl -sSL get.docker.com | sh && sudo usermod pi -aG docker")
    runRemoteCommand(host, "sudo dphys-swapfile swapoff && sudo dphys-swapfile uninstall && sudo update-rc.d dphys-swapfile remove")
    runRemoteCommand(host, "echo -n ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory' | sudo tee -a /boot/cmdline.txt")
    runRemoteCommand(host, "sudo reboot -n")
    waitForReboot(host)
    runRemoteCommand(host, "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -")
    runRemoteCommand(host, "echo 'deb http://apt.kubernetes.io/ kubernetes-xenial main' | sudo tee /etc/apt/sources.list.d/kubernetes.list")
    runRemoteCommand(host, "sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq kubeadm")


def createKubeMaster(config, host):
    prepareKubeHost(config, host)
    runRemoteCommand(host, "sudo kubeadm config images pull")
    initOutput = runRemoteCommandWithReturn(host, "sudo kubeadm init --token-ttl=0 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address={}".format(host))
    runRemoteCommand(host, "mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config")
    os.system("mkdir -p {}/sysRoots/kube".format(config['testMachines']['NFSrootPath']))
    kubeConf = runRemoteCommandWithReturn(host, "sudo cat /etc/kubernetes/admin.conf")
    os.system('echo "{}" > {}/sysRoots/kube/config'.format(kubeConf, config['testMachines']['NFSrootPath']))
    kVersion = runRemoteCommandWithReturn(host, "kubectl version | base64 | tr -d '\n'")
    sys.stdout.write('Kubectl version =  <<{}>> \n'.format(kVersion)) ; sys.stdout.flush()
    runRemoteCommand(host, 'kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version={}"'.format(kVersion))
    runRemoteCommand(host, "sudo sysctl net.bridge.bridge-nf-call-iptables=1")
    return initOutput

class createKubeNode (threading.Thread):
    def __init__(self, conf, host, joinCmd):
        threading.Thread.__init__(self)
        self.config = conf
        self.host = host
        self.joinCmd = joinCmd
    def run(self):
         prepareKubeHost(self.config, self.host)
         runRemoteCommand(self.host, "sudo sysctl net.bridge.bridge-nf-call-iptables=1")
         runRemoteCommand(self.host, "sudo {}".format(self.joinCmd)

with open('scripts/config.json') as f:
    config = json.load(f)

# Create Kube master
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'M':
                joinText = createKubeMaster(config, host["IP"])
                os.system("""echo "{}" > {}/sysRoots/joinLog.txt""".format(joinText, config['testMachines']['NFSrootPath']))
                break

joinCmd = subprocess.check_output("grep 'kubeadm join' {}/sysRoots/joinLog.txt".format(config['testMachines']['NFSrootPath']), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)
sys.stdout.write('Join command =  <<{}>>\n'.format(joinCmd)) ; sys.stdout.flush()

# Create Kube nodes
threads = []
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'N':
                sys.stdout.write('creating kubernetes node {}\n'.format(host["name"])) ; sys.stdout.flush()
                thread = createKubeNode(config, host["IP"], joinCmd)
                thread.start()
                threads.append(thread)
for t in threads:
    t.join()
