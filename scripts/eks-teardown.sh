#!/usr/bin/env bash
# Tear down everything on AWS, cleanly.
#
# Kubernetes creates two kinds of AWS resources that Terraform does not know about:
#   * the Network Load Balancer behind the Traefik Service (type LoadBalancer)
#   * the EBS volume behind the PostgreSQL PersistentVolumeClaim
# If they still exist, `terraform destroy` stalls on the VPC (the NLB's network interfaces
# keep the subnets busy) and the EBS volume keeps costing money. So delete them first.
set -euo pipefail
cd "$(dirname "$0")/.."

REGION="$(terraform -chdir=terraform output -raw region 2>/dev/null || echo ap-south-1)"
CLUSTER="$(terraform -chdir=terraform output -raw cluster_name 2>/dev/null || echo stockpilot-eks)"

if aws eks describe-cluster --region "$REGION" --name "$CLUSTER" >/dev/null 2>&1; then
  aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER" >/dev/null
  echo "==> removing app, PVCs and the load balancer"
  helm uninstall stockpilot -n stockpilot --wait 2>/dev/null || true
  kubectl delete pvc --all -n stockpilot --wait=true 2>/dev/null || true
  helm uninstall traefik -n traefik --wait 2>/dev/null || true
  helm uninstall kube-prometheus-stack -n monitoring --wait 2>/dev/null || true

  echo "==> waiting for the load balancer to disappear"
  for _ in $(seq 1 30); do
    remaining=$(aws elbv2 describe-load-balancers --region "$REGION" \
      --query "length(LoadBalancers[?contains(LoadBalancerName, 'traefik') || VpcId=='$(terraform -chdir=terraform output -raw vpc_id)'])" \
      --output text 2>/dev/null || echo 0)
    [[ "$remaining" == "0" ]] && break
    sleep 10
  done
fi

echo "==> terraform destroy"
terraform -chdir=terraform destroy -auto-approve -input=false

echo "==> leftover check (should be empty)"
aws ec2 describe-volumes --region "$REGION" --filters "Name=tag:kubernetes.io/cluster/${CLUSTER},Values=owned" \
  --query 'Volumes[].VolumeId' --output text
aws eks list-clusters --region "$REGION" --query 'clusters' --output text
echo "Teardown complete."
