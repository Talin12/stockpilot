# Submission checklist: rubric → evidence

Repository: **https://github.com/Talin12/stockpilot** (public)

Legend: ✅ in the repo / verified · 📸 screenshot in [`docs/screenshots/`](screenshots) (gallery: [SCREENSHOTS.md](SCREENSHOTS.md)) · 🎤 show live

## M1 Application: frontend + backend + database (10)

| Criterion | Evidence |
|-----------|----------|
| FastAPI starts, `/health` responds | ✅ `backend/app/main.py`; `curl localhost:8000/health` → `{"status":"UP"}` |
| ≥ 4 REST endpoints (GET/POST/PUT/DELETE) | ✅ 14 endpoints, see the [README API table](../README.md#rest-api) and `/docs` |
| PostgreSQL table via Alembic | ✅ `backend/alembic/versions/0001_create_products.py`, `0002_create_stock_movements.py` |
| Frontend renders and calls the API | ✅ `frontend/src/api.js`; 📸 `m1-app-dashboard.png` |
| Responsive, usable UI | ✅ 📸 `m1-app-products.png` (desktop), `m1-app-mobile.png` (phone layout) |

## M2 Testing (10)

| Criterion | Evidence |
|-----------|----------|
| pytest runs without errors | ✅ 38 passed; 📸 `m2-pytest-v.png`, `m5-pipeline-pytest-step.png` |
| ≥ 5 tests over ≥ 3 endpoints | ✅ 38 tests over all endpoints (`tests/test_*.py`) |
| Test DB / mock, not production | ✅ `tests/conftest.py`: in-memory SQLite per test, `dependency_overrides[get_db]` |
| `pytest.ini` / `conftest.py` | ✅ both present |

## M3 Git and GitHub (5)

| Criterion | Evidence |
|-----------|----------|
| Public repository | ✅ github.com/Talin12/stockpilot |
| Meaningful commit messages | ✅ Conventional-commit style (`feat(backend): …`, `fix(docker): …`); 📸 `m3-github-commits.png`, `m3-git-log.png` (30+ commits) |
| `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | ✅ root `.gitignore` |

## M4 Docker (10)

| Criterion | Evidence |
|-----------|----------|
| `backend/Dockerfile` builds | ✅ multi-stage, venv copied into a slim runtime |
| `frontend/Dockerfile` multi-stage (Node → Nginx) | ✅ `node:22-alpine` build → `nginx-unprivileged` runtime |
| Non-root users | ✅ backend uid 10001, frontend uid 101 (`docker compose exec backend id`) |
| `docker compose up --build` starts all 3 | ✅ health-gated startup; 📸 `m4-docker-compose-up.png`, `m4-browser-localhost-3000.png` |

## M5 CI/CD (15)

| Criterion | Evidence |
|-----------|----------|
| Workflow present | ✅ `.github/workflows/ci-cd.yml` |
| Triggers on push to `main` | ✅ `on.push.branches: [main]` (plus PRs and manual) |
| pytest gates the build | ✅ `build-scan-push` `needs: backend-tests` |
| Frontend built in the pipeline | ✅ `frontend-build` job (`npm ci && npm run build`) |
| Images built for both | ✅ matrix `[backend, frontend]` |
| Pushed to GHCR | ✅ `ghcr.io/talin12/stockpilot-backend`, `…-frontend` |
| SHA tags, not `latest` | ✅ `:${{ github.sha }}`; the chart refuses an empty tag |
| | 📸 `m5-pipeline-green-run.png` · `m5-ghcr-backend-sha-tags.png` · `m5-ghcr-frontend-sha-tags.png` |

## M6 DevSecOps: Trivy (5)

| Criterion | Evidence |
|-----------|----------|
| Trivy on both images | ✅ *Trivy scan* step in the matrix job |
| Fails on HIGH/CRITICAL | ✅ `severity: HIGH,CRITICAL`, `exit-code: "1"` |
| Explain a CVE / clean result | ✅ [docs/SECURITY.md](SECURITY.md): 4 HIGH CVEs found in pip's vendored urllib3/msgpack/setuptools, fixed by removing pip from the runtime image |
| | 📸 `m6-trivy-backend-pipeline.png` · `m6-trivy-frontend-pipeline.png` |

## M7 Terraform (15)

| Criterion | Evidence |
|-----------|----------|
| Valid HCL in `terraform/` | ✅ `terraform validate` runs in CI (`infra-lint`) |
| `terraform init` OK | ✅ |
| `terraform plan` non-empty | ✅ `Plan: 60 to add`; 📸 `m7-terraform-plan.png`, `m7-terraform-plan-resources.png` |
| VPC with ≥ 2 public subnets | ✅ `vpc.tf` (2 public + 2 private); 📸 `m7-aws-vpc.png`, `m7-aws-subnets.png` |
| EKS with a node group | ✅ `eks.tf` (`eks_managed_node_groups.default`); 📸 `m7-aws-eks-cluster.png`, `m7-aws-eks-nodes.png` |
| `terraform destroy` clean | ✅ `scripts/eks-teardown.sh`; 📸 `m7-terraform-destroy.png`, `m7-post-destroy-audit.png` |
| `terraform.tfvars.example`, no credentials | ✅ present; CLI uses `aws login`, CI uses OIDC |

## M8 Kubernetes + Helm (15)

| Criterion | Evidence |
|-----------|----------|
| `k8s/namespace.yaml` | ✅ (+ restricted Pod Security labels) |
| Helm chart (`Chart.yaml`, `values.yaml`, templates) | ✅ `helm/stockpilot/` |
| `helm upgrade --install` works | ✅ verified on minikube and EKS |
| ≥ 2 replicas backend + frontend | ✅ 2 each (backend HPA 2–6) |
| ClusterIP Services | ✅ `stockpilot-backend`, `stockpilot-frontend`, `stockpilot-postgres` |
| Ingress `/` → frontend, `/api` → backend | ✅ `templates/ingress.yaml` |
| All pods Running | 📸 `m8-eks-kubectl-pods-svc-helm.png` |
| | 📸 svc + `helm list` in `m8-eks-kubectl-pods-svc-helm.png` · `m8-app-on-eks-via-loadbalancer.png` · `m8-eks-hpa-scaling.png` |

## M9 Observability (10)

| Criterion | Evidence |
|-----------|----------|
| `/metrics` Prometheus format | ✅ 📸 `m9-curl-metrics.png`, `m9-curl-metrics-local.png` |
| Prometheus scraping the app | ✅ ServiceMonitor; 📸 `m9-prometheus-targets.png` (5/5 UP) |
| Grafana accessible | ✅ kube-prometheus-stack |
| Live panel (requests / latency / errors) | ✅ 📸 `m9-grafana-dashboard.png` |

## M10 Presentation + documentation (5)

| Criterion | Evidence |
|-----------|----------|
| Root README explains the app | ✅ `README.md` |
| Live demo: commit → pipeline → deployment update | 📸 `m10-pipeline-helm-deploy.png` · 🎤 [RUNBOOK §8](RUNBOOK.md#8-live-demo-script-final-presentation): the UI shows the running commit SHA, so the update is visible |

---

## Google Form reminders

* Use your **SST email ID**. Only one submission counts, so double-check every link opens in a private window.
* Repository: `https://github.com/Talin12/stockpilot`
* Successful pipeline: `https://github.com/Talin12/stockpilot/actions` (pick the latest green run)
* Packages: `https://github.com/Talin12?tab=packages`

## Verification log (15 Oct 2026)

What was actually run end to end before submission:

| Check | Result |
|-------|--------|
| `pytest -v` (Python 3.13 container, same as CI) | 38 passed, 96% coverage |
| `docker compose up --build` + `scripts/smoke-test.sh` | all checks passed; containers run as uid 10001 / 101 |
| Trivy v0.75.0, HIGH/CRITICAL, fixable only | backend 4 HIGH → fixed → 0; frontend 0 |
| GitHub Actions on `main` | green: test → build → Trivy → GHCR push → EKS deploy (OIDC, no stored AWS keys) |
| minikube: Helm install, Traefik Ingress, `helm test` | all Pods Running under the restricted Pod Security Standard; Ingress routes `/`, `/api`, `/docs` |
| minikube HPA under 230 req/s | 2 → 4 → 5 replicas, 0 errors in 34,487 requests |
| Prometheus | `serviceMonitor/stockpilot/stockpilot-backend/0`: 5/5 targets UP; alert rules loaded |
| Terraform on AWS (ap-south-1) | VPC + 4 subnets + EKS 1.35 + 2 × m7i-flex.large nodes + 6 add-ons |
| EKS: CI deploy of a UI change | `helm history` shows a new revision; the UI shows the new commit SHA |
| EKS HPA under load via the NLB | 2 → 3 → 4 replicas, settling at the 60% CPU target |
| EKS rolling restart under load (after the preStop fix) | 0 errors in 5,481 requests |
| Troubleshooting lab | all 4 scenarios reproduce the intended failure, and each documented fix resolves it |
