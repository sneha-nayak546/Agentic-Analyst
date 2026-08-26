import os
from google.cloud import aiplatform

def verify_auth():
    project_id = "agent-jgh"
    location = "us-central1"
    
    print("Checking GOOGLE_APPLICATION_CREDENTIALS...")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"Found credentials at: {creds_path}")
        if os.path.exists(creds_path):
            print("Credential file exists.")
        else:
            print("ERROR: Credential file does not exist!")
            return
    else:
        print("WARNING: GOOGLE_APPLICATION_CREDENTIALS is not set in environment. GCP APIs may fallback to default credentials.")
    
    try:
        print(f"Initializing aiplatform for project '{project_id}' in '{location}'...")
        aiplatform.init(project=project_id, location=location)
        print("Initialization successful.")
        
        print("\nAttempting to list Vertex AI models to test permissions...")
        models = aiplatform.Model.list()
        print(f"Success! Found {len(models)} models in the project.")
        
    except Exception as e:
        print(f"\nERROR validating GCP Connection/Permissions: {e}")

if __name__ == "__main__":
    verify_auth()
