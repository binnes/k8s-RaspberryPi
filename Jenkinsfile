pipeline {
  agent any
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        chmod 777 scripts/regenPiCluster
        ./scripts/regenPiCluster.py
      }
    }
  }
}