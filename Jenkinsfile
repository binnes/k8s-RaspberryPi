pipeline {
  agent { dockerfile true }
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh label: '', script: '''chmod 777 scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
  }
}