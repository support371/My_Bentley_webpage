# Account Creation & Authentication Flow

## Overview

This guide documents the complete account creation and authentication flow for the iTwin Ops platform.

## API Endpoints

### POST `/api/register` - Create Account
Public endpoint for new user registration.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Validation Rules:**
- `email`: Required, must be valid email format
- `password`: Required, minimum 8 characters
- `full_name`: Optional, minimum 2 characters if provided

**Success Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "viewer",
  "access_token": "jwt_token",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**

| Status | Detail | Reason |
|--------|--------|--------|
| 400 | Invalid JSON request body | Malformed JSON |
| 409 | A user with that email already exists | Duplicate email |
| 422 | email is required | Missing email |
| 422 | password is required | Missing password |
| 422 | password must be at least 8 characters | Password too short |
| 422 | invalid email format | Bad email format |
| 500 | Failed to create account | Server error |

### POST `/login` - Login
Authenticates user with email and password.

**Request (Form Data):**
```
email: user@example.com
password: SecurePass123
```

**Success Response (302 Redirect):**
- Redirects to `/dashboard`
- Sets HTTP-only cookie: `access_token`

**Error Responses:**
- 401: "Invalid email or password"
- 403: "Account is disabled. Contact your admin."

### POST `/api/users` - Admin User Creation
Admin endpoint to create users (includes role assignment).

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "role": "viewer"
}
```

**Role Options:**
- `viewer` - Read-only access
- `operator` - Can manage operations
- `admin` - Full administrative access

## Frontend Implementation

### Signup Page (`/app/auth/signup/page.tsx`)

The signup page includes:
- **Form Validation**
  - Email format validation (regex)
  - Password strength requirements (8+ chars, 1 uppercase, 1 number)
  - Password confirmation matching
  - Full name validation (2+ characters)

- **Error Handling**
  - Field-level error messages
  - General error display
  - Specific error handling for common cases (409 duplicate email, 422 validation)
  - Success message with redirect

- **User Experience**
  - Disabled form during submission
  - Loading state on button
  - Auto-focus and error clearing on input
  - Link to login page for existing users

### Login Page (`/app/auth/login/page.tsx`)

The login page includes:
- **Form Validation**
  - Email and password required
  - Basic presence checks

- **Error Handling**
  - 401: "Invalid email or password"
  - 403: "Your account is disabled"
  - Network errors: Clear error message
  - Field-level validation

- **User Experience**
  - Loading state during submission
  - Disabled form during submission
  - Link to signup page for new users

## API Client (`/lib/api.ts`)

Provides these methods:

```typescript
authAPI.register(email, password, fullName)
authAPI.login(email, password)
authAPI.logout()
```

Features:
- Automatic token handling
- Request/response interceptors
- Bearer token in Authorization header
- Automatic logout on 401

## State Management (`/lib/store.ts`)

Zustand store with:
- `user` - Current user object
- `token` - JWT token
- `isLoading` - Loading state
- `error` - Error message
- Methods: `setUser()`, `setToken()`, `setError()`, `setIsLoading()`, `reset()`

## Common Issues & Solutions

### Issue: "Invalid JSON request body"
**Cause:** Malformed JSON in request
**Solution:** Check Content-Type header is application/json

### Issue: "email already exists" (409)
**Cause:** Email is already registered
**Solution:** User should log in instead, or use different email

### Issue: "password must be at least 8 characters"
**Cause:** Password too short
**Solution:** Require 8+ characters with uppercase and number

### Issue: Account created but not logged in
**Cause:** Access token not set properly
**Solution:** Check token is stored in localStorage and state

### Issue: Redirect not working after signup
**Cause:** Next.js router navigation failed
**Solution:** Check useRouter import, ensure router.push() is called

## Testing the Flow

### Test Signup Success:
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'
```

Expected: 200/201 with token and user data

### Test Duplicate Email:
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'
```

Expected: 409 with "already exists" message

### Test Weak Password:
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "weak",
    "full_name": "Test User"
  }'
```

Expected: 422 with password requirement message

## Security Considerations

1. **Password Hashing**: Passwords are hashed with bcrypt + SHA-256
2. **Token Security**: JWT tokens expire based on JWT_EXPIRE_MINUTES setting
3. **HTTPS Only**: In production, set COOKIE_SECURE=true
4. **SameSite Policy**: Cookies use SameSite=lax for CSRF protection
5. **Audit Logging**: All registration and login attempts are logged

## Environment Configuration

Required environment variables:

```env
# Backend
SECRET_KEY=your-secret-key
JWT_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./app.db

# Frontend (optional, defaults to localhost:5000)
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Audit Logging

All authentication events are logged to the audit_log table:

- `register.success` - Successful account creation
- `register.duplicate` - Attempted registration with existing email
- `register.failed` - Registration error
- `login.success` - Successful login
- `login.failed` - Failed login attempt
- `login.blocked` - Login blocked (account disabled)
- `logout` - User logout

Logs include: action, user_id, ip_address, timestamp, detail
