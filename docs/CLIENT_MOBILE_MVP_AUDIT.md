# Client-Mobile MVP Integration Audit

Scope: verify the backend contract, compare it against the mobile app's user and organization management flows, and document what is fully aligned, partially aligned, or missing for MVP deployment.

Sources reviewed:
- Backend documentation: [README.md](../README.md), [docs/SECURITY.md](SECURITY.md), [docs/EMAIL_VERIFICATION.md](EMAIL_VERIFICATION.md), [PRODUCTION_READINESS_ASSESSMENT.md](../PRODUCTION_READINESS_ASSESSMENT.md)
- Backend implementation: auth, users, tenants, schemas, dependencies, and security modules in `app/`
- Backend tests: focused auth/user/tenant tests under `tests/`
- Mobile app implementation and tests in `~/portfolio/rechive/RechiveApp`

Validation performed:
- Ran focused backend tests under the project virtual environment with `pytest tests/test_auth.py tests/test_users.py tests/test_tenants.py -q`.
- Read the backend endpoint implementations and the mobile app screens/services that consume them.

## Executive Summary

The backend is stronger than the mobile client in several important lifecycle areas. The backend enforces the core security rules centrally, but the mobile app currently assumes some flows that the backend does not fully implement or does not expose in the way the client expects.

The project is not yet MVP-ready as a combined system because there are still contract mismatches and one likely missing backend capability. The highest-priority issues are:

- The mobile app expects a force-password-change endpoint, but I could not find an implementation in the backend code I reviewed.
- The mobile app allows admin editing of organization settings, but the backend only allows superadmins or active tenant owners to update tenants.
- The mobile app truncates user lists at 100 items and discards the backend pagination metadata.
- The mobile verification screens are informational only; they do not complete the backend email verification flow.

## Backend Behavior vs Mobile Usage

### 1. Authentication and tenant selection

Backend behavior:
- `POST /api/v1/auth/login` supports both single-tenant and multi-tenant responses.
- `POST /api/v1/auth/select-tenant` re-authenticates the user for the selected organization.
- The backend returns `requires_password_change` for owner-created users who must rotate their temporary password.

Mobile usage:
- `LoginScreen` correctly handles single-tenant and multi-tenant login responses.
- `TenantSelectionScreen` correctly calls the select-tenant endpoint and passes the selected tenant ID plus password.

Assessment:
- This part is aligned and is one of the better-integrated flows in the app.

### 2. Email verification

Backend behavior:
- `POST /api/v1/auth/verify-email` exists and returns new tokens after verification.
- `POST /api/v1/auth/resend-verification-email` exists and is rate limited.
- `require_verified_email` is enforced centrally for protected paths, so verified email is not optional in the backend.

Mobile usage:
- The mobile app has verification pending/success screens.
- The screens are informational and do not appear to call the backend verification endpoint.
- The onboarding flow passes `tenantId` and `ownerId` to `EmailVerificationPending`, but that screen only consumes `email`.

Assessment:
- Partial integration only.
- The client presents the UX for verification, but the actual verification lifecycle is not completed on-device.

Recommendation:
- The best approach is to wire the verification screen to the backend verify-email and resend endpoints, rather than relying on manual user instructions.
- This is preferable to keeping verification as a static info page because the backend already enforces verification and the client should not pretend the flow is complete when it is not.

### 3. Forced password change

Backend behavior:
- The backend stores `must_change_password` on owner-created users and blocks normal access until the password is changed.
- `get_current_user` and `require_verified_email` enforce the password-change gate centrally.
- I could not locate an implemented `/api/v1/auth/force-change-password` route or any equivalent password-change endpoint in the backend sources I reviewed.

Mobile usage:
- The mobile app includes a force-password-change screen and `AuthService.forceChangePassword(...)`.
- That client code assumes a backend endpoint exists.

Assessment:
- This is a major integration gap.
- The mobile client is implementing a workflow around a backend capability that is not actually present in the checked backend code.

Recommendation:
- The best fix is to implement the missing backend endpoint first, then keep the mobile screen as the thin presentation layer for that backend contract.
- This is better than changing the mobile client to piggyback on another endpoint because the backend is already enforcing the gate and the flow needs a single explicit API contract.

### 4. User management

Backend behavior:
- `GET /api/v1/users/` is tenant-scoped and paginated.
- `GET /api/v1/users/{user_id}`, `PUT /api/v1/users/{user_id}`, and `DELETE /api/v1/users/{user_id}` are owner-only.
- Owner-created users are pre-verified and marked `must_change_password=True`.

