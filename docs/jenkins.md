# Running Jenkins

Jenkins will be used as the primary tool for continuous delivery.  It will run in a Docker container on the Controller machine.  

The docker container needs to be extended to add support for Docker build agents.

Create a docker file containing the following:

```dockerfile
FROM jenkins/jenkins:lts
USER root
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates apt-utils curl gnupg2 software-properties-common
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
RUN apt-get update
RUN apt-get install -y docker-ce
USER jenkins
```

then run ```docker build``` on the dockerfile to create the new docker image.  This is what needs to be run in the next step.

1. To install and run Jenkins issue the following command : ```docker run -u root -d -p 8080:8080 -p 50000:50000 -v jenkins-data:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock --restart=always --privileged --cap-add=CAP_MKNOD  <tag or image ID of image build in previous step>```
2. To access the Jenkins console use URL http://<controller hostname>.local:8080 you should be prompted for an admin password.  To get this password do the following:
    1. run command ```docker ps -a``` and take note of the container ID of the Jenkins docker image
    2. run command ```docker exec <ID> cat /var/jenkins_home/secrets/initialAdminPassword```, where <ID> should be replaced with the container ID returned in previous step.
4. Select to install the suggested plugins
5. Create a new user