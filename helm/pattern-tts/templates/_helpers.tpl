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
{{- default "tts-service" .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image repository URL helper
*/}}
{{- define "pattern-tts.imageRepository" -}}
{{- if .Values.imageRegistry.url }}
{{- printf "%s/%s" .Values.imageRegistry.url .Values.tts.image.repository }}
{{- else }}
{{- .Values.tts.image.repository }}
{{- end }}
{{- end }}

{{/*
Full image name
*/}}
{{- define "pattern-tts.image" -}}
{{- $repo := include "pattern-tts.imageRepository" . }}
{{- printf "%s:%s" $repo .Values.tts.image.tag }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "pattern-tts.namespace" -}}
{{- default .Release.Namespace .Values.global.namespace }}
{{- end }}

{{/*
Environment
*/}}
{{- define "pattern-tts.environment" -}}
{{- default "dev" .Values.global.environment }}
{{- end }}