Mobile usage:
- `UsersListScreen`, `UserDetailScreen`, `AddUserScreen`, and `EditUserScreen` are broadly consistent with the owner-only model.
- The mobile user service requests only the first page and strips pagination metadata.
- The mobile screens do not implement paging or load-more behavior.

Assessment:
- The permissions model is aligned.
- The list handling is incomplete and will fail for tenants with more than 100 users.

Recommendation:
- Add pagination support in the client rather than increasing the page size.
- This is the best option because the backend already provides pagination metadata and enforces a maximum page size of 100.

### 5. Organization settings

Backend behavior:
- `GET /api/v1/tenants/{tenant_id}` and `GET /api/v1/tenants/` are currently unauthenticated in the code I reviewed.
- `PUT /api/v1/tenants/{tenant_id}` requires either superadmin privileges or an active owner of that tenant.
- Admin users are not permitted to update tenant settings.

Mobile usage:
- `OrganizationSettingsScreen` and `EditOrganizationSettingsScreen` show organization data and allow editing for Owner or Admin.
- The screens block editing when the user is not verified, which is consistent with the backend's verification requirement.
- The admin edit allowance is not consistent with the backend authorization rule.

Assessment:
- Read access is easy for the client but too open on the backend side if these endpoints are meant to be private.
- The edit screen is too permissive on the client side and will generate avoidable 403 responses for admins.

Recommendation:
- For MVP, align the UI to owner-only editing unless there is a deliberate product decision to support admin edits.
- This is better than letting admins reach a blocked action because the backend already treats tenant update as owner/superadmin scope.
- If tenant read endpoints are intended to remain public, document that explicitly; otherwise, add auth/tenant checks.

### 6. Login and session lifecycle

Backend behavior:
- JWT access and refresh tokens are central to the app.
- Token refresh is handled via `/api/v1/auth/refresh`.
- Token and user state are expected to stay consistent with backend rules for inactive users, deactivated tenants, and verification gates.

Mobile usage:
- `AuthContext` centralizes token storage and refresh correctly.
- `AppNavigator` correctly switches based on auth state and password-change state.
- `HomeScreen` has a stale focus-refresh dependency issue, so profile data can lag after changes.

Assessment:
- The session architecture is sound.
- The client still has at least one stale-state bug that can show outdated profile data.

## Verified Gaps

These are the highest-confidence issues after checking the backend code and tests:

1. Missing backend force-password-change endpoint.
2. Mobile verification flow does not complete backend email verification.
3. Mobile organization edit permissions are broader than backend authorization.
4. Mobile user list does not honor backend pagination.
5. Tenant read endpoints are open in the backend implementation I reviewed.

## Why These Recommendations Are Best

1. Implementing the missing backend capability is better than forcing the mobile app to work around it.
- The backend already owns lifecycle enforcement.
- A single explicit API contract is less fragile than inventing a workaround in the client.

2. Constraining the mobile UI to backend permissions is better than letting the user reach actions that will fail.
- It removes avoidable 403 handling.
- It makes the UX honest about what the backend actually allows.

3. Using backend pagination is better than fetching a large fixed page.
- It matches the server's design.
- It scales to larger tenants without redesigning the API.

4. Completing verification on-device is better than displaying instructional screens only.
- The backend requires verification.
- The user journey becomes deterministic and testable.

## MVP Readiness Judgment

Backend-only judgment:
- The backend looks substantially more production-ready than the mobile client.
- It has the expected security controls, RBAC, audit logging, rate limiting, and tenant isolation patterns.

System-level judgment:
- The combined mobile + backend system is not yet MVP-ready.
- The system is blocked by contract gaps and permission mismatches, not by missing core business logic.

## Recommended Fix Order

1. Implement or confirm the backend force-password-change endpoint and document its request/response contract.
2. Wire mobile email verification to the real backend verification flow.
3. Restrict organization editing in the mobile UI to owner/superadmin behavior that matches the backend.
4. Add pagination/infinite scrolling in the mobile user list.
5. Decide whether tenant read endpoints should be public or authenticated, and document that decision clearly.

## Notes for Documentation Follow-Up

- If the backend team wants the verification and password-change flows to be production-ready, the API docs should include exact mobile integration examples.
- If the mobile app is the primary client, the backend should keep route names and payloads stable and documented to avoid repeating these contract mismatches.
- The strongest long-term outcome is a shared integration contract document covering auth, verification, tenant selection, user management, and organization settings.