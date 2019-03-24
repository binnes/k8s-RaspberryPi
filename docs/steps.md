# Kubernetes cluster on Raspberry Pi

Install the raspberry pi using these instructions from [github](https://github.com/alexellis/k8s-on-raspbian/blob/master/GUIDE.md)

## why

- learn kubernetes (and possibly helm)
- see how devops can be applied to IoT/Edge platforms
- Create multi-platform docker images
- explore DevOps options for digital asset creation and lifecycle
- learn how to better use open source DevOps tools, such as Jenkins
- get better at creating tests - test driven development!

## Setting up the master node

### Initial install

1. Flash an SD card with the latest [Raspbian Stretch lite image](https://downloads.raspberrypi.org/raspbian_lite_latest)
1. Mount the image on your laptop and create a file named ssh in the /boot folder of the SD card (on Linux and mac use command ```touch ssh``` on windows use command ```type NUL >> ssh```) then eject the card from your laptop and insert it into the Raspberry Pi
1. Boot the pi and login using ```ssh pi@raspberrypi.local``` (windows users will need to use putty) with the password **raspberry**
1. on the raspberry pi issue command ```sudo raspi-config```
    - Change the password for user pi
    - Set a hostname
    - Set required localisation settings
1. Set a static IP address (192.168.0.199)
    - run command ```cat >> /etc/dhcpcd.conf```
    - paste the following block (updating to match your network)
      ```bash
      interface eth0
      static ip_address=192.168.0.199/24
      static routers=192.168.0.1
      static domain_name_servers=192.168.0.4 192.168.0.3
      ```
    - hit Ctrl+D to finish editing the file
1. reboot the raspberry pi with command ```sudo reboot -n```

### Software update and install

The initial setup has been done and your Raspberry Pi is now on the network with the hostname and IP address you specified with the updated password for user pi.

Log back into your pi

1. ssh ```pi@<your hostname>.local``` using the password you set.
1. update the software on the pi using commands ```sudo apt-get update ; sudo apt-get upgrade -y```
1. install docker on the pi using command ```curl -sSL get.docker.com | sh && sudo usermod pi -aG docker```
1. change to docker group with command ```newgrp docker```
1. turn off swap (required for Kubernetes) with command ```sudo dphys-swapfile swapoff && sudo dphys-swapfile uninstall && sudo update-rc.d dphys-swapfile remove```
1. Add additional boot options using command ```sudo sed -i '$s/$/ cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory/' /boot/cmdline.txt```
1. reboot the raspberry pi using command ```sudo reboot -n```

### Kubernetes install and setup

You are now ready to start installing kubernetes on the Master node Raspberry Pi

1. Log back into the raspberry pi
1. Add the repos containing the packages using command ```curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - && echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list```
1. install the kubeadm package with command ```sudo apt-get update -q && sudo apt-get install -qy kubeadm```
1. pre-pull the images needed for a Kubernetes master using command ```sudo kubeadm config images pull -v3```
1. Initialise master node with a pod network CIDR using command ```sudo kubeadm init --token-ttl=0 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=192.168.0.199```
    - *Note: this create a non-expiring token, which is not recommended for production systems*
1. save the output, as this is needed to join the other raspberry pis to the cluster
    - E.g. ```kubeadm join 192.168.0.199:6443 --token qqm037.8xjktuif7eccb1lb --discovery-token-ca-cert-hash sha256:d3452605e1d45b067575e846a82353eef4f25d18dec5eb93825ae3ba1033f48a```
1. make the config available to the kubectl command by issuing the following command ```mkdir -p $HOME/.kube && sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config```
1. check everything worked by issuing the command ```kubectl get pods --namespace=kube-system``` and after a short while you should see all services running:
    ```text
        NAME                                   READY   STATUS    RESTARTS   AGE
    coredns-86c58d9df4-ct9gj               0/1     Pending   0          3m13s
    coredns-86c58d9df4-vpj65               0/1     Pending   0          3m14s
    etcd-bi-k8smaster                      1/1     Running   0          8m31s
    kube-apiserver-bi-k8smaster            1/1     Running   0          8m8s
    kube-controller-manager-bi-k8smaster   1/1     Running   0          8m9s
    kube-proxy-crxs8                       1/1     Running   0          8m14s
    kube-scheduler-bi-k8smaster            1/1     Running   0          8m31s
    ```
1. Apply the Weave Net driver on the master with command ```kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"```
1. Configure the network with command ```sudo sysctl net.bridge.bridge-nf-call-iptables=1```

## Setting up the remaining nodes

The setup of the other Raspberry Pis you want in your cluster is basically the same as the process for setting up the Master node up to step 5 of the Kubernetes setup.  Once you have completed up to and including **step 4** of the Kubernetes setup, run the following commands:

1. Configure the network using command ```sudo sysctl net.bridge.bridge-nf-call-iptables=1```
2. Issue the join command you saved when you ran step 5 of the Kubernetes setup on the Master node e.g. ```sudo kubeadm join 192.168.0.199:6443 --token qqm037.8xjktuif7eccb1lb --discovery-token-ca-cert-hash sha256:d3452605e1d45b067575e846a82353eef4f25d18dec5eb93825ae3ba1033f48a```
3. On the Master node you can now run ```kubectl get nodes``` to see the nodes that belong to the cluster:

    ```text
    NAME           STATUS   ROLES    AGE    VERSION
    bi-k8smaster   Ready    master   129m   v1.13.2
    bi-k8snode01   Ready    <none>   22m    v1.13.2
    ```

## Install the Kubernetes dashboard

1. Install the kubernetes dashboard with the command ```kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/72832429656c74c4c568ad5b7163fa9716c3e0ec/src/deploy/recommended/kubernetes-dashboard-arm.yaml```
    - or ```kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/master/aio/deploy/alternative/kubernetes-dashboard-arm-head.yaml```
2. Setup security, so you can skip login of the dashboard (not for use in a production environment) using command
    ```bash
    cat <<EOF | kubectl create -f -
    apiVersion: rbac.authorization.k8s.io/v1beta1
    kind: ClusterRoleBinding
    metadata:
      name: kubernetes-dashboard
      labels:
        k8s-app: kubernetes-dashboard
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: ClusterRole
      name: cluster-admin
    subjects:
    - kind: ServiceAccount
      name: kubernetes-dashboard
      namespace: kube-system
    EOF
    ```
3. Wait for the dashboard to deploy, then you can access it by starting the proxy on a new command window ```kubectrl proxy``` then access the UI using [http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=default](http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/overview?namespace=default)

## Install MetalLN layer 2 load balancer

1. Install the MetalLB load balancer with command ```kubectl apply -f https://raw.githubusercontent.com/google/metallb/v0.7.3/manifests/metallb.yaml && kubectl apply -f metalLB-conf.yaml```

## Install Helm and Tiller

Helm and tiller allow a collection of services to be managed as a whole instead of individually

1. Install helm using command (on master node)
    - wget https://storage.googleapis.com/kubernetes-helm/helm-v2.12.3-linux-arm.tar.gz
    - tar zxvf helm-v2.12.3-linux-arm.tar.gz
    - sudo cp linux-arm/helm /usr/local/bin
3. Setup service account using command
    ```bash
cat <<EOF | kubectl create -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
EOF
    ```
    1. init help with command ```helm init --service-account tiller --tiller-image timotto/rpi-tiller```

## Install storage on Master then share via NFS

1. With and NFS server and an exported NFS disk make it available to kubernetes using command ```helm install stable/nfs-client-provisioner --set nfs.server=bi-up2.local --set nfs.path=/mnt/ssd --set image.repository=quay.io/external_storage/nfs-client-provisioner-arm --set image.tag=latest --set storageClass.name=standard```

## Install traefik Ingress

1. Use helm to deploy Traefik ingress using command ```helm install --name traefik stable/traefik --set dashboard.enabled=true --set dashboard.domain=traefik.otterburn.home --set rbac.enabled=true  --set externalIP=192.168.0.200```

## Install the Kubernetes dashboard

1. Enter command ```helm install stable/kubernetes-dashboard --name kube-dash --set image.repository=k8s.gcr.io/kubernetes-dashboard-arm,enableSkipLogin=true,enableInsecureLogin=true,ingress.annotations."kubernetes\.io/ingress\.class"=traefik,ingress.enabled=true,ingress.hosts[0]='dashboard.bik8s.home'``` to deploy the dashboard.

## Install a private docker registry

1. Use helm to deploy a docker registry, using command ```helm install --name dr stable/docker-registry --set persistence.enabled=true,persistence.storageClass=standard```

## Install Jenkins

1. Use helm to deploy Jenkins using command ```helm install --name ci stable/jenkins --set Persistence.StorageClass=standard,rbac.install=true```
2. Wait until the deploy completes, you can see the status using command ```kubectl get svc --namespace kube-system -w ci-jenkins```
3. Get the admin password with ```printf $(kubectl get secret --namespace kube-system ci-jenkins -o jsonpath="{.data.jenkins-admin-password}" | base64 --decode);echo```
4. Get the URL with command ```export SERVICE_IP=$(kubectl get svc --namespace kube-system ci-jenkins --template "{{ range (index .status.loadBalancer.ingress 0) }}{{ . }}{{ end }}") && echo http://$SERVICE_IP:8080/login```