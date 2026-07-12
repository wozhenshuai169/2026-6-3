# Backend authentication API changes

## Authentication

Protected endpoints require the Authorization header with value Bearer <token>.

Tokens expire after SESSION_TTL_SECONDS seconds. The default is 24 hours.
POST /api/auth/logout invalidates the current token immediately.

### Register

POST /api/auth/register accepts userName, password, and role.
Public registration accepts tourist and guide. It never accepts admin.
The response contains userId, userName, role, token, and expiresAt.

### Login and current user

- POST /api/auth/login accepts userName and password.
- GET /api/auth/me returns the authenticated user.
- POST /api/auth/logout revokes the current token.

Passwords are stored as salted PBKDF2-SHA256 hashes, never as plaintext.

## Authorization rules

- Only guide or admin can create a room.
- The room creator is automatically the leader and the first member.
- A user must join a room before reading its state or using its AI features.
- Only the room leader can update the current spot.
- Request userId must match the authenticated user; administrators may act across users.
- Dashboard and knowledge-base endpoints require the admin role.
- Spot and route catalog endpoints remain public.

For compatibility, create-room and join-room still accept token in the JSON body.
New clients should use the Bearer header.

## Administrator bootstrap

Set ADMIN_USER_NAME and ADMIN_PASSWORD before the backend starts.
The administrator can then sign in through POST /api/auth/login.

Optional configuration:

- SESSION_TTL_SECONDS=86400
- CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

## Frontend integration impact

The frontend API client must attach the Bearer header to every protected GET and POST request.
Registration must send the selected tourist or guide role. Admin pages require a user
created from the server-side bootstrap configuration.
