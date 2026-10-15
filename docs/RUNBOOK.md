# StockPilot runbook

Exact commands for every stage of the capstone: AWS infrastructure, deployment, continuous delivery,
the live demo, and teardown. All commands run from the repository root.

* [0. Tools](#0-tools)
* [1. AWS credentials (no long-lived keys)](#1-aws-credentials-no-long-lived-keys)
* [2. Provision VPC + EKS with Terraform](#2-provision-vpc--eks-with-terraform)
* [3. Bootstrap the cluster and deploy](#3-bootstrap-the-cluster-and-deploy)
* [4. Open the app, Grafana and Prometheus](#4-open-the-app-grafana-and-prometheus)
* [5. Autoscaling demo](#5-autoscaling-demo)
* [6. Troubleshooting demo](#6-troubleshooting-demo)
* [7. Enable continuous deployment](#7-enable-continuous-deployment)
* [8. Live demo script (final presentation)](#8-live-demo-script-final-presentation)
* [9. Teardown, every time](#9-teardown-every-time)
* [10. Local Kubernetes alternative (minikube)](#10-local-kubernetes-alternative-minikube)

---

## 0. Tools

| Tool | Tested with |
|------|-------------|
| Docker Desktop | 28.4 |
| AWS CLI v2 | 2.37 (`aws login` needs ≥ 2.32) |
| Terraform | 1.16 |
| kubectl | 1.37 |
| Helm | 4.3 |
| minikube (optional) | 1.39 |
| gh (GitHub CLI) | any recent |

## 1. AWS credentials (no long-lived keys)

```bash
aws login --profile stockpilot --region ap-south-1   # opens the browser; sign in to the AWS console
export AWS_PROFILE=stockpilot
aws sts get-caller-identity
```

`aws login` exchanges your console session for temporary credentials that refresh automatically,
so no access key is ever written to disk. For day-to-day work, sign in as an IAM user or IAM Identity
Center user rather than the root user, and enable MFA on root.

## 2. Provision VPC + EKS with Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # defaults: ap-south-1, EKS 1.35, 3 x t3.medium
terraform init
terraform plan -out tfplan                       # expect: Plan: 60 to add, 0 to change, 0 to destroy
terraform apply tfplan                           # ~15-20 minutes
terraform output
cd ..
```

What gets created: VPC (2 public and 2 private subnets in 2 AZs), internet gateway, single NAT gateway,
route tables, the EKS 1.35 control plane, a managed node group (AL2023), the add-ons (VPC CNI, CoreDNS,
kube-proxy, EBS CSI, metrics-server, Pod Identity Agent), IAM roles, and the GitHub OIDC provider and
deploy role.

**Approximate cost while running (ap-south-1):**

| Item | ~USD/hour |
|------|-----------|
| EKS control plane | 0.10 |
| 3 × t3.medium on-demand | 0.13 |
| NAT gateway (+ data) | 0.06 |
| Network Load Balancer | 0.03 |
| EBS (gp3 5 GiB + node disks) | < 0.01 |
| **Total** | **≈ 0.32 / hour (≈ $7.70 / day)** |

📸 **Screenshots for M7:** the `terraform plan` output; AWS Console → VPC → *Your VPCs* (`stockpilot-vpc`)
and *Subnets*; AWS Console → EKS → *Clusters* → `stockpilot-eks` (Compute tab shows the node group),
with the region **Asia Pacific (Mumbai)** visible.

## 3. Bootstrap the cluster and deploy

Use an image tag that CI has already pushed (any green run on `main`):

```bash
SHA=$(gh run list --branch main --status success --limit 1 --json headSha -q '.[0].headSha')
./scripts/eks-bootstrap.sh "$SHA"
```

The script:

1. runs `aws eks update-kubeconfig`;
2. applies `k8s/namespace.yaml` (restricted Pod Security) and `k8s/storageclass-gp3.yaml`;
3. installs kube-prometheus-stack (Prometheus and Grafana) and Traefik (internet-facing NLB);
4. installs the StockPilot Helm release with `values-prod.yaml` and the given SHA as the image tag;
5. prints the load balancer URL.

```bash
kubectl get nodes -o wide
kubectl get pods -n stockpilot -o wide    # 2 backend, 2 frontend, 1 postgres, all Running
kubectl get svc -n stockpilot             # three ClusterIP services
kubectl get ingress,hpa -n stockpilot
helm list -n stockpilot
helm test stockpilot -n stockpilot        # in-cluster smoke test
```

📸 **Screenshots for M8:** `kubectl get pods -n stockpilot`, `kubectl get svc -n stockpilot`,
`helm list -n stockpilot`, and the browser on the load balancer URL.

## 4. Open the app, Grafana and Prometheus

```bash
# App (through Traefik Ingress + NLB)
LB=$(kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
open "http://$LB/"            # UI
open "http://$LB/docs"        # Swagger
BASE_URL="http://$LB" ./scripts/smoke-test.sh

# Backend metrics
kubectl port-forward -n stockpilot svc/stockpilot-backend 8000:8000 &
curl -s localhost:8000/metrics | grep -E "^(http_requests_total|stockpilot_)" | head

# Prometheus  ->  http://localhost:9090/targets  (pool serviceMonitor/stockpilot/stockpilot-backend/0 = UP)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 &

# Grafana  ->  http://localhost:3001  (user admin)  ->  Dashboards -> "StockPilot / Overview"
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80 &
```

📸 **Screenshots for M9:** `curl …/metrics`, the Prometheus *Target health* page filtered to
`stockpilot-backend` showing **UP**, and the Grafana dashboard with live panels (run section 5 first so
the graphs move).

## 5. Autoscaling demo

```bash
kubectl get hpa -n stockpilot -w            # terminal 1
URL="http://$LB" DURATION=180 CONCURRENCY=40 ./scripts/load-test.sh   # terminal 2
kubectl top pods -n stockpilot              # terminal 3
```

Expected: CPU climbs well above the 60% target, and replicas go 2 → 4 → 6 within about a minute. About
a minute after the load stops, the HPA scales back down one Pod every 30 seconds.

## 6. Troubleshooting demo

See [troubleshooting/README.md](../troubleshooting/README.md): four scenarios (ImagePullBackOff,
Service without endpoints, CrashLoopBackOff, Pending), each with diagnosis commands and a one-line fix.
On EKS, change the image in `03-crashloop-bad-database-url.yaml` to your GHCR image
(`ghcr.io/talin12/stockpilot-backend:<sha>`).

## 7. Enable continuous deployment

The `deploy` job authenticates to AWS with **GitHub OIDC**: GitHub issues a short-lived token, and AWS
STS exchanges it for 1-hour credentials of the role Terraform created. No AWS secrets live in GitHub.

```bash
gh variable set AWS_DEPLOY_ROLE_ARN --body "$(terraform -chdir=terraform output -raw github_actions_role_arn)"
gh variable set AWS_REGION        --body ap-south-1
gh variable set EKS_CLUSTER_NAME  --body stockpilot-eks
gh variable set APP_URL           --body "http://$LB"
gh variable set DEPLOY_ENABLED    --body true
```

From now on, every push to `main` runs test → build → Trivy → push → `helm upgrade` with the new SHA.
To pause deployments (for example after teardown): `gh variable set DEPLOY_ENABLED --body false`.

## 8. Live demo script (final presentation)

| # | Show | Command / action |
|---|------|------------------|
| 1 | **Application** | Open `http://$LB/`, create a product, receive and ship stock, show the ledger |
| 2 | **API** | `http://$LB/docs`: try `GET /api/products`, `POST /api/products/{id}/movements` |
| 3 | **Database** | `kubectl exec -it -n stockpilot stockpilot-postgres-0 -- psql -U stockpilot -d stockpilot -c 'select sku, name, quantity from products order by id;'` and `\dt` |
| 4 | **Git** | Make a visible change, e.g. edit `brand-sub` text in `frontend/src/components/Sidebar.jsx`; `git commit -am "feat(ui): ..."` |
| 5 | **CI** | `git push`, then open the Actions tab: tests → frontend build → Terraform/Helm lint |
| 6 | **Docker** | Show the *Image · backend/frontend* jobs and both Dockerfiles (multi-stage, non-root) |
| 7 | **Security** | Expand *Trivy scan* in the job log, or the job summary table |
| 8 | **Registry** | GitHub profile → Packages → `stockpilot-backend`: the tag equals the commit SHA |
| 9 | **Terraform** | Walk through `terraform/vpc.tf`, `eks.tf`, `github-oidc.tf`; `terraform state list` |
| 10 | **Kubernetes** | `kubectl get pods,svc -n stockpilot` |
| 11 | **Helm** | `helm list -n stockpilot`, `helm history stockpilot -n stockpilot` (new revision per deploy) |
| 12 | **Ingress** | Reload `http://$LB/`: the sidebar shows the **new commit SHA** and your change |
| 13 | **HPA** | Section 5 |
| 14 | **Monitoring** | Prometheus targets UP, Grafana *StockPilot / Overview* during the load test |
| 15 | **Failure simulation** | Section 6, e.g. `kubectl apply -f troubleshooting/02-broken-service.yaml`, then diagnose and fix |

Rollback demo: `helm rollback stockpilot <previous-revision> -n stockpilot`, and the UI's SHA changes back.

## 9. Teardown, every time

```bash
./scripts/eks-teardown.sh
gh variable set DEPLOY_ENABLED --body false
```

The script deletes the Kubernetes-created AWS resources first (the Traefik NLB and the PostgreSQL EBS
volume, which Terraform doesn't track and which would otherwise block VPC deletion), then runs
`terraform destroy -auto-approve`, and finally checks that nothing was left behind.

📸 **Screenshot for M7:** the final `Destroy complete! Resources: 60 destroyed.` line.

## 10. Local Kubernetes alternative (minikube)

Everything except Terraform works locally at zero cost. It's useful for rehearsing.

```bash
./scripts/minikube-up.sh                     # ~10 minutes the first time
minikube tunnel -p stockpilot                # separate terminal (asks for sudo, exposes port 80)
echo "127.0.0.1 stockpilot.local" | sudo tee -a /etc/hosts
open http://stockpilot.local
URL=http://stockpilot.local ./scripts/load-test.sh
minikube delete -p stockpilot                # remove it all
```
