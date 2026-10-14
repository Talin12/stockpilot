#!/usr/bin/env bash
# Install the cluster add-ons StockPilot relies on, into whatever cluster kubectl points at:
#   1. kube-prometheus-stack (Prometheus Operator, Prometheus, Grafana)  -> namespace monitoring
#   2. Traefik ingress controller                                        -> namespace traefik
# Usage: scripts/install-addons.sh [--eks]
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/versions.env

traefik_overlay=()
if [[ "${1:-}" == "--eks" ]]; then
  traefik_overlay=(-f k8s/traefik-values-eks.yaml)
fi

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo update prometheus-community traefik >/dev/null

echo "==> kube-prometheus-stack ${KUBE_PROMETHEUS_STACK_VERSION}"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --version "${KUBE_PROMETHEUS_STACK_VERSION}" \
  --namespace monitoring --create-namespace \
  -f monitoring/kube-prometheus-stack-values.yaml \
  --wait --timeout 15m

# Installed after Prometheus so its ServiceMonitor CRD already exists.
echo "==> traefik ${TRAEFIK_CHART_VERSION}"
helm upgrade --install traefik traefik/traefik \
  --version "${TRAEFIK_CHART_VERSION}" \
  --namespace traefik --create-namespace \
  -f k8s/traefik-values.yaml ${traefik_overlay[@]+"${traefik_overlay[@]}"} \
  --wait --timeout 10m

if ! kubectl get apiservice v1beta1.metrics.k8s.io >/dev/null 2>&1; then
  echo "WARNING: metrics-server is missing - the HPA will show <unknown> targets." >&2
  echo "         minikube: minikube addons enable metrics-server | EKS: Terraform installs it." >&2
fi
echo "Add-ons ready."
