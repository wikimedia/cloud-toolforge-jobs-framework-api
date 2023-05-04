apiVersion: v1
kind: ConfigMap
metadata:
  name: harbor-config
  labels:
    {{- include "jobs-api.labels" . | nindent 4 }}
data:
  harbor.json: |
    {{ .Values.harbor | toJson }}
