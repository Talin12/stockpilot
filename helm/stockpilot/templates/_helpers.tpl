{{/* Base name: <release>, or <release>-stockpilot if the release name doesn't contain it. */}}
{{- define "stockpilot.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "stockpilot.backend.fullname" -}}{{ include "stockpilot.fullname" . }}-backend{{- end -}}
{{- define "stockpilot.frontend.fullname" -}}{{ include "stockpilot.fullname" . }}-frontend{{- end -}}
{{- define "stockpilot.postgres.fullname" -}}{{ include "stockpilot.fullname" . }}-postgres{{- end -}}
{{- define "stockpilot.dbSecretName" -}}
{{- if .Values.postgres.enabled -}}{{ include "stockpilot.fullname" . }}-db{{- else -}}{{ required "externalDatabase.existingSecret is required when postgres.enabled=false" .Values.externalDatabase.existingSecret }}{{- end -}}
{{- end -}}

{{/* Labels shared by everything; component resources add the selector labels on top. */}}
{{- define "stockpilot.baseLabels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/part-of: stockpilot
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}

{{/* For resources without selector labels (Ingress, HPA, PDB, Secret, ConfigMap, ...). */}}
{{- define "stockpilot.labels" -}}
{{ include "stockpilot.baseLabels" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Selector labels: must stay stable across upgrades. Call with (dict "ctx" . "component" "backend"). */}}
{{- define "stockpilot.selectorLabels" -}}
app.kubernetes.io/name: stockpilot-{{ .component }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* image reference; tag is mandatory (CI passes the commit SHA, never "latest"). */}}
{{- define "stockpilot.image" -}}
{{- $tag := required (printf "%s.image.tag is required (CI sets it to the Git commit SHA)" .component) .image.tag -}}
{{- printf "%s:%s" .image.repository $tag -}}
{{- end -}}

{{- define "stockpilot.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "stockpilot.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: ["ALL"]
{{- end -}}
