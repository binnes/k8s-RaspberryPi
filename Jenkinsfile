pipeline {
  agent any
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh label: '', script: '''chmod 777 scripts/regenPiCluster.py && python ./scripts/regenPiCluster.py'''
      }
    }
  }
}