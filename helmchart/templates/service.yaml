---
apiVersion: v1
kind: Service
metadata:
  name: jobs-api
  labels:
    {{- include "jobs-api.labels" . | nindent 4 }}
spec:
  selector:
    name: jobs-api
    {{- include "jobs-api.selectorLabels" . | nindent 4 }}
  type: ClusterIP
  ports:
    - name: https
      port: 8443
      targetPort: 8443
      protocol: TCP
