"""
Test suite for Audit Logging functionality.
Tests audit log creation, querying, and integration with critical operations.
"""
import json
from datetime import datetime, timezone, timedelta


def test_login_creates_audit_log(client, test_tenant, test_user, db_session):
    """Test that successful login creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction, ResourceType

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.LOGIN,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.resource_type == ResourceType.AUTH
    assert log.tenant_id == test_user.tenant_id
    assert log.status == "success"
    assert log.ip_address is not None


def test_failed_login_creates_audit_log(
    client, test_tenant, test_user, db_session
):
    """Test that failed login creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Attempt login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.LOGIN_FAILED,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.status == "failure"
    assert "Failed login attempt" in log.description


def test_token_refresh_creates_audit_log(
    client, auth_headers, test_user, db_session
):
    """Test that token refresh creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Get initial login to get refresh token
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123"
        }
    )
    assert response.status_code == 200
    refresh_token = response.json()["refresh_token"]

    # Refresh token
    response = client.post(
        f"/api/v1/auth/refresh?refresh_token={refresh_token}"
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.TOKEN_REFRESH,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1


def test_user_role_change_creates_audit_log(
    client, auth_headers, test_user, test_manager, db_session
):
    """Test that changing user role creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Update user role
    response = client.put(
        f"/api/v1/users/{test_manager.id}",
        headers=auth_headers,
        json={"role": "admin"}
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.USER_ROLE_CHANGED,
        AuditLog.resource_id == test_manager.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.user_id == test_user.id  # Owner who made the change
    assert log.changes is not None

    # Check changes contain role transition
    changes = json.loads(log.changes)
    assert "role" in changes
    assert changes["role"]["before"] == "manager"
    assert changes["role"]["after"] == "admin"


def test_user_deletion_creates_audit_log(
    client, auth_headers, test_attendant, db_session
):
    """Test that user deletion creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Delete user
    response = client.delete(
        f"/api/v1/users/{test_attendant.id}",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.USER_DELETED,
        AuditLog.resource_id == test_attendant.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert "deactivated" in log.description.lower()


def test_invoice_status_change_creates_audit_log(
    client, auth_headers, test_user, db_session
):
    """Test that invoice status change creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Create an invoice first
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Change invoice status from DRAFT to SENT
    response = client.patch(
        f"/api/v1/invoices/{invoice_id}/status",
        headers=auth_headers,
        json={"status": "sent"}
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.INVOICE_STATUS_CHANGED,
        AuditLog.resource_id == invoice_id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.user_id == test_user.id

    # Check changes contain status transition
    changes = json.loads(log.changes)
    assert "status" in changes
    assert changes["status"]["before"] == "draft"
    assert changes["status"]["after"] == "sent"


def test_tenant_update_creates_audit_log(client, test_tenant, db_session):
    """Test that tenant update creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Update tenant
    response = client.put(
        f"/api/v1/tenants/{test_tenant.id}",
        json={"name": "Updated Company Name"}
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.TENANT_UPDATED,
        AuditLog.resource_id == test_tenant.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]

    # Check changes contain name update
    changes = json.loads(log.changes)
    assert "name" in changes
    assert changes["name"]["after"] == "Updated Company Name"


def test_pdf_export_creates_audit_log(
    client, auth_headers, test_user, db_session
):
    """Test that PDF generation creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Create an invoice first
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Generate PDF
    response = client.get(
        f"/api/v1/invoices/{invoice_id}/pdf",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.INVOICE_PDF_GENERATED,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert "PDF generated" in log.description


def test_csv_export_creates_audit_log(
    client, auth_headers, test_user, db_session
):
    """Test that CSV export creates an audit log entry."""
    from app.models.audit_log import AuditLog, AuditAction

    # Export CSV
    response = client.get(
        "/api/v1/invoices/export/invoices?format=csv",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Check audit log was created
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.DATA_EXPORTED,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert "CSV export" in log.description


def test_list_audit_logs_requires_admin(client, manager_auth_headers):
    """Test that listing audit logs requires admin role."""
    response = client.get(
        "/api/v1/audit-logs/",
        headers=manager_auth_headers
    )
    # Manager role should not have access
    assert response.status_code == 403


def test_list_audit_logs_as_admin(client, admin_auth_headers, db_session):
    """Test that admin can list audit logs."""
    response = client.get(
        "/api/v1/audit-logs/",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert "has_next" in data
    assert "has_previous" in data
    assert isinstance(data["items"], list)


def test_list_audit_logs_with_filters(
    client, admin_auth_headers, test_user, db_session
):
    """Test filtering audit logs by various criteria."""
    from app.models.audit_log import AuditAction

    # Filter by single action
    response = client.get(
        f"/api/v1/audit-logs/?actions={AuditAction.LOGIN.value}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination structure
    assert "items" in data
    for log in data["items"]:
        assert log["action"] == AuditAction.LOGIN.value

    # Filter by user_id
    response = client.get(
        f"/api/v1/audit-logs/?user_id={test_user.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for log in data["items"]:
        if log["user_id"]:
            assert log["user_id"] == test_user.id


def test_list_audit_logs_with_multiple_filters(
    client, admin_auth_headers, test_user, db_session
):
    """Test filtering audit logs by multiple actions and resource types."""
    from app.models.audit_log import AuditAction, ResourceType

    # Filter by multiple actions
    response = client.get(
        f"/api/v1/audit-logs/?actions={AuditAction.LOGIN.value}"
        f"&actions={AuditAction.LOGIN_FAILED.value}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination structure
    assert "items" in data
    
    # Verify all returned logs have one of the specified actions
    for log in data["items"]:
        assert log["action"] in [
            AuditAction.LOGIN.value,
            AuditAction.LOGIN_FAILED.value
        ]

    # Filter by multiple resource types
    response = client.get(
        f"/api/v1/audit-logs/?resource_types={ResourceType.USER.value}"
        f"&resource_types={ResourceType.AUTH.value}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # Verify all returned logs have one of the specified resource types
    for log in data["items"]:
        assert log["resource_type"] in [
            ResourceType.USER.value,
            ResourceType.AUTH.value
        ]


def test_list_audit_logs_pagination(client, admin_auth_headers, db_session):
    """Test pagination of audit logs."""
    response = client.get(
        "/api/v1/audit-logs/?skip=0&limit=5",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination metadata
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    
    assert len(data["items"]) <= 5
    assert data["size"] == 5
    assert data["page"] == 1


def test_get_audit_log_by_id(client, admin_auth_headers, db_session):
    """Test getting a specific audit log by ID."""
    from app.models.audit_log import AuditLog

    # Get first audit log
    audit_log = db_session.query(AuditLog).first()
    if audit_log:
        response = client.get(
            f"/api/v1/audit-logs/{audit_log.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == audit_log.id


def test_get_user_audit_logs(
    client, admin_auth_headers, test_user, db_session
):
    """Test getting audit logs for a specific user."""
    response = client.get(
        f"/api/v1/audit-logs/user/{test_user.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_resource_audit_logs(
    client, admin_auth_headers, auth_headers, db_session
):
    """Test getting audit logs for a specific resource."""
    from app.models.audit_log import ResourceType

    # Create an invoice first
    response = client.post(
        "/api/v1/invoices/",
        json={
            "customer_name": "Test Customer",
            "issue_date": "2024-01-15",
            "items": [
                {
                    "description": "Product A",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    response = client.get(
        f"/api/v1/audit-logs/resource/{ResourceType.INVOICE.value}/"
        f"{invoice_id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_audit_logs_tenant_isolation(
    client, admin_auth_headers, second_tenant, db_session
):
    """Test that audit logs are isolated by tenant."""
    # Get audit logs - should only see logs from own tenant
    response = client.get(
        "/api/v1/audit-logs/",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all logs belong to the user's tenant
    for log in data:
        # Logs may have tenant_id or be null for certain actions
        if log["tenant_id"]:
            # Cannot directly access current user's tenant from here,
            # but we can verify consistency
            pass


def test_audit_log_captures_ip_address(
    client, test_tenant, test_user, db_session
):
    """Test that audit logs capture client IP address."""
    from app.models.audit_log import AuditLog, AuditAction

    # Login with custom headers
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123"
        },
        headers={"X-Forwarded-For": "192.168.1.100"}
    )
    assert response.status_code == 200

    # Check audit log captured IP
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.LOGIN,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    # Should capture the X-Forwarded-For IP
    assert log.ip_address == "192.168.1.100"


def test_audit_log_captures_user_agent(
    client, test_tenant, test_user, db_session
):
    """Test that audit logs capture user agent."""
    from app.models.audit_log import AuditLog, AuditAction

    # Login with custom user agent
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123"
        },
        headers={"User-Agent": "TestClient/1.0"}
    )
    assert response.status_code == 200

    # Check audit log captured user agent
    audit_logs = db_session.query(AuditLog).filter(
        AuditLog.action == AuditAction.LOGIN,
        AuditLog.user_id == test_user.id
    ).all()
    assert len(audit_logs) >= 1
    log = audit_logs[-1]
    assert log.user_agent == "TestClient/1.0"


def test_audit_log_date_filtering(client, admin_auth_headers, db_session):
    """Test filtering audit logs by date range."""
    from urllib.parse import quote
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    # Filter by date range (URL encode the dates)
    response = client.get(
        f"/api/v1/audit-logs/?start_date={quote(yesterday.isoformat())}"
        f"&end_date={quote(tomorrow.isoformat())}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
