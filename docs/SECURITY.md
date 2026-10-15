# Security notes

## Trivy image scanning (M6)

**What Trivy scans.** In every pipeline run, Trivy inspects both container images before they are
pushed to GHCR. That covers the OS packages (Debian 13 for the backend, Alpine 3.23 for the frontend)
and every language dependency it can find (the Python packages in `/opt/venv`). Each one is checked
against vulnerability databases. The gate is
`severity: HIGH,CRITICAL`, `ignore-unfixed: true`, `exit-code: 1`: any HIGH or CRITICAL CVE that already
has a fixed version available fails the job, and the image is never pushed.

**What it found and what we did.** The first local scan of the backend image failed with
**4 HIGH findings** while the frontend image was clean:

| Package | Installed | Fixed in | Advisory | Issue |
|---------|-----------|----------|----------|-------|
| urllib3 | 2.7.0 | 2.8.0 | CVE-2026-97687 | Traffic interception via HTTPS proxy TLS configuration override |
| urllib3 | 2.7.0 | 2.8.0 | CVE-2026-97689 | Denial of service via unbounded memory allocation in the chunk parser |
| msgpack | 1.1.2 | 1.2.1 | GHSA-6v7p-g79w-8964 | Out-of-bounds read / crash on Unpacker reuse |
| setuptools | 70.3.0 | 78.1.1 | CVE-2025-47273 | Path traversal in `PackageIndex` |

None of these are StockPilot dependencies. They are copies **vendored inside pip itself**
(`pip/_vendor/`), which ended up in the runtime image because the virtualenv was created with pip.
pip is only needed while building, so the build stage now runs `pip uninstall -y pip` before the venv is
copied into the runtime stage (commit `fix(docker): drop pip from runtime venv…`).

**Result:** both images now scan clean (0 fixable HIGH/CRITICAL), and every CI run publishes the Trivy
table in the job summary. A clean result means no *known, fixable* HIGH or CRITICAL vulnerabilities
right now. It is not a guarantee: new CVEs are published daily, `ignore-unfixed` hides issues that
have no patch yet, and Trivy does not test the app's own code. That is why it is one layer among several.

**Supply-chain note.** In March 2026, attackers repointed most `aquasecurity/trivy-action` version tags
at credential-stealing code (CVE-2026-33634). This pipeline therefore pins **every** action to a full commit
SHA (`aquasecurity/trivy-action@ed142fd…  # v0.36.0`, released after the incident) and pins the Trivy
binary version (`v0.75.0`).

## Security layers in this project

| Layer | Control |
|-------|---------|
| Source | No secrets committed; `.gitignore` covers `.env`, `*.tfvars`, `*.tfstate`, kubeconfigs, keys |
| Dependencies | Exact version pins (`requirements.txt`, `package-lock.json`), Trivy library scan |
| Build | Multi-stage images: no compilers, pip, Node or sources in runtime images; base packages upgraded at build |
| Container | Non-root users (10001 / 101 / 70), no privilege escalation, all Linux capabilities dropped, seccomp `RuntimeDefault` |
| Cluster | Namespace enforces the **restricted** Pod Security Standard; DB password generated in-cluster, never in Git |
| Network | Only Traefik is exposed; app Services are `ClusterIP`; worker nodes sit in private subnets behind a NAT gateway |
| Cloud identity | Laptop: `aws login` short-lived credentials. CI: GitHub OIDC → IAM role limited to `main`/`production`; EBS CSI uses EKS Pod Identity |
| HTTP | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, no server version banner |

### Other security scans (not implemented, for discussion)

* **SAST** (static analysis of our own code), for example Bandit or Semgrep for Python and CodeQL on GitHub.
* **Secret scanning**: GitHub push protection or gitleaks in CI.
* **Dependency review**: Dependabot alerts and `pip-audit` / `npm audit` on pull requests.
* **Runtime security**: Falco, or GuardDuty EKS Runtime Monitoring, to detect suspicious behaviour in running Pods.
