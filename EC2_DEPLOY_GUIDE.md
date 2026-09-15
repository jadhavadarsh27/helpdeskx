# EC2 Deployment Guide — HelpDeskX

This guide explains how to set up a new AWS EC2 instance and connect it to the existing GitHub Actions CI/CD workflow.

---

## Step 1 — Launch a New EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. Choose **Ubuntu 22.04 LTS** (recommended)
3. Select instance type: `t2.micro` (free tier eligible)
4. Create or select an existing **Key Pair** — save the `.pem` file securely
5. In **Security Group**, add the following inbound rules:

   | Type       | Port | Source    |
   |------------|------|-----------|
   | SSH        | 22   | 0.0.0.0/0 |
   | Custom TCP | 8000 | 0.0.0.0/0 |

6. Click **Launch Instance**

---

## Step 2 — Install Docker on the New EC2

SSH into your new instance:

```bash
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>
```

Then run the following commands to install and configure Docker:

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

Verify Docker is working:

```bash
docker ps
```

---

## Step 3 — Update GitHub Secrets

Go to: **GitHub → your repo → Settings → Secrets and variables → Actions**

Update the following secrets with your new EC2 details:

| Secret            | Action         | Value                                      |
|-------------------|----------------|--------------------------------------------|
| `EC2_HOST`        | ✅ Update      | New EC2 public IP address                  |
| `EC2_USERNAME`    | ✅ Update      | `ubuntu` (default for Ubuntu AMI)          |
| `EC2_SSH_KEY`     | ✅ Update      | Contents of your new `.pem` file           |
| `DOCKER_USERNAME` | ❌ No change   | Your Docker Hub username                   |
| `DOCKER_PASSWORD` | ❌ No change   | Your Docker Hub password or access token   |

### How to get your SSH key content:

```bash
cat your-key.pem
```

Copy the **entire output** including the header and footer lines:

```
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

Paste this as the value for the `EC2_SSH_KEY` secret.

---

## Step 4 — Trigger the Workflow

Push any change to the `main` branch to trigger the GitHub Actions workflow:

```bash
git commit --allow-empty -m "trigger deploy to new EC2"
git push origin main
```

GitHub Actions will automatically:
1. ✅ Checkout the code
2. ✅ Run tests
3. ✅ Build the Docker image
4. ✅ Push the image to Docker Hub
5. ✅ SSH into the new EC2 and deploy the container

You can monitor the workflow at:
```
https://github.com/jadhavadarsh27/helpdeskx/actions
```

---

## Step 5 — Verify the Deployment

Once the workflow completes, open your browser and navigate to:

```
http://<your-ec2-public-ip>:8000
```

> **Note:** Use `http://` not `https://` unless SSL is configured.

---

## Stopping & Avoiding Charges

When you're done, to avoid AWS charges:

### Stop the Docker container (on EC2):
```bash
docker stop helpdeskx
docker rm helpdeskx
```

### Stop the EC2 instance (AWS Console):
- EC2 → Instances → Select instance → **Instance State → Stop**

### Terminate the EC2 instance (permanent):
- EC2 → Instances → Select instance → **Instance State → Terminate**

> ⚠️ **Termination is irreversible.** All data on the instance will be deleted.

### After terminating, also clean up:
- **Elastic IPs** → EC2 → Elastic IPs → Release
- **Unattached EBS Volumes** → EC2 → Volumes → Delete

---

## Summary — What Needs to Change for a New EC2

The workflow file (`deploy.yml`) does **not** need any changes.
Only update the **3 GitHub Secrets** listed below:

| Secret         | Update with                  |
|----------------|------------------------------|
| `EC2_HOST`     | New public IP                |
| `EC2_USERNAME` | `ubuntu`                     |
| `EC2_SSH_KEY`  | Contents of new `.pem` file  |
