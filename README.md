# 🎫 HelpDeskX

[![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-jadhavadarsh27%2Fhelpdeskx-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/jadhavadarsh27/helpdeskx)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-manifests-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#-license)

A cloud-native IT service desk and ticket management platform built with Django. Employees raise
tickets, support agents triage and resolve them, and admins manage categories, SLA policies, and
reporting — all from a single dashboard.

> 💡 **New here?** Jump straight to [Quick Start](#-quick-start-pick-one) and pick the setup path that matches how you want to run this.

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack Map](#-tech-stack-map)
- [Quick Start (pick one)](#-quick-start-pick-one)
  - [Local (venv)](#option-a--local-venv)
  - [Docker Compose](#option-b--docker-compose)
  - [Kubernetes](#option-c--kubernetes)
  - [Vercel (serverless)](#option-d--vercel-serverless)
- [Demo Logins](#-demo-logins)
- [Project Layout](#-project-layout)
- [Troubleshooting](#-troubleshooting)
- [Deployment Checklist](#-deployment-checklist)
- [Roadmap](#-roadmap--suggested-next-steps)

---

## ✨ Features

<details>
<summary><strong>Auth & roles</strong></summary>

Custom `User` model with `Employee`, `Support Agent`, and `Admin` roles. Self-service sign-up plus a Django admin panel for provisioning.
</details>

<details>
<summary><strong>Ticket lifecycle</strong></summary>

`New → Assigned → In Progress → Resolved → (Closed | Reopened)`. Employees confirm a resolution to close a ticket, or reject it to reopen it.
</details>

<details>
<summary><strong>SLA management</strong></summary>

Per-priority response/resolution windows (`SLAPolicy`), an automatic due-date stamp on every new ticket, and an "overdue" flag surfaced in the UI.
</details>

<details>
<summary><strong>Comments & audit trail</strong></summary>

Agents can leave internal notes hidden from the employee. A full ticket-history log records every status/assignment change.
</details>

<details>
<summary><strong>Attachments</strong></summary>

File uploads on ticket creation.
</details>

<details>
<summary><strong>Notifications</strong></summary>

In-app notifications on ticket creation, assignment, status changes, and comments. See `notifications/services.py` — swap in email/WebSocket delivery later without touching call sites.
</details>

<details>
<summary><strong>Knowledge base</strong></summary>

Searchable articles ("Wi-Fi not working", "Password reset", etc.) to deflect repeat tickets.
</details>

<details>
<summary><strong>Dashboard</strong></summary>

Total / open / pending / resolved / closed / high-priority / overdue counts, average resolution time, tickets by category / status / department, and agent performance (admin view).
</details>

<details>
<summary><strong>Feedback</strong></summary>

Employees rate resolved tickets 1–5 when accepting them.
</details>

---

## 🧩 Tech Stack Map

| Technology | Where it's used |
|---|---|
| Django (DRF-ready structure) | `accounts`, `tickets`, `knowledgebase`, `dashboard`, `notifications` apps |
| Docker | `Dockerfile` (app image), `docker-compose.yml` (app + Postgres + Redis) |
| Kubernetes | `k8s/deployment.yaml` (Deployment, Service, HPA), `k8s/config-and-ingress.yaml` (ConfigMap, Secret, Ingress, NetworkPolicy) |
| Terraform | `terraform/main.tf` — VPC with public/private subnets, EKS cluster + node group, managed Postgres |
| Networking | Ingress + TLS, `NetworkPolicy` restricting pod egress to DB/Redis only, ClusterIP service in front of the Django pods |

---

## 🚀 Quick Start (pick one)

### Option A — Local (venv)

<details>
<summary>Click to expand steps</summary>

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo      # optional: demo users, tickets, KB articles
python manage.py runserver
```

Visit **http://localhost:8000/** — you'll land on the dashboard once logged in.
</details>

### Option B — Docker Compose

<details>
<summary>Click to expand steps</summary>

```bash
docker compose up --build
```

Brings up the Django app, Postgres, and Redis together. First-time setup:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
</details>

### Option C — Kubernetes

<details>
<summary>Click to expand steps</summary>

```bash
# 1. Build and push the image to Docker Hub
docker build -t jadhavadarsh27/helpdeskx:latest .
docker push jadhavadarsh27/helpdeskx:latest

# 2. Update k8s/deployment.yaml with your image reference, then apply
kubectl apply -f k8s/

# 3. Provision the underlying cluster/VPC/DB with Terraform
cd terraform && terraform init && terraform apply
```
</details>

### Option D — Vercel (serverless)

<details>
<summary>Click to expand steps ⚠️ requires external Postgres</summary>

Vercel's filesystem is read-only, so SQLite **will not work** — every write throws `OperationalError: unable to open database file`. Use a managed Postgres instead:

```bash
# 1. Create a free Postgres DB (Neon or Supabase)
# 2. Add to requirements.txt: dj-database-url, psycopg2-binary
# 3. In settings.py:
#    DATABASES = {'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))}

# 4. Add DATABASE_URL as an env var in the Vercel dashboard, then:
vercel env pull .env.local
python manage.py migrate
python manage.py seed_demo   # optional

# 5. Before going live:
#    set DJANGO_DEBUG=False as a Vercel env var
```
</details>

---

## 🔑 Demo Logins

> Only available after running `python manage.py seed_demo`.

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin12345` |
| Support Agent | `agent.rios` | `agent12345` |
| Support Agent | `agent.chen` | `agent12345` |
| Employee | `j.doe` | `employee12345` |
| Employee | `s.patel` | `employee12345` |

---

## 📁 Project Layout

```
helpdeskx/
├── accounts/          # custom User model, auth, profile
├── tickets/            # Category, SLAPolicy, Ticket, comments, attachments, history, feedback
├── knowledgebase/       # searchable articles
├── dashboard/          # stats & reporting views
├── notifications/      # in-app notification model + service
├── templates/          # server-rendered HTML (Bootstrap + custom design system)
├── static/css/style.css
├── k8s/                 # Kubernetes manifests
├── terraform/           # infrastructure as code
├── Dockerfile
└── docker-compose.yml
```

---

## 🛠 Troubleshooting

<details>
<summary><code>OperationalError: unable to open database file</code></summary>

You're running on a read-only filesystem (Vercel, most serverless hosts) while still pointed at SQLite. Switch to an external Postgres — see [Option D above](#option-d--vercel-serverless).
</details>

<details>
<summary>Django's yellow debug page is showing in production</summary>

`DEBUG=True` leaks source code and settings to anyone who triggers an error. Set `DJANGO_DEBUG=False` as an environment variable once the app is working, and configure `ALLOWED_HOSTS` for your real domain.
</details>

<details>
<summary>Static files / CSS not loading after deploy</summary>

Run `python manage.py collectstatic --noinput` as part of your build step, and confirm `STATIC_URL` / `STATICFILES_DIRS` are set in `settings.py`.
</details>

<details>
<summary>Ticket attachments disappear after redeploy</summary>

On ephemeral hosts (Vercel, most serverless platforms) local file storage doesn't persist. Add `django-storages` with an S3-compatible bucket (e.g. Cloudflare R2) instead of local `MEDIA_ROOT`.
</details>

---

## ✅ Deployment Checklist

- [ ] Swapped SQLite for Postgres in `settings.py` (`DATABASE_URL` env var)
- [ ] `python manage.py migrate` run against the production database
- [ ] `DJANGO_DEBUG=False` set in production environment
- [ ] `ALLOWED_HOSTS` set to your real domain
- [ ] Media storage moved off local disk if hosting is ephemeral (S3 / R2)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Demo/seed data removed or replaced before real users sign up

---

## 🗺 Roadmap / Suggested Next Steps

- [ ] Wire `notifications/services.py` into an email backend or WebSocket layer for live push
- [ ] Add Celery + Redis for background SLA-escalation checks (auto-escalate overdue tickets)
- [ ] Add DRF serializers/viewsets over the existing models for a REST API layer
- [ ] Add automated tests for the ticket lifecycle transitions

---

## 📄 License

MIT — adapt as needed for your own deployment.
