apiVersion: apps/v1
kind: Deployment
metadata: { name: ${SVC} }
spec:
  replicas: ${REPLICAS}
  selector: { matchLabels: { app: ${SVC} } }
  template:
    metadata: { labels: { app: ${SVC}, tier: ${TIER} } }
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
        resources: { requests: { cpu: 100m }, limits: { cpu: 800m } }
---
apiVersion: v1
kind: Service
metadata: { name: ${SVC} }
spec:
  type: NodePort
  selector: { app: ${SVC} }
  ports: [{ port: 80, targetPort: 8080, nodePort: ${PORT} }]
