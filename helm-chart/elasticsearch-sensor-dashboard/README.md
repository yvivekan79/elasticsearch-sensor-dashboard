# Elasticsearch Sensor Dashboard Helm Chart

This Helm chart deploys a complete solution for Elasticsearch data streams with Kibana visualization for sensor telemetry data. It includes:

- Elasticsearch 8.x cluster
- Kibana 8.x dashboard
- Flask web application for monitoring
- Automatic data stream setup and sample data ingestion

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure
- A Docker registry where you can push the application images

## Installing the Chart

### 1. Build and Push Docker Images

First, build and push the Docker images for the web application and initialization job:

```bash
# Build web application image
cd /path/to/your/app
docker build -t your-docker-registry/elasticsearch-sensor-dashboard:latest -f helm-chart/Dockerfile .
docker push your-docker-registry/elasticsearch-sensor-dashboard:latest

# Build initialization job image
docker build -t your-docker-registry/elasticsearch-sensor-dashboard-init:latest -f helm-chart/Dockerfile.init .
docker push your-docker-registry/elasticsearch-sensor-dashboard-init:latest
```

### 2. Install the Helm Chart

```bash
# Add the Elastic Helm repository
helm repo add elastic https://helm.elastic.co

# Update repositories
helm repo update

# Install the chart with a release name
helm install my-sensor-dashboard ./helm-chart/elasticsearch-sensor-dashboard \
  --set webapp.image.repository=your-docker-registry/elasticsearch-sensor-dashboard \
  --set webapp.initJob.image.repository=your-docker-registry/elasticsearch-sensor-dashboard-init
```

### 3. Testing the Chart

To verify the deployment:

```bash
# Check the deployment status
kubectl get pods

# Access the web application (if no ingress is enabled)
kubectl port-forward svc/my-sensor-dashboard-elasticsearch-sensor-dashboard-webapp 8080:80
```

Then open http://localhost:8080 in your browser.

## Configuration

The following table lists the configurable parameters for this Helm chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `webapp.replicaCount` | Number of webapp replicas | `1` |
| `webapp.image.repository` | Web application image repository | `your-docker-registry/elasticsearch-sensor-dashboard` |
| `webapp.image.tag` | Web application image tag | `latest` |
| `webapp.service.type` | Service type for web application | `ClusterIP` |
| `webapp.ingress.enabled` | Enable ingress for web application | `false` |
| `webapp.env.ES_HOST` | Elasticsearch host URL | `http://elasticsearch-sensor-dashboard-elasticsearch-master:9200` |
| `webapp.env.KIBANA_URL` | Kibana URL | `http://elasticsearch-sensor-dashboard-kibana:5601` |
| `elasticsearch.replicas` | Number of Elasticsearch nodes | `1` |
| `elasticsearch.persistence.enabled` | Enable persistent storage for Elasticsearch | `true` |
| `elasticsearch.persistence.size` | Storage size for Elasticsearch | `10Gi` |
| `elasticsearch.resources.requests.memory` | Memory request for Elasticsearch | `2Gi` |
| `kibana.resources.requests.memory` | Memory request for Kibana | `1Gi` |
| `sampleData.enabled` | Enable persistent volume for sample data | `true` |
| `sampleData.size` | Size of sample data volume | `1Gi` |

## Upgrading the Chart

To upgrade the deployment:

```bash
helm upgrade my-sensor-dashboard ./helm-chart/elasticsearch-sensor-dashboard \
  --set webapp.image.tag=new-version
```

## Uninstalling the Chart

To uninstall/delete the deployment:

```bash
helm delete my-sensor-dashboard
```

This will delete all the Kubernetes resources associated with the chart and remove the release.

## Persistence

The chart mounts a Persistent Volume for Elasticsearch and for the sample data. The PVs will not be deleted upon helm uninstall. To delete the PVs:

```bash
kubectl delete pvc -l app.kubernetes.io/instance=my-sensor-dashboard
```

## Security

This chart uses the built-in security features of Elasticsearch 8.x. The default password for the elastic user is generated automatically and stored in a Kubernetes secret.

To retrieve the Elasticsearch password:

```bash
kubectl get secret my-sensor-dashboard-elasticsearch-master-credentials -o jsonpath="{.data.password}" | base64 --decode
```

For production environments, it is recommended to:

1. Enable TLS for Elasticsearch and Kibana
2. Configure a more robust ingress with TLS
3. Set up proper role-based access control
4. Consider using external authentication providers