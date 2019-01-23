pipeline {
  agent { dockerfile true }
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh script: '''pip install paramiko''' 
        sh label: '', script: '''chmod +x scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
  }
}