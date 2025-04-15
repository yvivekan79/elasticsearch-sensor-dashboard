# Elasticsearch Sensor Dashboard - Kubernetes Deployment

This directory contains resources for deploying the Elasticsearch Sensor Dashboard solution to Kubernetes using Helm.

## Contents

- **elasticsearch-sensor-dashboard/** - The Helm chart for deploying the complete solution
- **Dockerfile** - Dockerfile for building the Flask web application container
- **Dockerfile.init** - Dockerfile for building the initialization job container

## Deployment Steps

### 1. Prepare your Docker images

Build and push the Docker images required for the deployment:

```bash
# Build the main application image
docker build -t your-docker-registry/elasticsearch-sensor-dashboard:latest -f Dockerfile ..
docker push your-docker-registry/elasticsearch-sensor-dashboard:latest

# Build the initialization job image
docker build -t your-docker-registry/elasticsearch-sensor-dashboard-init:latest -f Dockerfile.init ..
docker push your-docker-registry/elasticsearch-sensor-dashboard-init:latest
```

### 2. Deploy with Helm

```bash
# Add the Elastic Helm repository for Elasticsearch and Kibana dependencies
helm repo add elastic https://helm.elastic.co
helm repo update

# Install the chart
helm install sensor-dashboard ./elasticsearch-sensor-dashboard \
  --set webapp.image.repository=your-docker-registry/elasticsearch-sensor-dashboard \
  --set webapp.initJob.image.repository=your-docker-registry/elasticsearch-sensor-dashboard-init
```

For more detailed instructions, see the README.md in the elasticsearch-sensor-dashboard directory.

## Customization

You can customize the deployment by creating a values.yaml file with your specific configuration:

```bash
helm install sensor-dashboard ./elasticsearch-sensor-dashboard -f my-values.yaml
```

## Example values.yaml

Here's an example values.yaml file for a production deployment:

```yaml
webapp:
  replicaCount: 2
  image:
    repository: your-docker-registry/elasticsearch-sensor-dashboard
    tag: 1.0.0
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: nginx
      cert-manager.io/cluster-issuer: letsencrypt
    hosts:
      - host: dashboard.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: dashboard-tls
        hosts:
          - dashboard.example.com

elasticsearch:
  replicas: 3
  persistence:
    size: 50Gi
  resources:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
  esJavaOpts: "-Xmx4g -Xms4g"
  protocol: https

kibana:
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: nginx
      cert-manager.io/cluster-issuer: letsencrypt
    hosts:
      - host: kibana.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: kibana-tls
        hosts:
          - kibana.example.com
```