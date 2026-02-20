# Scenario 02: User Logs In with Google OAuth

## Phase
Auth

## User Story
A user who prefers not to create a password clicks "Sign in with Google," completes the OAuth flow, and arrives at their dashboard. If it's their first time, an account is created automatically. If they've signed in before, they resume where they left off.

## Preconditions
- Google OAuth client ID and secret are configured
- The OAuth callback URL is registered with Google

## Steps — First-Time User
1. User clicks "Sign in with Google"
2. Frontend redirects to `GET /auth/google` which returns a Google OAuth authorization URL
3. User completes Google consent screen (mocked in tests)
4. Google redirects to `GET /auth/google/callback?code=...&state=...`
5. Backend exchanges code for Google tokens, retrieves user profile (email, name, avatar)
6. Backend creates a new user with `google_id` set and `password_hash` NULL
7. Backend returns JWT tokens
8. Frontend redirects to dashboard

## Steps — Returning User
1. Same OAuth flow as above
2. Backend finds existing user by `google_id`
3. Backend updates `avatar_url` if changed
4. Backend returns JWT tokens for the existing user
5. User sees their existing tasks and plans

## Satisfaction Criteria
- First-time OAuth creates a user with `google_id` set and `password_hash = NULL`
- Returning OAuth matches by `google_id`, not email (handles email changes)
- The user cannot log in with email/password if they only have a Google account (no password set)
- State parameter in OAuth flow prevents CSRF
- Tokens returned are identical in format to email/password login tokens
- If Google returns an email that matches an existing email/password user, return an error suggesting they link accounts (do not silently merge)

## Failure Modes
- Invalid or expired OAuth code returns 401 with code `AUTH_OAUTH_FAILED`
- Missing state parameter returns 400 with code `AUTH_OAUTH_INVALID_STATE`
- Google API unreachable returns 502 with code `AUTH_OAUTH_PROVIDER_ERROR`

## Satisfaction Score Rubric
- **1.0**: Both first-time and returning flows work, CSRF protection present, email collision handled
- **0.8**: Flows work but CSRF protection missing or email collision silently merges
- **0.5**: OAuth endpoint exists but only first-time OR returning flow works
- **0.2**: OAuth endpoint exists but redirects fail or tokens are missing
- **0.0**: No OAuth implementation
