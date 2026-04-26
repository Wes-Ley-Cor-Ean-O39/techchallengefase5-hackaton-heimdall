{{- define "heimdail.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "heimdail.fullname" -}}
{{- default (include "heimdail.name" .) .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
