#!/bin/bash
# Google Cloud Run Deployment Script for Online Exam Application
# Choose your preferred method by uncommenting the appropriate section

set -e

# Configuration
PROJECT_ID="onlineexam-f01cd"  # Your Firebase project ID
SERVICE_NAME="online-exam"
REGION="us-central1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Online Exam Application to Cloud Run${NC}"
echo "================================================================"

# Check if user is logged in to gcloud
if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Please login to gcloud first: gcloud auth login${NC}"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

echo -e "${YELLOW}📋 Choose your deployment method:${NC}"
echo "1. Environment Variable (Recommended for testing)"
echo "2. Service Account with IAM (Most secure)"
echo "3. Secret Manager (Enterprise)"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}🔐 Method 1: Using Environment Variable${NC}"
        
        # Check if service account file exists
        SERVICE_ACCOUNT_FILE="onlineexam-f01cd-firebase-adminsdk-fbsvc-41ab6e69cf.json"
        if [ ! -f "$SERVICE_ACCOUNT_FILE" ]; then
            echo -e "${RED}❌ Service account file not found: $SERVICE_ACCOUNT_FILE${NC}"
            echo "Please download it from Firebase Console > Project Settings > Service Accounts"
            exit 1
        fi
        
        # Convert to single line for environment variable
        FIREBASE_KEY=$(cat $SERVICE_ACCOUNT_FILE | tr -d '\n')
        
        echo "📧 Enter your email configuration:"
        read -p "Email address: " MAIL_USERNAME
        read -s -p "Email app password: " MAIL_PASSWORD
        echo
        
        # Deploy with environment variables
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated \
            --port 8080 \
            --memory 1Gi \
            --cpu 1 \
            --max-instances 10 \
            --set-env-vars "FIREBASE_SERVICE_ACCOUNT=$FIREBASE_KEY" \
            --set-env-vars "SECRET_KEY=$(openssl rand -base64 32)" \
            --set-env-vars "MAIL_SERVER=smtp.gmail.com" \
            --set-env-vars "MAIL_PORT=587" \
            --set-env-vars "MAIL_USERNAME=$MAIL_USERNAME" \
            --set-env-vars "MAIL_PASSWORD=$MAIL_PASSWORD" \
            --set-env-vars "MAIL_DEFAULT_SENDER=$MAIL_USERNAME"
        ;;
        
    2)
        echo -e "${GREEN}🔐 Method 2: Using Service Account with IAM${NC}"
        
        SA_NAME="cloudrun-firebase-sa"
        SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
        
        # Create service account
        echo "Creating service account..."
        gcloud iam service-accounts create $SA_NAME \
            --display-name "Cloud Run Firebase Service Account" || echo "Service account may already exist"
        
        # Grant Firebase permissions
        echo "Granting Firebase admin permissions..."
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SA_EMAIL" \
            --role="roles/firebase.admin"
        
        echo "📧 Enter your email configuration:"
        read -p "Email address: " MAIL_USERNAME
        read -s -p "Email app password: " MAIL_PASSWORD
        echo
        
        # Deploy with service account
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated \
            --service-account $SA_EMAIL \
            --port 8080 \
            --memory 1Gi \
            --cpu 1 \
            --max-instances 10 \
            --set-env-vars "SECRET_KEY=$(openssl rand -base64 32)" \
            --set-env-vars "MAIL_SERVER=smtp.gmail.com" \
            --set-env-vars "MAIL_PORT=587" \
            --set-env-vars "MAIL_USERNAME=$MAIL_USERNAME" \
            --set-env-vars "MAIL_PASSWORD=$MAIL_PASSWORD" \
            --set-env-vars "MAIL_DEFAULT_SENDER=$MAIL_USERNAME"
        ;;
        
    3)
        echo -e "${GREEN}🔐 Method 3: Using Secret Manager${NC}"
        
        SERVICE_ACCOUNT_FILE="onlineexam-f01cd-firebase-adminsdk-fbsvc-41ab6e69cf.json"
        if [ ! -f "$SERVICE_ACCOUNT_FILE" ]; then
            echo -e "${RED}❌ Service account file not found: $SERVICE_ACCOUNT_FILE${NC}"
            exit 1
        fi
        
        # Create secret in Secret Manager
        echo "Creating secret in Secret Manager..."
        gcloud secrets create firebase-service-account \
            --data-file $SERVICE_ACCOUNT_FILE || echo "Secret may already exist"
        
        # Grant Cloud Run access to secret
        echo "Granting Cloud Run access to secret..."
        PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
        gcloud secrets add-iam-policy-binding firebase-service-account \
            --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
            --role="roles/secretmanager.secretAccessor"
        
        echo "📧 Enter your email configuration:"
        read -p "Email address: " MAIL_USERNAME
        read -s -p "Email app password: " MAIL_PASSWORD
        echo
        
        # Deploy with Secret Manager
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated \
            --port 8080 \
            --memory 1Gi \
            --cpu 1 \
            --max-instances 10 \
            --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
            --set-env-vars "SECRET_KEY=$(openssl rand -base64 32)" \
            --set-env-vars "MAIL_SERVER=smtp.gmail.com" \
            --set-env-vars "MAIL_PORT=587" \
            --set-env-vars "MAIL_USERNAME=$MAIL_USERNAME" \
            --set-env-vars "MAIL_PASSWORD=$MAIL_PASSWORD" \
            --set-env-vars "MAIL_DEFAULT_SENDER=$MAIL_USERNAME"
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo "================================================================"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")
echo -e "${GREEN}🌐 Your application is live at: $SERVICE_URL${NC}"

echo -e "${YELLOW}📝 Default Admin Credentials:${NC}"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "   Username: admin2" 
echo "   Password: admin456"

echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "1. Visit your application and test the login"
echo "2. Change default admin passwords"
echo "3. Create your first exam and users"
echo "4. Configure email settings in admin panel"

echo -e "${GREEN}🎉 Happy examining!${NC}"