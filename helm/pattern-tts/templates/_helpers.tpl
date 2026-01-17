{{/*
Expand the name of the chart
*/}}
{{- define "pattern-tts.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name
*/}}
{{- define "pattern-tts.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label
*/}}
{{- define "pattern-tts.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pattern-tts.labels" -}}
helm.sh/chart: {{ include "pattern-tts.chart" . }}
{{ include "pattern-tts.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: pattern-agentic
pattern-agentic.io/service-group: audio
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pattern-tts.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pattern-tts.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "pattern-tts.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default "pattern-tts-service" .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Full image name
*/}}
{{- define "pattern-tts.image" -}}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "pattern-tts.namespace" -}}
{{- default .Release.Namespace .Values.global.namespace }}
{{- end }}

{{/*
Helper to convert .Values.config to ConfigMap data with PA_TTS_ prefix
*/}}
{{- define "pattern-tts.configmap.data" -}}
{{- range $key, $val := .Values.config -}}
{{- printf "PA_TTS_%s: %s\n" $key ($val | toString | quote) }}
{{- end -}}
{{- end -}}
