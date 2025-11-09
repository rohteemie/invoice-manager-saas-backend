import os
# Set TESTING environment variable before any app imports
os.environ["TESTING"] = "1"
# Set required environment variables for tests
os.environ["PROJECT_NAME"] = "Multi-Tenant SaaS Backend Test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
