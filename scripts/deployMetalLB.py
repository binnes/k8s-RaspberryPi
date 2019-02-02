import json
import os
import sys
import string
import subprocess
import threading
import time
import socket


def log(txt):
    sys.stdout.write('{}\n'.format(txt)) ; sys.stdout.flush()

def runLocalCommand(cmd):
    ret = os.system('{}'.format(cmd))
    log('Ran local command <<{}>>, return code = {}'.format(cmd, ret))
    return ret

def runRemoteCommand(host, cmd):
    ret = os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -q pi@{} "{}"'.format(host, cmd)) 
    log('Ran remote command <<{}>> on host {}, return code = {}'.format(cmd, host, ret))
    return ret 

def runRemoteCommandWithReturn(host, cmd):
    sys.stdout.write('Running remote command <<{}>> on host {}\n'.format(cmd, host)) ; sys.stdout.flush()
    return subprocess.check_output('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -q pi@{} "{}"'.format(host, cmd), shell=True, executable='/bin/bash').decode("utf-8").strip(string.whitespace)

with open('scripts/config.json') as f:
    config = json.load(f)

# Deploy Metal LoadBalancer
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'M':
                runRemoteCommand(host["IP"], "mkdir -p /home/pi/kubernetes/manifests")
                os.system("scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no k8sManifests/metalLB.yaml pi@{}:kubernetes/manifests/metalLB.yaml".format(host["IP"]))
                runRemoteCommand(host["IP"], "kubectl apply -f /home/pi/kubernetes/manifests/metalLB.yaml")
                os.system("scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no k8sManifests/metalLB-conf.yaml pi@{}:kubernetes/manifests/metalLB-conf.yaml".format(host["IP"]))
                runRemoteCommand(host["IP"], "sed -i -e 's/IPRange/{}/g' /home/pi/kubernetes/manifests/metalLB-conf.yaml".format(config["kubernetes"]["metalLB"]["IPrange"]))
                runRemoteCommand(host["IP"], "kubectl apply -f /home/pi/kubernetes/manifests/metalLB-conf.yaml")
                break
  