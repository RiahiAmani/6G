apiVersion: apps/v1
kind: Deployment
metadata: { name: mec-${TIER} }
spec:
  replicas: 1
  selector: { matchLabels: { app: mec-${TIER} } }
  template:
    metadata: { labels: { app: mec-${TIER}, tier: ${TIER} } }
    spec:
      nodeSelector: { tier: ${TIER} }
      containers:
      - name: app
        image: mec-app:1.0
        imagePullPolicy: IfNotPresent
        env:
        - { name: TIER, value: "${TIER}" }
        - { name: NODE_NAME, valueFrom: { fieldRef: { fieldPath: spec.nodeName } } }
        readinessProbe:
          httpGet: { path: /, port: 8080 }
          periodSeconds: 2
        resources: { requests: { cpu: 100m }, limits: { cpu: ${CPU_LIMIT} } }
---
apiVersion: v1
kind: Service
metadata: { name: mec-${TIER} }
spec:
  type: NodePort
  selector: { app: mec-${TIER} }
  ports: [{ port: 80, targetPort: 8080, nodePort: ${PORT} }]
