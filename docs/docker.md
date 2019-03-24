# Installing Docker on the Controller

The controller machine needs to run Docker, so use the following steps (assuming an Ubuntu bionic 18.04TLS system):

1. Remove any old installations with command ```sudo apt-get remove docker docker-engine docker.io containerd runc```
2. Allow apt command to use a repo via https with commands ```sudo apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common```
3. Add the Docker repo GPG key with command ```curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -```
4. Add the Docker repo with command ```sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"```
5. Update the package index with command ```sudo apt-get update```
6. Install Docker with command ```sudo apt-get install -y docker-ce```
7. Add your user to the with command ```sudo usermod -aG docker $USER```, you will need to log out and relog back in to be able to access Docker from your user account without using sudo.

## Caching images locally

To save bandwidth and improve local performance you may want to set up a local docker registry to cache images.  This will allow images to be pulled only once then served locally after.

To run the docker mirror cache run the following:

```bash
mkdir -p /mnt/ssd/docker_mirror/cache
mkdir -p /mnt/ssd/docker_mirror/certs
docker run --name docker_registry_proxy -d -p 0.0.0.0:3128:3128 -v /mnt/ssd/docker_mirror/cache:/docker_mirror_cache        -v /mnt/ssd/docker_mirror/certs:/ca -e REGISTRIES="k8s.gcr.io gcr.io quay.io" -e AUTH_REGISTRIES="" --restart=always rpardini/docker-registry-proxy:0.2.4
openssl x509 -in /mnt/ssd/docker_mirror/certs/ca.crt -out /mnt/ssd/docker_mirror/certs/ca.pem -outform PEM
```

You can now setup you local docker instances to use the local registry as a mirror:

On a raspberry pi create a file /etc/docker/daemon.json run the following:

```bash
cat <<EOF| sudo tee /lib/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://192.168.0.190:3128/"
Environment="HTTPS_PROXY=http://192.168.0.190:3128/"
EOF 
```

replace 192.168.0.190 with the address of your registry host machine.

You also need to add the CA Root certificate for the mirror to the trusted roots on each machine.  The root certificate is located at **/mnt/ssd/docker_mirror/certs/ca.pem**, which need to be copied to **/usr/share/ca-certificates** and rename it to docker_registry_ca.pem.  Then add the certificate with command ```echo "docker_registry_ca.pem" | sudo tee -a /etc/ca-certificates.conf``` then make it live with command ```update-ca-certificates --fresh```

