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
                # Note: this deployment disables all security, so not a good option for production or publically accessible clusters
                # TODO: lock down with appropriate security and access control
                 runRemoteCommand(host["IP"], "helm install stable/kubernetes-dashboard --name kube-dash --set image.repository=k8s.gcr.io/kubernetes-dashboard-arm,enableSkipLogin=true,enableInsecureLogin=true,ingress.annotations.'kubernetes\.io/ingress\.class'=traefik,ingress.enabled=true,ingress.hosts[0]='dashboard.{}',service.externalPort=8080,rbac.clusterAdminRole=true --namespace kube-system".format(config["kubernetes"]["domain"]))
