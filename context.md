# StockPilot: project context

Working notes for anyone (or any AI assistant) picking this project up. Keep this file current: update the
**Current state** and **Change log** sections whenever something significant changes.

_Last updated: 15 Oct 2026_

## What this is

DevOps final capstone for Scaler School of Technology (SST). Deadline: **16 Oct 2026, 11:59 PM**, submitted
through the Google Form (Section B: https://forms.gle/pAuXQaokwVzhRzit6) with the SST email. Only one
submission counts.

The course reference project is TaskBoard (https://github.com/Nency-Ravaliya/devops-heros, folder
`session21-python`). The rubric requires **your own application domain** (a TaskBoard clone scores zero), so this is
**StockPilot**, an inventory management app. Grading is out of 100 across modules M1–M10; see
[docs/SUBMISSION.md](docs/SUBMISSION.md) for each criterion mapped to its evidence.

| | |
|---|---|
| Repository | https://github.com/Talin12/stockpilot (public) |
| Local path | `~/Projects/stockpilot` |
| Evidence folder (not in git) | `~/Projects/stockpilot-evidence/` (form answer sheet, screenshots zip, AWS logs) |
| Backup of pre-rewrite git history | `~/Projects/stockpilot-backup-before-rewrite.bundle` |
| Screenshots in repo | `docs/screenshots/` (33 PNGs, gallery in `docs/SCREENSHOTS.md`) |

## Current state (15 Oct 2026)

- **Code:** complete. 35 commits on `main`, all authored by the repo owner only. Claude attribution was removed
  from history on request; do **not** add `Co-Authored-By` or "generated with" lines to commits or PRs.
- **Tests:** 38 pytest tests pass, 96.56% coverage (CI gate is 85%).
- **CI/CD:** GitHub Actions is green. The latest verified run is
  https://github.com/Talin12/stockpilot/actions/runs/38704898446. Images are in GHCR, public and SHA-tagged.
- **AWS:** **nothing is running.** The EKS cluster was verified end to end, then destroyed with
  `terraform destroy` (60 resources). The repo variable `DEPLOY_ENABLED` is `false`, so the pipeline's deploy job is
  skipped.
- **Local:** Docker Compose stack and a minikube cluster (profile `stockpilot`) may still be running on the
  author's Mac. Stop them with `docker compose down` and `minikube stop -p stockpilot`.
- **Remaining step:** submit the Google Form. Everything needed is in `~/Projects/stockpilot-evidence/FORM-ANSWERS.md`
  and `stockpilot-screenshots.zip`. A live demo/presentation is still to be scheduled; re-create the cluster
  beforehand (see "Re-creating EKS").

## The application

Inventory management for a small warehouse: products, stock levels, reorder alerts, and an append-only ledger of
every receipt, shipment and adjustment.

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic (2 migrations: `products`, `stock_movements`).
  14 endpoints under `/api`, plus `/health` (liveness), `/ready` (DB-aware), `/metrics` (Prometheus).
  Business rule: shipping more than on-hand returns `409`. Stock quantity only changes through movements.
- **Frontend:** React 19 + Vite 8, plain CSS, responsive (tables become cards on phones). Served by
  `nginx-unprivileged` on port 8080; `/api` is proxied to the backend. The sidebar shows environment and the running
  commit SHA.
- **Database:** PostgreSQL 17.
- **Observability:** HTTP metrics via `prometheus-fastapi-instrumentator` plus business counters
  (`stockpilot_stock_movements_total`, etc.).

## Repository map

```text
backend/            FastAPI app (app/), Alembic migrations, tests (conftest.py + 5 modules), Dockerfile
frontend/           React app (src/), nginx/ templates, multi-stage Dockerfile
docker-compose.yml  postgres + backend + frontend, health-gated
.github/workflows/  ci-cd.yml (test, build, Trivy, push to GHCR, deploy to EKS)
terraform/          vpc.tf, eks.tf, github-oidc.tf, variables, outputs, tfvars example
helm/stockpilot/    chart: backend, frontend, postgres StatefulSet, ingress, HPA, PDBs, monitoring, Grafana dashboard
k8s/                namespace (restricted Pod Security), gp3 StorageClass, Traefik values
monitoring/         kube-prometheus-stack values
troubleshooting/    4 broken-on-purpose manifests + README
scripts/            minikube-up, eks-bootstrap, eks-teardown, install-addons, load-test, smoke-test, gen_dashboard.py
docs/               RUNBOOK, SECURITY, SUBMISSION, SCREENSHOTS, screenshots/
```

## Decisions and why

| Decision | Reason |
|---|---|
| Own domain (inventory) instead of TaskBoard | Rubric gives zero to a TaskBoard copy |
| **Traefik** ingress, not ingress-nginx | ingress-nginx was retired by Kubernetes SIG Network in March 2026 (no more security fixes) |
| All GitHub Actions pinned to full commit SHAs; Trivy action v0.36.0 | `trivy-action` tags were hijacked in March 2026 (CVE-2026-33634) |
| `pip` removed from the runtime image | Trivy flagged 4 HIGH CVEs in pip's vendored urllib3/msgpack/setuptools |
| EKS 1.35, nodes 2 × `m7i-flex.large` | 1.33 is out of standard support (6× price); the AWS Free plan rejects `t3.medium` and has a 5 vCPU quota |
| CI deploys via GitHub **OIDC**, no stored AWS keys | Safer than long-lived secrets; the role trusts only this repo's `main` / `production` |
| OIDC trust uses GitHub's **immutable** subject claim (`repo:Talin12@186754467/stockpilot@1420236630`) | New repos issue tokens with IDs; the plain `repo:Owner/name` form is rejected |
| `preStop` sleep (5s) on backend and frontend | Without it, rolling updates dropped ~0.9% of requests under load; now 0 errors |
| DB password generated by Helm, kept across upgrades | No secrets in Git |
| Project lives in `~/Projects`, not Desktop | Desktop syncs to iCloud, and macOS evicted git objects ("dataless" files, reads time out) |

## Environment facts and gotchas

- **AWS:** Free-plan account, region `ap-south-1`. CLI auth uses `aws login --profile stockpilot` (short-lived credentials);
  set `AWS_PROFILE=stockpilot` and `AWS_REGION=ap-south-1`. The account was signed in as root; prefer an IAM user + MFA.
  A cluster costs about $0.36/hour; always run `./scripts/eks-teardown.sh` afterwards.
- **macOS DNS** can negatively cache an AWS hostname ("no such host") for ~20 seconds. Retry rather than debug.
- **VPC CNI leaks ENIs** (`aws-K8S-i-*`) when nodes terminate, stalling subnet deletion; the teardown script removes them.
- **`minikube image build`** exits 0 even when the build fails; `minikube-up.sh` verifies the images exist.
- **zsh:** `$c:l` is a lowercase modifier; write `${c}` in scripts.
- **Docker Hub** may be unreachable from minikube; the Pending lab uses `registry.k8s.io/pause`.
- **Free-plan nodes:** a `t3.medium` node group sits in CREATING forever; the real error is in the Auto Scaling activity history.

## Re-creating EKS (for the live demo)

Full detail in [docs/RUNBOOK.md](docs/RUNBOOK.md). Short version (~25 minutes):

```bash
aws login --profile stockpilot --region ap-south-1 && export AWS_PROFILE=stockpilot AWS_REGION=ap-south-1
cd terraform && terraform init && terraform apply && cd ..          # ~15-20 min
SHA=$(gh run list --branch main --status success --limit 1 --json headSha -q '.[0].headSha')
./scripts/eks-bootstrap.sh "$SHA"                                   # add-ons + app + load balancer URL
gh variable set DEPLOY_ENABLED --body true                          # turn CD back on
gh variable set APP_URL --body "http://<load-balancer-dns>"
```

The GitHub repo variables `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION` and `EKS_CLUSTER_NAME` were set for the old cluster. The role
ARN stays the same only if Terraform re-creates the same role name (it does: `stockpilot-eks-github-deploy`).
After the demo: `./scripts/eks-teardown.sh` and `gh variable set DEPLOY_ENABLED --body false`.

## Useful commands

```bash
# local stack
docker compose up --build                       # http://localhost:3000, API docs on :8000/docs
BASE_URL=http://localhost:3000 ./scripts/smoke-test.sh
cd backend && source .venv/bin/activate && pytest -v

# local Kubernetes
./scripts/minikube-up.sh && minikube tunnel -p stockpilot    # then add 127.0.0.1 stockpilot.local to /etc/hosts

# pipeline
gh run list --limit 5
gh run view <id> --log-failed
```

## Verification history

Done on 15 Oct 2026 (details in [docs/SUBMISSION.md](docs/SUBMISSION.md)): pytest, Compose + smoke test, Trivy, Helm on minikube
(incl. HPA 2→5 and `helm test`), Prometheus 5/5 targets UP, Grafana dashboard, Terraform apply/destroy on AWS, a CI-driven deploy to EKS,
HPA 2→4 under load via the load balancer, a rolling restart under load with 0 errors, all 4 troubleshooting scenarios and their fixes.

## Change log

| Date | Change |
|---|---|
| 14 Oct 2026 | Project created; backend, frontend, Docker, Terraform, Helm, CI, monitoring, troubleshooting lab |
| 15 Oct 2026 | Verified on minikube and EKS; fixed Trivy findings, OIDC trust, node sizing, preStop; EKS destroyed |
| 15 Oct 2026 | Added README, runbook, security notes, submission checklist and 33 screenshots |
| 15 Oct 2026 | Removed Claude attribution from git history (force-push); refreshed affected screenshots; added this file |

## Open items

- [ ] Submit the Google Form (Section B) with the SST email
- [ ] Schedule the live demo and re-create the cluster beforehand
- [ ] Optional: delete old GHCR package versions tagged with pre-rewrite SHAs
- [ ] Optional: replace root AWS sign-in with an IAM user + MFA
