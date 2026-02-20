# Scenario 05: Cross-User Task Isolation

## Phase
Tasks

## User Story
Alice and Bob both use Meridian. Neither can see, modify, or infer the existence of the other's tasks, even by guessing task IDs.

## Preconditions
- Alice is registered and authenticated
- Bob is registered and authenticated
- Alice has 3 tasks, Bob has 2 tasks

## Steps
1. Alice lists her tasks → sees exactly 3
2. Bob lists his tasks → sees exactly 2
3. Alice notes the UUID of one of her tasks: `task_alice_1`
4. Bob tries `GET /tasks/{task_alice_1}` → receives 404 (NOT 403)
5. Bob tries `PATCH /tasks/{task_alice_1}` with `{"title": "hacked"}` → receives 404
6. Bob tries `DELETE /tasks/{task_alice_1}` → receives 404
7. Alice's task remains unchanged
8. Bob tries `GET /tasks?category=work` → returns only Bob's work tasks, never Alice's
9. Total task count in database is 5 (3 + 2), but neither user can see the full count

## Satisfaction Criteria
- All task endpoints filter by `user_id` from the JWT, never from the request body or URL
- Accessing another user's task returns 404, not 403 (prevents ID enumeration)
- Database queries always include `WHERE user_id = :authenticated_user_id`
- No endpoint returns a total count of all tasks across users
- Pagination cursors are scoped to the user (cannot be reused by another user)

## Failure Modes
- If any endpoint returns 403 instead of 404 for cross-user access, that leaks information
- If any query is missing the user_id filter, tasks leak across users

## Satisfaction Score Rubric
- **1.0**: Complete isolation with 404 (not 403) for all cross-user attempts
- **0.7**: Isolation works but returns 403 instead of 404
- **0.3**: Some endpoints leak cross-user data
- **0.0**: No user scoping on task queries
