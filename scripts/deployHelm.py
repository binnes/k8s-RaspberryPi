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

# Deploy Helm / tiller
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'M':
                runRemoteCommand(host["IP"], "mkdir -p /home/pi/kubernetes/manifests")
                runLocalCommand("scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no k8sManifests/helm-rbac.yaml pi@{}:kubernetes/manifests/helm-rbac.yaml".format(host["IP"]))
                runRemoteCommand(host["IP"], "kubectl apply -f /home/pi/kubernetes/manifests/helm-rbac.yaml")
                runRemoteCommand(host["IP"], "wget https://storage.googleapis.com/kubernetes-helm/helm-v2.12.3-linux-arm.tar.gz")
                runRemoteCommand(host["IP"], "tar zxvf helm-v2.12.3-linux-arm.tar.gz")
                runRemoteCommand(host["IP"], "sudo cp linux-arm/helm /usr/local/bin")
                runRemoteCommand(host["IP"], "rm -rf linux-arm && rm helm-v2.12.3-linux-arm.tar.gz")
                runRemoteCommand(host["IP"], "helm init --service-account tiller --tiller-image jessestuart/tiller")
                # Wait for tiller pod to start before ending this script
                tillerRunning = False
                timeout = time.time() + 180
                log("Waiting for tiller pod to start")
                while tillerRunning == False and time.time() < timeout:
                    time.sleep(10)
                    try:
                        pods = runRemoteCommandWithReturn(host["IP"], "kubectl get pods --all-namespaces | grep tiller")
                        if "Running" in pods:
                            tillerRunning = True
                    except subprocess.CalledProcessError:
                        pass

                if tillerRunning == True:
                    log("Tiller started")
                else:
                    log("Tiller failed to start")
                    sys.exit(1)
                    
