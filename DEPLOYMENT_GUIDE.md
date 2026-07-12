# ArenaMind AI - Production Deployment Guide

This guide outlines the steps required to deploy the **ArenaMind AI Stadium Operating System** to production on **Google Cloud Platform (GCP)** using **Cloud Run**, **Secret Manager**, **Artifact Registry**, and **GitHub Actions**.

---

## Architecture Overview
The application is structured into three primary containerized components:
1. **Database**: Managed Cloud SQL PostgreSQL instance (recommended for production) or a containerized PostgreSQL database.
2. **Backend**: FastAPI server running on Cloud Run, retrieving secrets from GCP Secret Manager at runtime, and serving clients.
3. **Frontend**: Next.js (Node.js) server running on Cloud Run, pointing to the backend service.

---

## Prerequisites
- A Google Cloud Platform account with active billing.
- The [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install) installed locally.
- A GitHub repository containing the project.

---

## Step 1: Enable Google Cloud APIs
Run the following command to enable the necessary APIs for deployment, container storage, and secrets management:

```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com
```

---

## Step 2: Configure Secret Manager
ArenaMind AI retrieves database URLs and AI model API keys securely from GCP Secret Manager at startup. 

Create the following secrets:

1. **`DATABASE_URL`**:
   ```bash
   echo -n "postgresql://user:password@host:5432/db" | gcloud secrets create DATABASE_URL --data-file=-
   ```
2. **`GEMINI_API_KEY`**:
   ```bash
   echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
   ```

Grant the Cloud Run service account access to read these secrets:
```bash
# Get the default Compute Engine service account
SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:Default compute service account" --format="value(email)")

# Grant Secret Manager Secret Accessor role
gcloud secrets add-iam-policy-binding DATABASE_URL \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Step 3: Create Google Artifact Registry
Create a Docker registry repository in your target region (e.g., `us-central1`):
```bash
gcloud artifacts repositories create arenamind-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="ArenaMind AI Docker Images"
```

---

## Step 4: Deployment Configurations

### Option A: Deployment via GCP Cloud Build
A configuration file [cloudbuild.yaml](file:///c:/IT/Hackathons/PromptWars4/cloudbuild.yaml) is defined in the root directory. To trigger a manual build and deployment via Cloud Build, run:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

### Option B: Automated CI/CD via GitHub Actions
An automated workflow is configured at [.github/workflows/deploy.yml](file:///c:/IT/Hackathons/PromptWars4/.github/workflows/deploy.yml).

1. Create a GCP Service Account for GitHub Actions:
   ```bash
   gcloud iam service-accounts create github-deployer --display-name="GitHub Deployer"
   ```
2. Grant permissions to the service account:
   ```bash
   # Grant Cloud Run Developer
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-deployer@your-project-id.iam.gserviceaccount.com" \
       --role="roles/run.developer"

   # Grant Artifact Registry Writer
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-deployer@your-project-id.iam.gserviceaccount.com" \
       --role="roles/artifactregistry.writer"

   # Grant Service Account User (needed to associate default runtime account with Cloud Run)
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:github-deployer@your-project-id.iam.gserviceaccount.com" \
       --role="roles/iam.serviceAccountUser"
   ```
3. Generate a JSON Key for the Service Account:
   ```bash
   gcloud iam service-accounts keys create keys.json \
       --iam-account=github-deployer@your-project-id.iam.gserviceaccount.com
   ```
4. Add the contents of `keys.json` to your GitHub Repository Secrets under **`GCP_SA_KEY`**.
5. Update `PROJECT_ID` inside [.github/workflows/deploy.yml](file:///c:/IT/Hackathons/PromptWars4/.github/workflows/deploy.yml) to match your GCP project ID.
6. Push a commit to your `main` branch to trigger the build and deploy pipeline.

---

## Step 5: Logging, Monitoring, & Health Checks
- **Health Checks**: The backend container exposes a `/health` endpoint that validates database connectivity and Digital Twin status. Cloud Run uses this health check as startup/liveness probes automatically.
- **Structured Logging**: Container stdout/stderr logs are automatically aggregated by **Google Cloud Logging**. You can inspect runtime events and FastAPI tracebacks by searching:
  ```
  resource.type="cloud_run_revision" AND resource.labels.service_name="arenamind-backend"
  ```
- **Performance Metrics**: CPU utilization, memory consumption, request counts, and latency are visible directly in the **Google Cloud Run Monitoring Dashboard** under the Metrics tab for each service.
