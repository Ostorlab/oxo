The # Cloud Run Runtime for Ostorlab

The Cloud Run runtime enables running Ostorlab security scans on Google Cloud Run, providing a scalable and serverless approach to security scanning.

## Overview

Unlike the traditional local runtime that uses Docker Swarm, the Cloud Run runtime:
- **Deploys agents as Cloud Run services** instead of Docker containers
- **Uses external message queue and Redis services** that are accessible over the internet
- **Provides automatic scaling** based on workload
- **Eliminates the need for local Docker Swarm** infrastructure
- **Enables serverless security scanning** with pay-per-use pricing

## Architecture

```
┌─────────────────┐        ┌──────────────────┐        ┌─────────────────┐
│                 │        │                  │        │                 │
│   RabbitMQ      │◄──────►│   Cloud Run      │◄──────►│   Redis         │
│   (External)    │  AMQP  │   Services       │  TCP   │   (External)    │
│                 │        │   (Agents)       │        │                 │
└─────────────────┘        └──────────────────┘        └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │                  │
                        │   Local Database │
                        │   (SQLite)       │
                        │                  │
                        └──────────────────┘
```

## Prerequisites

### Google Cloud Platform

1. **GCP Account** with billing enabled
2. **Cloud Run API** enabled in your project
3. **Appropriate permissions**:
   - `roles/run.admin` - For deploying and managing services
   - `roles/iam.serviceAccountUser` - For using service accounts
   - `roles/cloudsql.client` - If using Cloud SQL (optional)

### External Services

You need to provide RabbitMQ and Redis services accessible over the internet:

1. **RabbitMQ** (with management plugin enabled)
2. **Redis** (optionally with TLS support)

These can be hosted on:
- Google Cloud Memorystore for Redis
- CloudAMQP for RabbitMQ
- Self-hosted services with public IP addresses
- Other cloud providers

### Local Environment

1. **Python 3.8+**
2. **Google Cloud SDK** installed and authenticated
3. **Ostorlab CLI** installed

## Installation

### 1. Install Required Dependencies

```bash
pip install google-cloud-run google-api-core
```

### 2. Configure Google Cloud SDK

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Initialize and authenticate
gcloud init
gcloud auth login
gcloud auth application-default login
```

### 3. Set Up External Services

#### Option A: Using CloudAMQP and Google Memorystore

```bash
# Set up RabbitMQ on CloudAMQP
export MQ_URL="amqps://user:password@host.cloudamqp.com:5671/vhost"
export MQ_MANAGEMENT_URL="https://user:password@host.cloudamqp.com:15672"

# Set up Redis on Google Memorystore
export REDIS_URL="redis://10.0.0.1:6379"
```

#### Option B: Self-Hosted with Public IPs

Ensure your RabbitMQ and Redis services are accessible and secured with TLS/SSL.

## Configuration

### Environment Variables

You can configure the Cloud Run runtime using environment variables:

```bash
# Google Cloud Configuration
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export GCP_SERVICE_ACCOUNT="cloud-run-sa@your-project.iam.gserviceaccount.com"

# External Services (required)
export MQ_URL="amqps://user:password@rabbitmq:5671/vhost"
export MQ_VHOST="vhost"
export MQ_MANAGEMENT_URL="https://user:password@rabbitmq:15672"
export REDIS_URL="redis://redis-host:6379"
```

### Command Line Arguments

When running scans, provide the following arguments:

```bash
oxo scan run \
  --runtime cloud_run \
  --gcp-project-id your-project-id \
  --gcp-region us-central1 \
  --bus-url "amqps://user:password@host:5671/vhost" \
  --bus-vhost "vhost" \
  --bus-management-url "https://user:password@host:15672" \
  --redis-url "redis://redis-host:6379" \
  --agent=agent/ostorlab/nmap \
  --title "Cloud Run Scan" \
  ip 8.8.8.8
```

## Usage

### Basic Scan Example

```bash
# Scan a single IP address
oxo scan run \
  --runtime cloud_run \
  --gcp-project-id my-security-project \
  --gcp-region us-central1 \
  --bus-url "${MQ_URL}" \
  --bus-management-url "${MQ_MANAGEMENT_URL}" \
  --redis-url "${REDIS_URL}" \
  --agent=agent/ostorlab/nmap \
  --title "Nmap Cloud Run Scan" \
  ip 192.168.1.1
```

### Multiple Agents Example

```bash
# Run multiple security agents
oxo scan run \
  --runtime cloud_run \
  --gcp-project-id my-security-project \
  --gcp-region us-central1 \
  --bus-url "${MQ_URL}" \
  --bus-management-url "${MQ_MANAGEMENT_URL}" \
  --redis-url "${REDIS_URL}" \
  --agent=agent/ostorlab/nmap \
  --agent=agent/ostorlab/openvas \
  --agent=agent/ostorlab/zap \
  --title "Multi-Agent Cloud Run Scan" \
  domain-name example.com
```

### Using Agent Group Definition

Create a YAML file with agent group definition:

```yaml
# agents.yaml
agents:
  - key: agent/ostorlab/nmap
    args:
      fast_mode: true
      ports: "80,443"
  - key: agent/ostorlab/subfinder
  - key: agent/ostorlab/httpx
```

Run the scan:

```bash
oxo scan run \
  --runtime cloud_run \
  --gcp-project-id my-security-project \
  --gcp-region us-central1 \
  --bus-url "${MQ_URL}" \
  --bus-management-url "${MQ_MANAGEMENT_URL}" \
  --redis-url "${REDIS_URL}" \
  --agent-group-definition agents.yaml \
  --title "Agent Group Cloud Run Scan" \
  domain-name target.com
```

### Monitoring Scans

```bash
# List all scans
oxo scan list

