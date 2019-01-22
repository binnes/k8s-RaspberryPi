pipeline {
  agent any
  stages {
    stage('reset') {
      steps {
        echo 'Reset stage'
        python $WORKSPACE/scripts/regenPiCluster.py
      }
    }
  }
}