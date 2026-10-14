#!/usr/bin/env bash
# One-time preparation of the EKS cluster created by Terraform, then a first deploy.
# Prereqs: `terraform apply` finished, AWS credentials configured, images pushed to GHCR by CI.
#
#   ./scripts/eks-bootstrap.sh <image-tag>     # image-tag = a commit SHA that CI pushed
set -euo pipefail
cd "$(dirname "$0")/.."

TAG="${1:?usage: eks-bootstrap.sh <image tag (git commit SHA pushed by CI)>}"
OWNER="${GHCR_OWNER:-$(gh repo view --json owner -q .owner.login 2>/dev/null | tr '[:upper:]' '[:lower:]')}"
REGION="$(terraform -chdir=terraform output -raw region)"
CLUSTER="$(terraform -chdir=terraform output -raw cluster_name)"

echo "==> kubeconfig for ${CLUSTER} (${REGION})"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER"

echo "==> bootstrap manifests"
kubectl apply -f k8s/namespace.yaml -f k8s/storageclass-gp3.yaml

./scripts/install-addons.sh --eks

echo "==> StockPilot ${OWNER}:${TAG}"
helm upgrade --install stockpilot helm/stockpilot \
  --namespace stockpilot \
  -f helm/stockpilot/values-prod.yaml \
  --set backend.image.repository="ghcr.io/${OWNER}/stockpilot-backend" \
  --set frontend.image.repository="ghcr.io/${OWNER}/stockpilot-frontend" \
  --set backend.image.tag="$TAG" --set frontend.image.tag="$TAG" \
  --rollback-on-failure --wait --timeout 10m

kubectl get pods,svc,ingress,hpa -n stockpilot
LB="$(kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
echo
echo "App URL (DNS can take 1-3 minutes to resolve): http://${LB}/"
