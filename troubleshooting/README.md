# Troubleshooting lab

Four deliberately broken manifests, one per common Kubernetes failure. Each is
isolated (prefixed `lab-`, labelled `lab=troubleshooting`) and does not touch the real app.

Clean up everything at once:

```bash
kubectl delete -n stockpilot deploy,svc -l lab=troubleshooting
```

---

## 1. ImagePullBackOff (wrong image tag)

```bash
kubectl apply -f troubleshooting/01-broken-image.yaml
kubectl get pods -n stockpilot -l app=lab-broken-image        # ErrImagePull -> ImagePullBackOff
kubectl describe pod -n stockpilot -l app=lab-broken-image    # Events: "manifest unknown" / "not found"
kubectl get events -n stockpilot --sort-by=.lastTimestamp | tail
```

**Root cause:** the tag `this-tag-does-not-exist` was never pushed. In CI the tag is always the commit SHA
that was just pushed, which is why `latest`-style guessing is avoided.

**Fix:** point the Deployment at a tag that exists in GHCR:

```bash
kubectl set image deploy/lab-broken-image -n stockpilot backend=ghcr.io/<owner>/stockpilot-backend:<sha>
```

## 2. Service with no endpoints (label selector / port mismatch)

```bash
kubectl apply -f troubleshooting/02-broken-service.yaml
kubectl get svc,endpointslices -n stockpilot                  # lab-broken-service has no endpoints
kubectl get pods -n stockpilot --show-labels | grep backend   # real label: app.kubernetes.io/name=stockpilot-backend
kubectl run curl -n stockpilot --rm -it --restart=Never --image=curlimages/curl \
  --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":100,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"curl","image":"curlimages/curl","args":["-sv","--max-time","3","http://lab-broken-service:8000/health"],"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}}}]}}'
```

**Root cause:** a Service routes to Pods whose labels match its `selector`. No match means no
endpoints, so no traffic, even though every Pod is healthy. The `targetPort` (8080) is also wrong.

**Fix:**

```bash
kubectl patch svc lab-broken-service -n stockpilot --type merge \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"stockpilot-backend"},"ports":[{"name":"http","port":8000,"targetPort":8000}]}}'
kubectl get endpointslices -n stockpilot -l kubernetes.io/service-name=lab-broken-service
```

## 3. CrashLoopBackOff (bad configuration)

```bash
kubectl apply -f troubleshooting/03-crashloop-bad-database-url.yaml
kubectl get pods -n stockpilot -l app=lab-crashloop -w        # Running -> Error -> CrashLoopBackOff
kubectl logs -n stockpilot deploy/lab-crashloop               # "database not ready (n/30) ... failed to resolve host"
kubectl logs -n stockpilot deploy/lab-crashloop --previous    # logs of the last crashed container
```

**Root cause:** `DATABASE_URL` points to a host that does not exist. The container exits with code 1,
and the kubelet restarts it with exponential back-off.

**Fix:** use the real connection string from the release's Secret:

```bash
kubectl set env deploy/lab-crashloop -n stockpilot --from=secret/stockpilot-db --keys=DATABASE_URL
```

## 4. Pending (unschedulable)

```bash
kubectl apply -f troubleshooting/04-pending-unschedulable.yaml
kubectl get pods -n stockpilot -l app=lab-pending              # Pending forever
kubectl describe pod -n stockpilot -l app=lab-pending          # "0/N nodes are available: Insufficient cpu, Insufficient memory"
kubectl describe nodes | grep -A6 "Allocated resources"
```

**Root cause:** requests (64 CPU, 256Gi) exceed every node's allocatable capacity.

**Fix:** lower the requests (or add bigger nodes via Terraform `node_instance_types`):

```bash
kubectl set resources deploy/lab-pending -n stockpilot --requests=cpu=50m,memory=64Mi
```

---

## General triage order

```text
kubectl get pods            -> which state? (Pending / ImagePullBackOff / CrashLoopBackOff / Running-not-Ready)
kubectl describe pod <pod>  -> Events at the bottom explain scheduling, pulling and probe failures
kubectl logs <pod> [--previous]
kubectl get events --sort-by=.lastTimestamp
kubectl get svc,endpointslices  -> is the Service actually selecting Pods?
```
