import requests
import random
import string
# import json
import os
from dotenv import load_dotenv


# Load environment variables from .env if present
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
print(BASE_URL)


verified_users_email = os.getenv("verified_user_email")
verified_user_password = os.getenv("verified_user_password")

super_admin_email = os.getenv("super_admin_email")
super_admin_password = os.getenv("super_admin_password")


results = []
checklist = [
    "Create a new user",
    "Login with the user",
    "Read user profile",
    "Update user profile",
    "Delete user profile",
    "Create an organization (tenant)",
    "Add users with privileges to organization",
    "Grant new privileges to newly added users in organization",
    "Newly added users should carry out actions in organization",
    "Owner can promote or demote users in the organization",
    "Invoice creation by organization users",
    "Login and check using different users with different privileges",
    "Modify invoices created by another users",
    "Delete invoices created by another users",
    "Update organization details",
    "Owners can read all invoices created within an organization",
    "Owner can modify invoices created by any users in organization "
    "(draft/sent)",
    "Other users can only read all invoices that are created by them alone",
    "Other users can modify invoices created by them, only if status is "
    "still draft/unpaid",
    "Created users from inside the organization cannot signin until "
    "password had been changed",
    "Created users within an organisation cannot read all other users or "
    "view all other users",
]


# 2. Login with a VERIFIED admin user
login_data = {
    "username": verified_users_email,
    "password": verified_user_password
}
resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
success = resp.status_code == 200 and "access_token" in resp.json()

print(f"2. Login with verified admin: {'✔' if success else '✘'}")

tokens = resp.json() if resp.ok else {}
access_token = tokens.get("access_token")

headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
owner_headers = headers  # Use verified admin as owner for subsequent tests



# invoice_data = {
#     "customer_name": "Customer B",
#     "customer_email": "someemail@mail.com",
#     "customer_phone": "1234567890",
#     "customer_address": "123 Main St",
#     "issue_date": "2026-01-20",
#     "items": [{"description": "Product X", "quantity": 2, "unit_price": 50.0}],
#     "notes": "Test invoice",
# }


# invoice_resp = requests.post(
#     f"{BASE_URL}/invoices", json=invoice_data, headers=owner_headers
# )


# invoice_success = (
#     invoice_resp.status_code == 201 and "id" in invoice_resp.json()
# )


# print(f"11. Admin creates invoice: {'✔' if invoice_success else '✘'}")
# invoice_id = invoice_resp.json().get("id") if invoice_success else None

# print("Invoice ID:", invoice_id)  # Invoice ID: 2d06589d-b425-4a8f-97c4-23ad845c1555



# Update the invoice (requires manager role)
# response = requests.put(
# 	f"{BASE_URL}/invoices/2d06589d-b425-4a8f-97c4-23ad845c1555",
# 	json={
# 		"customer_name": "Updated Name",
# 		"notes": "Updated notes"
# 	},
# 	headers=owner_headers
# )
# print(response.json())



# Update to tenant
response = requests.put(
	f"{BASE_URL}/tenants/4edea210-ee63-43d1-a268-940e1e90ffe0",
	json={
		"tax_rate": 10.0
	},
	headers=owner_headers
)
print(response.json())