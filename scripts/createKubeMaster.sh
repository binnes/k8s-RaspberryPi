#!/usr/bin/bash

KUBEHOST=`python scripts/getKubeHost.py`
NFSRootPath=`python -c "import json ; config = json.load(open('scripts/config.json')) ; print config['testMachines']['NFSrootPath']"`


ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "curl -sSL get.docker.com | sh && sudo usermod pi -aG docker"
# ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "newgrp docker"
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo dphys-swapfile swapoff && sudo dphys-swapfile uninstall && sudo update-rc.d dphys-swapfile remove"
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST 'echo -n `cat /boot/cmdline.txt` cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory | sudo tee /boot/cmdline.txt'
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo reboot -n"

sleep 60 # let the pi shutdown
while ! ping -c 1 $KUBEHOST &>/dev/null; do sleep 1; done
sleep 60

ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -"
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "echo 'deb http://apt.kubernetes.io/ kubernetes-xenial main' | sudo tee /etc/apt/sources.list.d/kubernetes.list"

ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo apt-get update -q && sudo apt-get install -qy kubeadm"
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo kubeadm config images pull -v3"
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo kubeadm init --token-ttl=0 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=$KUBEHOST" | grep 'kubeadm join' > $NFSRootPath/sysRoots/join.txt
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST 'mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config'
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST 'kubectl apply -f \"https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\''\n'\'')"'
ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@$KUBEHOST "sudo sysctl net.bridge.bridge-nf-call-iptables=1"
