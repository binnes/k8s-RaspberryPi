pipeline {
  agent { dockerfile {
            filename 'Dockerfile'
            args '-v /mnt/ssd:/mnt/ssd'
           }
  }
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh label: '', script: '''chmod +x scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
  }
}