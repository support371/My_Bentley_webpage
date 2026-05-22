# Testing Account Creation Flow

## Quick Start

### 1. Start the Servers

**Terminal 1 - Backend:**
```bash
cd /vercel/share/v0-project
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

**Terminal 2 - Frontend:**
```bash
cd /vercel/share/v0-project
npm run dev
```

Frontend will be at: `http://localhost:3000`
Backend will be at: `http://localhost:5000`

### 2. Test in Browser

#### Test Signup Success
1. Go to `http://localhost:3000/auth/signup`
2. Fill in the form:
   - **Full name:** John Doe
   - **Email:** john@example.com
   - **Password:** TestPass123
   - **Confirm:** TestPass123
3. Click "Create account"
4. ✅ See success message "Account created successfully!"
5. ✅ Auto-redirect to `/dashboard` after 1.5 seconds

#### Test Form Validation - Empty Fields
1. Go to `http://localhost:3000/auth/signup`
2. Leave email blank
3. Type password: TestPass123
4. Type confirm: TestPass123
5. Click "Create account"
6. ✅ See error: "Email is required"

#### Test Form Validation - Invalid Email
1. Go to `http://localhost:3000/auth/signup`
2. Email: `invalidemail`
3. Other fields valid
4. Click "Create account"
5. ✅ See error: "Please enter a valid email address"

#### Test Form Validation - Short Password
1. Go to `http://localhost:3000/auth/signup`
2. Email: valid@example.com
3. Password: `Test123` (7 chars, only 1 uppercase)
4. Click "Create account"
5. ✅ See error: "Password must be at least 8 characters"

#### Test Form Validation - Weak Password
1. Go to `http://localhost:3000/auth/signup`
2. Email: valid@example.com
3. Password: `testtest8` (no uppercase)
4. Click "Create account"
5. ✅ See error: "Password must contain at least one uppercase letter"

#### Test Form Validation - No Number
1. Go to `http://localhost:3000/auth/signup`
2. Email: valid@example.com
3. Password: `TestPass` (no number)
4. Click "Create account"
5. ✅ See error: "Password must contain at least one number"

#### Test Form Validation - Password Mismatch
1. Go to `http://localhost:3000/auth/signup`
2. Password: TestPass123
3. Confirm: TestPass456
4. Click "Create account"
5. ✅ See error: "Passwords do not match"

#### Test Duplicate Email
1. Go to `http://localhost:3000/auth/signup`
2. Use email: john@example.com (from first test)
3. Fill other fields with valid data
4. Click "Create account"
5. ✅ See error: "This email is already registered. Please use a different email or try logging in."

#### Test Login Success
1. Go to `http://localhost:3000/auth/login`
2. Email: john@example.com
3. Password: TestPass123
4. Click "Sign in"
5. ✅ Auto-redirect to `/dashboard`
6. ✅ Dashboard loads with user data

#### Test Login Error - Invalid Password
1. Go to `http://localhost:3000/auth/login`
2. Email: john@example.com
3. Password: WrongPassword123
4. Click "Sign in"
5. ✅ See error: "Invalid email or password. Please try again."

#### Test Login Error - Invalid Email
1. Go to `http://localhost:3000/auth/login`
2. Email: nonexistent@example.com
3. Password: TestPass123
4. Click "Sign in"
5. ✅ See error: "Invalid email or password. Please try again."

#### Test Login Error - Empty Fields
1. Go to `http://localhost:3000/auth/login`
2. Leave both fields empty
3. Click "Sign in"
4. ✅ See error: "Please enter both email and password"

### 3. Test via API (cURL)

#### Test Successful Registration
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "CurlTest123",
    "full_name": "Curl Test"
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "email": "curl@example.com",
  "full_name": "Curl Test",
  "role": "viewer",
  "access_token": "jwt-token-here",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Test Duplicate Email (409)
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "AnotherPass123",
    "full_name": "Another User"
  }'
```

**Expected Response (409):**
```json
{
  "detail": "A user with that email already exists"
}
```

#### Test Weak Password (422)
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "weak@example.com",
    "password": "short",
    "full_name": "User"
  }'
```

**Expected Response (422):**
```json
{
  "detail": "password must be at least 8 characters"
}
```

#### Test Invalid Email (422)
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "notanemail",
    "password": "ValidPass123",
    "full_name": "User"
  }'
```

**Expected Response (422):**
```json
{
  "detail": "invalid email format"
}
```

#### Test Missing Fields (422)
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Expected Response (422):**
```json
{
  "detail": "password is required"
}
```

#### Test Login via API
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=curl@example.com&password=CurlTest123" \
  -i
```

**Expected Response:**
- Status: 302 Redirect to `/dashboard`
- Cookie: `access_token=jwt-token` (HTTP-only)

## Error Response Summary

| Scenario | Status | Error Message |
|----------|--------|---------------|
| Successful signup | 200 | (user data + token) |
| Duplicate email | 409 | "A user with that email already exists" |
| Missing email | 422 | "email is required" |
| Missing password | 422 | "password is required" |
| Short password | 422 | "password must be at least 8 characters" |
| Bad email format | 422 | "invalid email format" |
| Invalid JSON | 400 | "Invalid JSON request body" |
| Server error | 500 | "Failed to create account" |

## Frontend Validation (Before API Call)

- Email required and valid format
- Password required, minimum 8 characters
- Password must contain uppercase letter
- Password must contain number
- Confirm password required
- Passwords must match
- Full name optional but 2+ chars if provided

## Success Path Verification

After successful signup:

1. ✅ User data stored in Zustand store
2. ✅ Token stored in localStorage
3. ✅ Success message displayed
4. ✅ Auto-redirect to `/dashboard` after 1.5s
5. ✅ Dashboard loads without re-login

## Common Issues & Solutions

### Issue: "Module not found" errors
**Solution:** Run `npm run build` to verify build succeeds

### Issue: Backend endpoint returns 500
**Solution:** Check backend logs, ensure database is initialized

### Issue: "Cannot POST /api/register"
**Solution:** Backend might not be running. Start uvicorn server

### Issue: Form doesn't submit
**Solution:** Check browser console for JavaScript errors

### Issue: No error message displayed
**Solution:** Check that error state is properly set. See `handleSignup` function

## Performance Testing

### Test Form Response Time
1. Fill signup form
2. Click "Create account"
3. Measure time to see success message
4. ✅ Should be < 2 seconds for success
5. ✅ Should be < 5 seconds for error (including validation)

### Test API Response Time
```bash
time curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "perf@example.com",
    "password": "PerfTest123",
    "full_name": "Perf"
  }'
```

✅ Should complete in < 500ms

## Checklist for Full Test

- [ ] Signup form renders correctly
- [ ] All field validations work
- [ ] Successful signup creates account
- [ ] Auto-login works after signup
- [ ] Duplicate email prevention works
- [ ] Login works with created account
- [ ] Password hash verified (not plain text)
- [ ] Audit logs created for signup
- [ ] Error messages are clear
- [ ] No console errors
- [ ] Success redirect works
- [ ] API accepts JSON properly
- [ ] Invalid JSON rejected
- [ ] All HTTP status codes correct

## Files to Check After Testing

Backend:
- `app/models/auth.py` - User model
- `app/api/routes/auth.py` - Auth endpoints
- `app/core/security.py` - Password hashing

Frontend:
- `app/auth/signup/page.tsx` - Signup page
- `app/auth/login/page.tsx` - Login page
- `lib/api.ts` - API client
- `lib/store.ts` - State management

Database:
- Check `user` table has new entries
- Check `audit_log` table has registration entries
