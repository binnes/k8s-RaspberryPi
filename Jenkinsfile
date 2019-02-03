pipeline {
  agent { dockerfile {
            filename 'Dockerfile'
            args '-v /mnt/ssd:/mnt/ssd -v /home/brian/.ssh:/root/.ssh --privileged  --cap-add=CAP_MKNOD'
           }
  }
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh label: 'Reset all host systems', script: '''chmod +x scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
    stage('Kubernetes') {
      steps {
        echo 'Build Kubernetes cluster'
        sh label: 'Build cluster nodes', script: '''chmod +x scripts/createKubeCluster.py && python ./scripts/createKubeCluster.py'''
        sh label: 'Deploy load balancer', script: '''chmod +x scripts/deployMetalLB.py && python ./scripts/deployMetalLB.py'''
        sh label: 'Deploy helm / tiller', script: '''chmod +x scripts/deployHelm.py && python ./scripts/deployHelm.py'''
        sh label: 'Deploy storage', script: '''chmod +x scripts/deployStorage.py && python ./scripts/deployStorage.py'''
        sh label: 'Deploy Traefik', script: '''chmod +x scripts/deployTraefik.py && python ./scripts/deployTraefik.py'''
      }
    }
  }
}