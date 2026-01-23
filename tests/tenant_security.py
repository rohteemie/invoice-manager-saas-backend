# import requests
# import os
# import random
# import string
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
# VERIFIED_USER_EMAIL = os.getenv("verified_user_email")
# VERIFIED_USER_PASSWORD = os.getenv("verified_user_password")
# SUPER_ADMIN_EMAIL = os.getenv("super_admin_email")
# SUPER_ADMIN_PASSWORD = os.getenv("super_admin_password")

# def random_email():
#     return f"user{random.randint(10000, 99999)}@test.com"

# def get_token(email, password):
#     resp = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
#     if resp.status_code == 200:
#         return resp.json().get("access_token")
#     return None

# def test_tenant_security():
#     print("--- Starting Tenant Security Tests ---")

#     # 1. Setup: Get tokens and create a target tenant
#     print("1. Setup: Authenticating users...")
#     super_admin_token = get_token(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
#     verified_admin_token = get_token(VERIFIED_USER_EMAIL, VERIFIED_USER_PASSWORD)

#     if not super_admin_token or not verified_admin_token:
#         print("❌ Failed to get necessary tokens. Check credentials.")
#         return

#     # Create a new tenant owned by a regular user
#     owner_email = random_email()
#     owner_password = "StrongPass1!"
#     tenant_data = {
#         "name": "Target Tenant",
#         "domain": f"target-{random.randint(1000,9999)}.com",
#         "owner": {
#             "full_name": "Target Owner",
#             "email": owner_email,
#             "password": owner_password
#         }
#     }
#     resp = requests.post(f"{BASE_URL}/tenants/register", json=tenant_data)
#     if resp.status_code != 201:
#         print(f"❌ Failed to create tenant: {resp.text}")
#         return

#     tenant_id = resp.json()["tenant"]["id"]
#     owner_id = resp.json()["owner"]["id"]
#     owner_token = get_token(owner_email, owner_password)

#     print(f"✔ Tenant created (ID: {tenant_id}) with Owner (ID: {owner_id})")

#     # 2. Test: Owner updates allowed fields (Expect Success)
#     print("\n2. Test: Owner updates allowed fields (name, description)")
#     headers = {"Authorization": f"Bearer {owner_token}"}
#     update_data = {"name": "Updated Target Tenant", "description": "New Description"}
#     resp = requests.put(f"{BASE_URL}/tenants/{tenant_id}", json=update_data, headers=headers)

#     if resp.status_code == 200 and resp.json()["name"] == "Updated Target Tenant":
#         print("✔ Owner successfully updated allowed fields.")
#     else:
#         print(f"❌ Owner failed to update allowed fields. Status: {resp.status_code}")

#     # 3. Test: Owner attempts to update plan_type (Expect Failure - 403)
#     print("\n3. Test: Owner attempts to update strict field 'plan_type'")
#     update_data = {"plan_type": "premium"}
#     resp = requests.put(f"{BASE_URL}/tenants/{tenant_id}", json=update_data, headers=headers)

#     if resp.status_code == 403:
#         print("✔ Security Enforced: Owner blocked from updating plan_type (403).")
#     elif resp.status_code == 200:
#         # Check if plan actually changed (current implementation might ignore it, which is also bad UI but safe-ish,
#         # OR it might update it which is critical failure)
#         if resp.json().get("plan_type") == "premium":
#              print("❌ CRITICAL FAIL: Owner was able to change plan_type!")
#         else:
#              print("⚠ Warning: Request succeeded (200) but plan_type didn't change (Silently ignored). Should be 403.")
#     else:
#         print(f"❌ Unexpected status code: {resp.status_code}")

#     # 4. Test: Unauthorized user (Verified Admin of DIFFERENT tenant) updates details (Expect Failure - 403)
#     print("\n4. Test: Cross-tenant access (Unrelated Admin updates tenant)")
#     headers_unrelated = {"Authorization": f"Bearer {verified_admin_token}"}
#     update_data = {"name": "Hacked Tenant Name"}
#     resp = requests.put(f"{BASE_URL}/tenants/{tenant_id}", json=update_data, headers=headers_unrelated)

#     if resp.status_code == 403:
#         print("✔ Security Enforced: Unrelated admin blocked (403).")
#     elif resp.status_code == 200:
#         print("❌ CRITICAL FAIL: Unrelated admin updated tenant details!")
#     else:
#         print(f"❌ Unexpected status code: {resp.status_code}")

#     # 5. Test: Super Admin updates plan_type (Expect Success)
#     print("\n5. Test: Super Admin updates plan_type")
#     headers_sa = {"Authorization": f"Bearer {super_admin_token}"}
#     update_data = {"plan_type": "enterprise"}
#     resp = requests.put(f"{BASE_URL}/tenants/{tenant_id}", json=update_data, headers=headers_sa)

#     if resp.status_code == 200 and resp.json().get("plan_type") == "enterprise":
#         print("✔ Super Admin successfully updated plan_type.")
#     else:
#         print(f"❌ Super Admin failed to update plan_type. Status: {resp.status_code}, Body: {resp.text}")

#     print("\n--- Tests Completed ---")

# if __name__ == "__main__":
#     test_tenant_security()
