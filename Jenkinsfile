pipeline {
  agent { dockerfile {
            filename 'Dockerfile'
            args '-v /mnt/ssd:/mnt/ssd -v /tmp:/tmp'
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