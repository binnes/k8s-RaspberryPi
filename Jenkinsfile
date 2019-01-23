pipeline {
  agent { dockerfile true }
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh label: '', script: '''chmod +x scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
  }
}