# Scenario 03: Token Refresh and Expiry

## Phase
Auth

## User Story
A user has been using Meridian for an hour. Their access token expires. The frontend silently refreshes it using the refresh token without interrupting their workflow. After 7 days, the refresh token also expires and the user must log in again.

## Preconditions
- User `alice@example.com` is registered and logged in
- Access token has 15-minute expiry, refresh token has 7-day expiry

## Steps — Silent Refresh
1. User has been active for 16 minutes
2. User tries to create a task
3. Frontend sends `POST /tasks` with the expired access token
4. Backend returns 401 with code `AUTH_TOKEN_EXPIRED`
5. Frontend's Axios interceptor catches the 401
6. Frontend sends `POST /auth/refresh` with the refresh token
7. Backend validates the refresh token against Redis, issues new access + refresh tokens
8. Backend invalidates the old refresh token in Redis (rotation)
9. Frontend retries the original `POST /tasks` with the new access token
10. Task creation succeeds transparently

## Steps — Full Expiry
1. User returns after 8 days without activity
2. Both tokens are expired
3. Frontend attempts refresh, gets 401 with code `AUTH_REFRESH_EXPIRED`
4. Frontend clears stored tokens and redirects to login page

## Steps — Stolen Refresh Token
1. Attacker obtains a refresh token
2. Attacker uses it to get new tokens — this succeeds
3. Original user tries to refresh — their (now-invalidated) refresh token is rejected
4. Original user is forced to re-login
5. Attacker's new tokens remain valid until they expire naturally

## Satisfaction Criteria
- Access tokens expire in exactly 15 minutes (±30 seconds)
- Refresh tokens expire in exactly 7 days
- Refresh token rotation: each refresh invalidates the old token and issues a new one
- Old refresh tokens cannot be reused (prevents replay attacks)
- The Axios interceptor retries the original request, not just refreshes silently
- No more than 1 concurrent refresh request per client (queue parallel 401s behind a single refresh)

## Failure Modes
- Using a revoked refresh token returns 401 with `AUTH_REFRESH_REVOKED`
- Malformed JWT returns 401 with `AUTH_TOKEN_INVALID`
- Missing Authorization header returns 401 with `AUTH_TOKEN_MISSING`

## Satisfaction Score Rubric
- **1.0**: Silent refresh works, rotation implemented, concurrent requests handled, stolen token scenario addressed
- **0.8**: Silent refresh works with rotation but concurrent request deduplication missing
- **0.5**: Refresh works but no token rotation (old tokens still valid)
- **0.2**: Refresh endpoint exists but frontend doesn't auto-retry
- **0.0**: No refresh mechanism