# Get scan details
oxo scan describe <scan-id>

# Follow scan logs
oxo scan run \
  --runtime cloud_run \
  # ... other options ...
  --follow agent/ostorlab/nmap \
  ip 8.8.8.8
```

### Stopping a Scan

```bash
# Stop a running scan
oxo scan stop <scan-id>
```

This will delete all Cloud Run services associated with the scan.

## Configuration Options

### Google Cloud Options

| Option | Environment Variable | Description | Required |
|--------|---------------------|-------------|----------|
| `--gcp-project-id` | `GCP_PROJECT_ID` | GCP Project ID | Yes |
| `--gcp-region` | `GCP_REGION` | GCP Region (e.g., us-central1) | Yes |
| `--gcp-service-account` | `GCP_SERVICE_ACCOUNT` | Service account email | No |

### External Services Options

| Option | Environment Variable | Description | Required |
|--------|---------------------|-------------|----------|
| `--bus-url` | `MQ_URL` | RabbitMQ AMQP URL | Yes |
| `--bus-management-url` | `MQ_MANAGEMENT_URL` | RabbitMQ management URL | Yes |
| `--bus-vhost` | `MQ_VHOST` | RabbitMQ virtual host | Yes |
| `--redis-url` | `REDIS_URL` | Redis connection URL | Yes |

### Scan Options

All standard Ostorlab scan options work with Cloud Run runtime:

- `--agent`: Specify agents to run
- `--agent-group-definition`: Use YAML file for agent configuration
- `--title`: Scan title
- `--follow`: Follow specific agent logs
- `--timeout`: Scan timeout
- And more...

## Resource Configuration

### Default Resources

By default, Cloud Run services use:
- **Memory**: 512Mi
- **CPU**: 1
- **Min Instances**: 1
- **Max Instances**: 10

### Custom Resources (Future Enhancement)

Future versions will support custom resource specifications through agent definitions.

## Pricing

### Google Cloud Run Costs

You are charged for:
- **CPU**: Per CPU-second used
- **Memory**: Per GB-second used
- **Requests**: Per million requests
- **Networking**: Egress charges for external MQ/Redis connections

Example monthly cost for typical scans:
- Light scanning: $10-50
- Moderate scanning: $50-200
- Heavy scanning: $200-1000+

### External Services Costs

- **CloudAMQP**: Based on message volume and connections
- **Memorystore**: Based on instance size
- **Self-hosted**: Server/VM costs

## Security Considerations

### 1. Service Account Security

- Use dedicated service accounts for Cloud Run
- Apply principle of least privilege
- Rotate service account keys regularly

### 2. Network Security

- **Always use TLS/SSL** for MQ and Redis connections
- Use VPC Service Controls to restrict service access
- Enable Cloud Audit Logs
- Consider using Private Google Access

### 3. Secrets Management

Store sensitive configuration in:
- Google Secret Manager
- Environment variables (less secure)
- Cloud Key Management Service

### 4. Scan Isolation

Each scan runs in isolated Cloud Run services:
- Separate service instances per agent
- Network isolation between scans
- Resource quotas per scan

## Troubleshooting

### Common Issues

#### 1. Permission Errors

```
Error: Permission denied for Cloud Run
```

**Solution**: Ensure service account has `roles/run.admin` and `roles/iam.serviceAccountUser`.

#### 2. MQ Connection Failures

```
Error: Cannot connect to RabbitMQ
```

**Solution**: Verify MQ_URL format and firewall rules. Test connection:
```bash
python -c "import pika; pika.BlockingConnection(pika.URLParameters('${MQ_URL}'))"
```

#### 3. Redis Connection Failures

```
Error: Redis connection timeout
```

**Solution**: Check Redis URL and network accessibility.

#### 4. Resource Exhaustion

```
Error: Quota exceeded
```

**Solution**: Request quota increase in GCP Console or reduce max instances.

### Debug Mode

Enable debug logging:

```bash
export OSTORLAB_DEBUG=1
oxo scan run --runtime cloud_run ...
```

## Best Practices

### 1. Resource Optimization

- Start with smaller agents and scale up
- Monitor Cloud Run metrics in GCP Console
- Use appropriate instance sizes for agent workload

### 2. Cost Management

- Set up budget alerts in GCP
- Use Cloud Run min/max instance controls
- Clean up completed scans promptly
- Consider using Cloud Run jobs for batch scanning

### 3. Performance Tuning

- Use regions closest to your external services
- Enable connection pooling in agents
- Monitor MQ and Redis performance
- Scale based on queue depth

### 4. Reliability

- Use health checks in external services
- Implement retry logic for transient failures
- Monitor service quotas
- Set up proper alerting

## Limitations

1. **No Local Persistence**: Unlike local runtime, agents cannot access local files directly
2. **External Dependencies**: Requires reliable internet connectivity to external services
3. **Startup Latency**: Cloud Run services may have cold start delays
4. **Resource Limits**: Subject to Cloud Run resource constraints
5. **VPC Access**: Requires additional configuration for private VPC resources

## Future Enhancements

Planned improvements:
- [ ] Custom resource configuration per agent
- [ ] VPC Connector support for private resources
- [ ] Cloud Run Job support for batch scanning
- [ ] Automatic service discovery
- [ ] Enhanced monitoring and metrics
- [ ] Cost optimization features
- [ ] Multi-region deployment support

## Contributing

To contribute to the Cloud Run runtime:

1. Follow the existing code patterns
2. Add unit tests for new features
3. Update documentation
4. Test with real GCP projects

## Support

For issues and questions:
- Check troubleshooting section
- Review GCP Cloud Run documentation
- Check Ostorlab documentation
- Create GitHub issue with debug logs

## License

This module follows the same license as the main Ostorlab project.
