# Google Cloud Deployment Guide

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud SDK installed (`gcloud` CLI)
3. Project created in Google Cloud Console

## Initial Setup

1. **Authenticate with Google Cloud:**
```bash
gcloud auth login
```

2. **Set your project:**
```bash
gcloud config set project YOUR_PROJECT_ID
```

3. **Enable required APIs:**
```bash
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

## Option 1: Deploy to App Engine

### Steps:

1. **Initialize App Engine:**
```bash
gcloud app create --region=us-central1
```

2. **Update app.yaml:**
- Replace `your-production-secret-key-change-this` with a secure secret key
- Add your email configuration in environment variables

3. **Deploy:**
```bash
gcloud app deploy
```

4. **View your app:**
```bash
gcloud app browse
```

## Option 2: Deploy to Cloud Run

### Steps:

1. **Build and deploy using Cloud Build:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

OR manually:

2. **Build Docker image:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/online-exam
```

3. **Deploy to Cloud Run:**
```bash
gcloud run deploy online-exam \
  --image gcr.io/YOUR_PROJECT_ID/online-exam \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

## Database Setup (Production)

### ⚠️ Important Note for Cloud Run
The application now **automatically initializes** the database on startup. For Cloud Run deployments:
- SQLite databases are ephemeral (reset on container restart)
- For persistent data, use Cloud SQL (recommended for production)
- Default admin users are created automatically: `admin/admin123` and `admin2/admin456`

### Option A: Use Cloud SQL (Recommended for production)

1. **Create Cloud SQL instance:**
```bash
gcloud sql instances create exam-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

2. **Create database:**
```bash
gcloud sql databases create exam_system --instance=exam-db
```

3. **Create user:**
```bash
gcloud sql users create exam_user \
  --instance=exam-db \
  --password=YOUR_SECURE_PASSWORD
```

4. **Update configuration:**
- Update `DATABASE_URL` in app.yaml or set as environment variable
- Format: `postgresql://exam_user:password@/exam_system?unix_socket=/cloudsql/PROJECT_ID:us-central1:exam-db`

### Option B: Use Firestore (NoSQL alternative)
- Enable Firestore in Google Cloud Console
- Modify application to use Firestore SDK

## Environment Variables

Set these in app.yaml or Cloud Run environment:

```yaml
env_variables:
  SECRET_KEY: "your-secure-secret-key"
  MAIL_SERVER: "smtp.gmail.com"
  MAIL_PORT: "587"
  MAIL_USE_TLS: "true"
  MAIL_USERNAME: "your-email@gmail.com"
  MAIL_PASSWORD: "your-app-password"
  DATABASE_URL: "your-database-url"  # For Cloud SQL
```

## Security Considerations

1. **Secret Management:**
```bash
# Use Secret Manager for sensitive data
gcloud secrets create app-secret-key --data-file=-
gcloud secrets add-iam-policy-binding app-secret-key \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

2. **Enable Cloud IAP for authentication:**
```bash
gcloud iap web enable --resource-type=app-engine \
  --oauth2-client-id=CLIENT_ID \
  --oauth2-client-secret=CLIENT_SECRET
```

3. **Set up Cloud Armor for DDoS protection**

## Monitoring

1. **View logs:**
```bash
gcloud app logs tail -s default
# OR for Cloud Run
gcloud run logs read --service online-exam
```

2. **Set up monitoring:**
- Go to Cloud Console > Monitoring
- Create alerts for errors, latency, and uptime

## CI/CD with GitHub

1. **Set up Cloud Build trigger:**
```bash
gcloud builds triggers create github \
  --repo-name=onlineExam \
  --repo-owner=mintgrid \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

2. **Add service account permissions:**
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_CLOUDBUILD_SA@cloudbuild.gserviceaccount.com" \
  --role="roles/run.developer"
```

## Useful Commands

```bash
# Check deployment status
gcloud app describe

# Stream logs
gcloud app logs tail

# SSH into instance (App Engine Flex only)
gcloud app instances ssh INSTANCE_ID --service=default

# Update traffic split
gcloud app services set-traffic default --splits=v1=0.5,v2=0.5

# Delete old versions
gcloud app versions delete VERSION_ID
```

## Estimated Costs (as of 2024)

- **App Engine Standard:** ~$0-50/month for low traffic
- **Cloud Run:** ~$0-30/month for low traffic  
- **Cloud SQL:** ~$7-50/month for basic instance
- **Storage:** ~$0.02/GB/month

## Troubleshooting

1. **502 Bad Gateway:**
   - Check logs: `gcloud app logs read`
   - Verify all dependencies in requirements.txt
   - Ensure database connection string is correct

2. **Memory errors:**
   - Increase instance class in app.yaml
   - Optimize database queries

3. **Permission denied:**
   - Check service account permissions
   - Verify API services are enabled

## Support

For issues specific to this deployment:
- Check logs first
- Review Google Cloud documentation
- Contact Google Cloud Support