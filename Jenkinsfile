pipeline {
  agent any
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        sh chmod 777 ./scripts/regenPiCluster
        python ./scripts/regenPiCluster.py
      }
    }
  }
}