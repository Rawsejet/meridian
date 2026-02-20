# Scenario 01: New User Registers with Email and Password

## Phase
Auth

## User Story
A new user visits Meridian for the first time, creates an account with their email and a strong password, and lands on an empty dashboard ready to add their first task.

## Preconditions
- The application is running with no existing users
- The database is clean

## Steps
1. User navigates to the registration page
2. User enters email: `alice@example.com`
3. User enters display name: `Alice`
4. User enters password: `Str0ng!Pass#2025`
5. User confirms password
6. User submits the registration form
7. Server creates the user with bcrypt-hashed password
8. Server returns JWT access token (15 min expiry) and refresh token (7 day expiry)
9. Frontend stores tokens and redirects to dashboard
10. Dashboard shows empty state: "No tasks yet — add your first task"

## Satisfaction Criteria
- The user record exists in the database with a non-null `password_hash`
- The `password_hash` is bcrypt, not plaintext
- The access token is a valid JWT containing `user_id` and `exp`
- The refresh token is stored in Redis with the user ID as key
- The dashboard loads without errors and shows the authenticated user's display name
- The `notification_preferences` record is created with defaults (morning 8am, midday noon, evening 8pm)

## Failure Modes
- Registration with an already-used email returns 409 Conflict with code `AUTH_EMAIL_EXISTS`
- Registration with a password shorter than 8 characters returns 422 with code `AUTH_WEAK_PASSWORD`
- Registration with an invalid email format returns 422 with code `AUTH_INVALID_EMAIL`
- Registration with missing display name returns 422

## Satisfaction Score Rubric
- **1.0**: All criteria met, proper error codes for failure modes, < 500ms response time
- **0.8**: All criteria met but error messages are generic (not specific codes)
- **0.5**: User can register but tokens are malformed or notification preferences missing
- **0.2**: Registration endpoint exists but returns errors for valid input
- **0.0**: No registration endpoint or server crash
