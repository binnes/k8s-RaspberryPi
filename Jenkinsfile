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
        sh label: '', script: '''chmod +x scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
    stage('Kubernetes') {
      steps {
        echo 'Build master node'
        sh label: '', script: '''chmod +x scripts/createKubeMaster.py && python ./scripts/createKubeMaster.py'''
      }
    }
  }
}