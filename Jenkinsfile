pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_CREDENTIALS = 'dockerhub-creds'
        ANSIBLE_SSH_CREDENTIALS = 'ansible-ssh-key'
        ANSIBLE_HOST = '192.168.1.10'
        ANSIBLE_USER = 'ansible'
        IMAGE_NAME = 'zahidbilal/flask-multibranch-demo'
    }

    stages {
        stage('Validate branch') {
            steps {
                script {
                    if (!(env.BRANCH_NAME in ['dev', 'staging', 'prod'])) {
                        echo "Branch ${env.BRANCH_NAME}: build and test only; no deployment configured."
                    }
                }
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    set -e
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m unittest discover -s tests -v
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh '''
                    set -e
                    IMAGE_TAG="${BRANCH_NAME}-${BUILD_NUMBER}"

                    docker build \
                        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
                        .

                    docker tag \
                        "${IMAGE_NAME}:${IMAGE_TAG}" \
                        "${IMAGE_NAME}:${BRANCH_NAME}-latest"
                '''
            }
        }

        stage('Container smoke test') {
            steps {
                sh '''
                    set -e

                    IMAGE_TAG="${BRANCH_NAME}-${BUILD_NUMBER}"

                    docker rm -f flask-ci-test >/dev/null 2>&1 || true

                    docker run -d \
                        --name flask-ci-test \
                        -p 127.0.0.1:5001:5000 \
                        "${IMAGE_NAME}:${IMAGE_TAG}"

                    trap 'docker rm -f flask-ci-test >/dev/null 2>&1 || true' EXIT

                    for i in $(seq 1 15); do
                        if curl --fail --silent \
                            http://127.0.0.1:5001/health; then
                            echo "Container health check passed"
                            exit 0
                        fi
                        sleep 2
                    done

                    echo "Health check failed"
                    docker logs flask-ci-test
                    exit 1
                '''
            }
        }

        stage('Push to Docker Hub') {
            when {
                expression {
                    env.BRANCH_NAME in ['dev', 'staging', 'prod']
                }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: env.DOCKERHUB_CREDENTIALS,
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        echo "$DOCKERHUB_TOKEN" |
                            docker login \
                                -u "$DOCKERHUB_USER" \
                                --password-stdin

                        IMAGE_TAG="${BRANCH_NAME}-${BUILD_NUMBER}"

                        docker push "${IMAGE_NAME}:${IMAGE_TAG}"
                        docker push "${IMAGE_NAME}:${BRANCH_NAME}-latest"

                        docker logout
                    '''
                }
            }
        }

        stage('Production approval') {
            when {
                branch 'prod'
            }
            steps {
                input(
                    message: 'Deploy this build to PRODUCTION?',
                    ok: 'Deploy to production'
                )
            }
        }

        stage('Deploy with Ansible') {
            when {
                expression {
                    env.BRANCH_NAME in ['dev', 'staging', 'prod']
                }
            }
            steps {
                script {
                    def target = env.BRANCH_NAME
                    def imageTag = "${target}-${env.BUILD_NUMBER}"

                    sshagent(credentials: [env.ANSIBLE_SSH_CREDENTIALS]) {
                        sh """
                            set -eu

                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=accept-new \
                                ${ANSIBLE_USER}@${ANSIBLE_HOST} \
                                'cd ~/flask-multibranch/ansible &&
                                 ansible-playbook playbooks/deploy.yml
                                 -e target_group=${target}
                                 -e image_name=${IMAGE_NAME}
                                 -e image_tag=${imageTag}'
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'docker rm -f flask-ci-test >/dev/null 2>&1 || true'
        }
    }
}
