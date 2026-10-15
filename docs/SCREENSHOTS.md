# Screenshot evidence

Every screenshot the grading rubric asks for, grouped by module. All were captured on 15 Oct 2026 from
real runs of this repository:

* **Browser and console screenshots** (the app, Swagger, Grafana, Prometheus, GitHub, AWS Console) are real
  browser captures. The AWS account ID is masked in the console screenshots.
* **Terminal screenshots** show the real output of the commands, captured during the run and rendered as
  a terminal window. Long build and plan logs are shortened where marked `[… N lines omitted …]`.
  Outputs labelled EKS were captured while the cluster was running, before `terraform destroy`.

---

## M1 · Application

| | |
|---|---|
| Dashboard (Docker Compose / minikube) | ![](screenshots/m1-app-dashboard.png) |
| Products page: search, filters, stock meters, actions | ![](screenshots/m1-app-products.png) |
| Stock ledger | ![](screenshots/m1-app-ledger.png) |
| Responsive phone layout | ![](screenshots/m1-app-mobile.png) |
| FastAPI Swagger `/docs` | ![](screenshots/m1-swagger-docs.png) |

## M2 · Testing: `pytest -v` (38 passed)

![pytest -v](screenshots/m2-pytest-v.png)

The same suite in CI, with the 85% coverage gate:

![pytest in GitHub Actions](screenshots/m5-pipeline-pytest-step.png)

## M3 · Git: commit history (30+ meaningful commits)

![GitHub commits](screenshots/m3-github-commits.png)

![git log](screenshots/m3-git-log.png)

## M4 · Docker: `docker compose up --build` and the app on http://localhost:3000

![docker compose up --build](screenshots/m4-docker-compose-up.png)

![browser at localhost:3000](screenshots/m4-browser-localhost-3000.png)

## M5 · CI/CD: green pipeline and GHCR images tagged with the commit SHA

![green pipeline](screenshots/m5-pipeline-green-run.png)

![GHCR backend](screenshots/m5-ghcr-backend-sha-tags.png)

![GHCR frontend](screenshots/m5-ghcr-frontend-sha-tags.png)

## M6 · DevSecOps: Trivy scan output from the pipeline

Both images: 0 fixable HIGH/CRITICAL vulnerabilities. See [SECURITY.md](SECURITY.md) for the 4 HIGH CVEs
found earlier and how they were fixed.

![Trivy backend](screenshots/m6-trivy-backend-pipeline.png)

![Trivy frontend](screenshots/m6-trivy-frontend-pipeline.png)

## M7 · Terraform: plan, AWS Console (ap-south-1), destroy

![terraform plan](screenshots/m7-terraform-plan.png)

![terraform plan resources](screenshots/m7-terraform-plan-resources.png)

| | |
|---|---|
| VPC `stockpilot-vpc` | ![](screenshots/m7-aws-vpc.png) |
| 2 public + 2 private subnets | ![](screenshots/m7-aws-subnets.png) |
| EKS cluster `stockpilot-eks` (Active, 1.35) | ![](screenshots/m7-aws-eks-cluster.png) |
| Managed node group: 2 nodes | ![](screenshots/m7-aws-eks-nodes.png) |

![terraform destroy](screenshots/m7-terraform-destroy.png)

![nothing left after destroy](screenshots/m7-post-destroy-audit.png)

## M8 · Kubernetes + Helm on EKS

![kubectl get pods/svc, helm list](screenshots/m8-eks-kubectl-pods-svc-helm.png)

The app through the Traefik Ingress and the AWS Network Load Balancer (UI shows `PRODUCTION` and the
running commit SHA):

![app on EKS](screenshots/m8-app-on-eks-via-loadbalancer.png)

![swagger on EKS](screenshots/m8-swagger-on-eks.png)

Horizontal Pod Autoscaler under load (2 → 3 → 4 replicas):

![HPA scaling](screenshots/m8-eks-hpa-scaling.png)

## M9 · Observability

![curl /metrics on EKS](screenshots/m9-curl-metrics.png)

![curl /metrics locally](screenshots/m9-curl-metrics-local.png)

Prometheus *Target health*: the StockPilot ServiceMonitor pool is **5/5 UP** (after the HPA scaled out):

![Prometheus targets](screenshots/m9-prometheus-targets.png)

Grafana *StockPilot / Overview* dashboard with live panels:

![Grafana dashboard](screenshots/m9-grafana-dashboard.png)

## M10 · Commit → pipeline → deployment update

The pipeline's deploy job runs `helm upgrade` with the new commit's images (here revision 5). The UI's
build badge then shows that commit SHA (compare M8).

![helm upgrade from CI](screenshots/m10-pipeline-helm-deploy.png)
