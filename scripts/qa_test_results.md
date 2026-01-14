# AuditBrain API QA Test Results

**Date**: 2026-01-14 11:09:50  
**Base URL**: http://localhost:8000

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✓ Passed | 18 | 100.0% |
| ✗ Failed | 0 | 0.0% |
| ⚠ Warnings | 0 | 0.0% |
| ○ Skipped | 0 | 0.0% |
| **Total** | **18** | **100%** |

## Test Results by Phase


### Authentication

| Status | Method | Endpoint | Message |
|--------|--------|----------|----------|
| ✓ | POST | `/api/auth/login/` | Correctly rejected invalid credentials |
| ✓ | POST | `/api/auth/login/` | Login successful, tokens received |
| ✓ | POST | `/api/auth/token/verify/` | Token verified successfully |
| ✓ | POST | `/api/auth/token/refresh/` | Token refreshed successfully |
| ✓ | GET | `/api/auth/profile/` | Profile retrieved successfully |
| ✓ | GET | `/api/auth/users/` | Users list retrieved (25 users) |
| ✓ | GET | `/api/auth/users/` | All 3 filter tests passed |

### Audits

| Status | Method | Endpoint | Message |
|--------|--------|----------|----------|
| ✓ | GET | `/api/audits/` | Audits retrieved successfully |
| ✓ | GET | `/api/audit-types/` | Audit types retrieved successfully |
| ✓ | GET | `/api/events/` | Events retrieved successfully |
| ✓ | GET | `/api/evidences/` | Evidences retrieved successfully |
| ✓ | GET | `/api/audits/` | Correctly returns 401 for unauthenticated request |

### Reports

| Status | Method | Endpoint | Message |
|--------|--------|----------|----------|
| ✓ | GET | `/api/reports/audits/summary/` | Audit summary retrieved |
| ✓ | GET | `/api/reports/audits/by-period/` | All period report tests passed |
| ✓ | GET | `/api/reports/audits/by-user/` | Audit by user report retrieved |
| ✓ | GET | `/api/reports/events/summary/` | Events summary retrieved |
| ✓ | GET | `/api/reports/evidences/summary/` | Evidences summary retrieved |

### Error Handling

| Status | Method | Endpoint | Message |
|--------|--------|----------|----------|
| ✓ | GET | `/api/audits/99999999/` | Correctly returns 404 for non-existent resource |
