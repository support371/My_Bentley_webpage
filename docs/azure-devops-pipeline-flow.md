# Azure DevOps pipeline flow for `My_Bentley_webpage`

This repo is currently a **FastAPI-first service**, not a Next.js + FastAPI monorepo.
The pipeline package added here is therefore **backend-ready now** and structured so a future frontend image can be added without redesigning the release flow.

## What was added

- `azure-pipelines.aks.yml`
- `.azure-pipelines/templates/backend-ci.yml`
- `.azure-pipelines/templates/containerize.yml`
- `.azure-pipelines/templates/deploy-aks.yml`
- `Dockerfile`
- `charts/bentley-fastapi/*`

## Delivery flow

1. **Validate**
   - install Python dependencies
   - compile-check `app/` and `tests/`
   - run `pytest`
   - boot the FastAPI app
   - run `smoke-test.sh`

2. **Containerize**
   - build Docker image
   - push image to ACR
   - tag with branch + build ID and `latest`

3. **Deploy to dev**
   - runs from `develop`
   - upgrades Helm release in AKS dev namespace

4. **Deploy to prod**
   - runs from `main`
   - upgrades Helm release in AKS prod namespace
   - intended to be protected by Azure DevOps environment approvals

## Azure DevOps resources you still need to create

### Service connections

Create these two service connections in Azure DevOps:

1. `Bentley-ACR-ServiceConnection`
   - points to Azure Container Registry
   - used by `Docker@2`

2. `Bentley-AzureRM-ServiceConnection`
   - Azure Resource Manager connection with access to:
     - AKS cluster
     - resource group
     - ACR if needed for deployment-time operations

## Pipeline variables to replace immediately

Update these root pipeline variables in `azure-pipelines.aks.yml`:

- `acrLoginServer`
- `aksResourceGroup`
- `aksClusterName`
- `devIngressHost`
- `prodIngressHost`
- `devExistingSecret`
- `prodExistingSecret`

## Secrets that must exist in Kubernetes

The chart expects an **existing Kubernetes secret** per environment.

Minimum recommended keys:

- `SECRET_KEY`
- `WEBHOOK_SECRET`
- `DATABASE_URL`
- `BENTLEY_CLIENT_ID`
- `BENTLEY_CLIENT_SECRET`
- `INITIAL_ADMIN_PASSWORD`

Optional but recommended:

- `ALERT_SLACK_WEBHOOK`
- `ALERT_EMAIL_SMTP`

## Recommended variable groups

Create Azure DevOps variable groups such as:

- `bentley-dev`
- `bentley-prod`

Use them for non-secret deployment metadata or as references when you extend the pipeline later.

## Recommended environment approvals

Create Azure DevOps environments:

- `bentley-dev`
- `bentley-prod`

Add approvals/checks to `bentley-prod` so production releases pause until an authorized approver allows deployment.

## AKS / ingress expectations

The Helm chart assumes:

- NGINX ingress controller already exists
- cert-manager already exists
- a cluster issuer named `letsencrypt-prod` exists
- the namespace is created automatically by Helm if missing

If your cluster does not use cert-manager yet, remove or override the ingress annotations and TLS section before first production deployment.

## How to extend this to the full autonomous builder flow later

When you add a Next.js frontend or an autonomous builder worker, extend the package like this:

1. add a second Dockerfile and image build stage
2. split Helm values into `frontend` and `backend`
3. add a worker deployment for agent jobs
4. connect Azure OpenAI via managed identity or Key Vault-backed secrets
5. attach Azure DevOps MCP server credentials through a controlled secret flow
6. add approvals, audit hooks, and PR policy enforcement outside YAML

## Practical rollout order

1. replace placeholder Azure values
2. create ACR + AzureRM service connections
3. create dev/prod Kubernetes secrets
4. run pipeline from `develop`
5. validate `/health` and smoke route coverage in dev
6. add prod environment approvals
7. release from `main`

## Why this package is backend-first

Your current production path is the Bentley FastAPI app already running from `app.main:app`.
Trying to force a fake frontend stage into this repo now would create deployment drift.
This package gets the real service under CI/CD immediately and leaves clean room for the broader autonomous builder stack afterward.
