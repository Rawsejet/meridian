# Scenario 20: API Design for Future iOS Client Compatibility

## Phase
Integration

## User Story
An iOS developer (future phase) should be able to consume the Meridian API without any backend changes. This scenario validates that the API design is mobile-friendly by checking for common mobile-hostile patterns.

## Preconditions
- The full API is implemented and documented via OpenAPI/Swagger

## Checks — Not Steps (This is a Design Validation Scenario)

### Authentication
1. Auth uses JWT Bearer tokens, not cookies — mobile apps can't rely on cookie jars
2. Refresh token flow works with raw HTTP (no browser redirects)
3. Google OAuth returns tokens via a deeplink-friendly callback, not a web redirect
4. The API never sets `Set-Cookie` headers on auth responses

### Request/Response Format
5. All responses use consistent JSON shapes (no HTML mixed in)
6. All dates are ISO 8601 strings (not Unix timestamps, not locale-formatted)
7. UUIDs are lowercase hyphenated strings
8. Pagination uses cursor tokens (not page numbers, which don't work well with real-time data on mobile)
9. Error responses follow the standard `{"detail": {"code": "...", "message": "..."}}` format
10. No endpoint returns HTML or redirects to HTML

### Push Notifications
11. `push_subscriptions` table includes a `user_agent` or `platform` field to distinguish web vs iOS
12. The notification service has an interface/abstraction for delivery — web push is one implementation, APNs would be another
13. Notification payload format is generic enough that APNs can consume it (title + body + data dict)

### Real-Time (Future)
14. The OpenAPI spec includes a placeholder WebSocket endpoint for real-time plan sync
15. The endpoint doesn't need to be implemented, just documented

### Performance
16. List endpoints support `If-None-Match` / `ETag` headers for caching (mobile clients cache aggressively)
17. Response sizes are reasonable (<50KB for typical list responses)

## Satisfaction Criteria
- All 17 checks pass
- An iOS developer reading the OpenAPI spec can build a client without asking questions about the backend
- No endpoint has a hidden dependency on browser behavior (cookies, redirects, CORS preflight)

## Satisfaction Score Rubric
- **1.0**: All 17 checks pass, OpenAPI spec is complete and accurate
- **0.8**: Most checks pass but ETag support is missing or WebSocket placeholder isn't documented
- **0.6**: Core API is mobile-friendly but push notification abstraction is web-only
- **0.4**: API works but uses cookies for auth or returns HTML errors
- **0.2**: API works but OpenAPI spec is incomplete or missing
- **0.0**: API has hard dependencies on browser behavior
