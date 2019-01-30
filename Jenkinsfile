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
        echo 'Build Jubernetes cluster'
        sh label: 'Build cluster nodes', script: '''chmod +x scripts/createKubeCluster.py && python ./scripts/createKubeCluster.py'''
      }
    }
  }
}