#!/usr/bin/env bash
# Local Kubernetes environment that mirrors the EKS setup:
# minikube + metrics-server + kube-prometheus-stack + Traefik + the StockPilot Helm release.
#
#   ./scripts/minikube-up.sh           # create/refresh everything
#   minikube tunnel -p stockpilot      # (separate terminal) exposes Traefik on 127.0.0.1:80
#   echo "127.0.0.1 stockpilot.local" | sudo tee -a /etc/hosts
#   open http://stockpilot.local
set -euo pipefail
cd "$(dirname "$0")/.."

PROFILE="${MINIKUBE_PROFILE:-stockpilot}"
CPUS="${MINIKUBE_CPUS:-4}"
MEMORY="${MINIKUBE_MEMORY:-5g}"

echo "==> minikube profile '${PROFILE}' (${CPUS} CPU, ${MEMORY})"
if ! minikube status -p "$PROFILE" >/dev/null 2>&1; then
  minikube start -p "$PROFILE" --driver=docker --cpus="$CPUS" --memory="$MEMORY"
fi
kubectl config use-context "$PROFILE" >/dev/null
minikube -p "$PROFILE" addons enable metrics-server

echo "==> building images inside minikube (no registry needed)"
for component in backend frontend; do
  minikube -p "$PROFILE" image build -t "stockpilot-${component}:local" "$component"
  # `minikube image build` can exit 0 even when the build fails, so verify the result.
  minikube -p "$PROFILE" image ls | grep -q "stockpilot-${component}:local" \
    || { echo "ERROR: stockpilot-${component}:local was not built" >&2; exit 1; }
done

./scripts/install-addons.sh

echo "==> StockPilot"
kubectl apply -f k8s/namespace.yaml
helm upgrade --install stockpilot helm/stockpilot \
  --namespace stockpilot \
  -f helm/stockpilot/values-dev.yaml \
  --set backend.image.tag=local --set frontend.image.tag=local \
  --wait --timeout 10m

kubectl get pods,svc,ingress,hpa -n stockpilot
cat <<EOF

Done. Next:
  1. In another terminal:   minikube tunnel -p ${PROFILE}
  2. Map the hostname once: echo "127.0.0.1 stockpilot.local" | sudo tee -a /etc/hosts
  3. App:      http://stockpilot.local          Swagger: http://stockpilot.local/docs
  4. Grafana:  kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
               password: kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
  5. Prometheus targets: kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
EOF
