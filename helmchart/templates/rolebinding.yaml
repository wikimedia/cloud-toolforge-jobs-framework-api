---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: jobs-api
  labels:
    {{- include "jobs-api.labels" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: jobs-api
subjects:
- kind: ServiceAccount
  name: jobs-api
  namespace: {{ .Release.Namespace }}
