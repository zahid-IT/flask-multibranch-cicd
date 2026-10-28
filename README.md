# Flask Multibranch CI/CD: GitHub + Jenkins + Docker Hub + Ansible

A learning project for a Jenkins Multibranch Pipeline that tests a Flask app, builds a Docker image, pushes it to Docker Hub, and deploys to separate Ubuntu VMs using Ansible.

## Branch workflow

- `dev`: deploy to the development VM
- `test`: deploy to the test VM
- `prod`: requires a Jenkins manual approval before production deployment
- Other branches: unit tests and image build/smoke test only

Images are tagged as `<branch>-<build-number>` and `<branch>-latest`.

## 1. Prepare the Jenkins controller/agent

The Jenkins node running this pipeline needs Git, Python 3, `python3-venv`, Docker Engine, Ansible, `ssh-agent`, and `curl`. The Jenkins OS user must be able to run Docker and Ansible. If you add the `jenkins` user to the `docker` group, remember that Docker access is effectively root-level access.

On Ubuntu, install prerequisites as needed:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip ansible openssh-client curl
```

Install Docker Engine using Docker's official Ubuntu installation instructions: https://docs.docker.com/engine/install/ubuntu/

Ensure Jenkins can run these commands:

```bash
sudo -u jenkins docker version
sudo -u jenkins ansible --version
sudo -u jenkins ssh -V
```

## 2. Prepare deployment VMs

Install Docker Engine on each target VM. Make sure the SSH user can connect from Jenkins and run Docker with sudo. The playbook uses `become: true`, so the SSH account needs sudo permission (preferably passwordless sudo for non-interactive CI jobs).

Edit `ansible/inventory/hosts.ini` to match your VM IP addresses and usernames. Example IPs are placeholders:

```ini
[dev]
192.168.1.4 ansible_user=dev
[test]
192.168.1.6 ansible_user=test
[prod]
192.168.1.5 ansible_user=prod
```

Test SSH and Ansible connectivity from the Jenkins execution node before running the pipeline:

```bash
cd ansible
ansible all -m ping
```

## 3. Push this project to GitHub

Create an empty GitHub repository, then from this directory run:

```bash
git init
git add .
git commit -m "Initial Flask multibranch CI/CD project"
git branch -M dev
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY.git
git push -u origin dev
git checkout -b test
git push -u origin test
git checkout -b prod
git push -u origin prod
```

Create a Multibranch Pipeline in Jenkins and configure its repository URL. Enable periodic branch indexing or configure a GitHub webhook. Jenkins discovers branches that contain a root-level `Jenkinsfile`.

## 4. Configure Jenkins plugins

Install/verify these plugins under **Manage Jenkins → Plugins**:

- Pipeline
- Multibranch Pipeline
- Git and GitHub Branch Source (if using GitHub as the branch source)
- Credentials Binding
- SSH Agent

## 5. Configure credentials

Add these under **Manage Jenkins → Credentials**:

1. ID `dockerhub-creds`: Username with password. Use your Docker Hub username and a Docker Hub access token as the password.
2. ID `ansible-ssh-key`: SSH Username with private key, containing the SSH private key Jenkins uses to access the deployment VMs.

The SSH public key must be installed in the target user's `~/.ssh/authorized_keys`. Ensure host keys are trusted/managed securely for your environment. The sample `ansible.cfg` disables host key checking for lab convenience; for production, enable host key checking and pre-populate `known_hosts`.

## 6. Update Jenkinsfile

Replace `YOUR_DOCKERHUB_USERNAME` in `Jenkinsfile` with your Docker Hub username and repository name. Commit and push that change to each branch. Keep the repository public or configure suitable GitHub checkout credentials.

## 7. Create the Multibranch Pipeline job

1. Jenkins Dashboard → **New Item**.
2. Enter a job name and select **Multibranch Pipeline**.
3. Add a GitHub Branch Source (or Git source) and enter the repository URL.
4. Save, then choose **Scan Multibranch Pipeline Now**.
5. Open the `dev` branch job and run it. After validating dev and test, test `prod`; it pauses for manual approval before deployment.

## 8. Verify deployment

From a machine that can reach the target VM:

```bash
curl http://DEV_VM_IP:5000/health
curl http://DEV_VM_IP:5000/
```

The application should respond with JSON. Repeat with the test or production VM IP.

## Security and lab notes

- Do not commit passwords, tokens, or private keys to Git.
- The sample inventory IPs and usernames must be replaced with your real VM details.
- The sample is intended for a learning lab. Production environments should use managed secrets, secure host-key verification, image scanning, restricted deployment permissions, and a rollback strategy.
- The Jenkins node needs Docker access to build and smoke-test images. Target nodes need Docker to pull and run the published image.
