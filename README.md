# framily

A self-hosted digital photo frame system that connects families together. Family members can upload photos to a shared gallery, which are automatically displayed on a physical frame device in your home.

## Table of Contents

TODO

---

## What is Framily?

Framily consists of two main components:

- **Digital Frame Device**: A connected device that displays a rotating gallery of family photos
- **Web Application**: A web interface where family members can upload photos, manage the frame, and manage other members

Family members create user accounts, join a shared "framily" (family + frame) using a unique framily code, and can then upload and manage photos together.

---

## System Architecture

    Framily Frame Device
    - Connects to home Wi-Fi
    - Displays rotating photo gallery
    - Polls server for new pictures every N seconds (Frame has secret token for auth)
    - Can be configured via Wi-Fi hotspot when offline

    Framily Backend Server
    - REST API for authentication & framily management
    - User account management
    - Photo metadata storage & retrieval
    - Photo storage integration (MinIO)
    - Real-time notifications (future)
    - Built with FastAPI & PostgreSQL

    Framily Web Application
    - User authentication & account management
    - Photo upload & gallery management
    - Framily member management
    - Frame configuration

---

## Using Framily

### User Authentication

1. **User opens web app** in browser
2. **User registers account**
   - Username, email, password
   - Receives JWT token
3. **User logs in** to web application
4. **User navigates through framily connection flow**

### Frame Initial Setup

1. **Frame powers on** -> No internet yet
2. **Frame creates Wi-Fi hotspot** (credentials shown on screen):
  - SSID: `framily-xxxx`
  - Password: random alphanumeric string
3. **User connects to hotspot** via phone/computer
4. **User accesses setup portal** in browser
  - Frame serves simple web app for setup
  - Accesses via `http://192.168.4.1/` or `TBD framily domain`
  - QR code shown on frame for easy access
5. **User enters initial setup info**:
  - Home Wi-Fi credentials (SSID, password)
  - Self-hosted server URL
  - Framily name (optional)
6. **Frame connects to home Wi-Fi and server**
7. If connection fails, **frame restarts hotspot** for retry (gets back to step 2)
8. On success, **frame receives framily code and secret token** from server
9. **Frame displays framily code & QR code** on screen for first user to join

### Framily Connection

1. **User enters framily code** (from frame display or QR code)
2. **User connects** with framily code -> frame now knows this user exists
3. **User becomes framily admin** (first user to connect)

### Daily Usage

- Users navigates through framilies and photos in web app
- Users can upload photos
- Admins can manage members (invite, kick, promote)
- Admins can adjust frame settings (picture duration, shuffle, transitions)

---

## API Documentation

### Authentication

All requests (except `/auth/register` and `/auth/login`) require a JWT token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response Format

**Success (2xx):**

```json
{
  "data": {
    /* response payload */
  },
  "message": "Operation successful"
}
```

**Error (4xx/5xx):**

```json
{
  "error": "Error code or message",
  "detail": "Detailed error description"
}
```

### HTTP Status Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| 200  | Success                              |
| 201  | Resource created                     |
| 400  | Bad request (validation error)       |
| 401  | Unauthorized (missing/invalid token) |
| 403  | Forbidden (insufficient permissions) |
| 404  | Not found                            |
| 409  | Conflict (e.g., duplicate username)  |
| 500  | Server error                         |

---

### Authentication Endpoints

#### Register New User

```
POST /api/v1/auth/register
```

**Request:**

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Validation Rules:**

- Username: 3-32 characters, alphanumeric + underscore, unique
- Email: Valid email format, may already exist (and its ok)
- Password: Minimum 8 characters

**Error Cases:**

- 400: Validation errors
- 409: Username already exists

---

#### Login

```
POST /api/v1/auth/login
```

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Cases:**

- 400: Missing fields
- 401: Invalid credentials

---

### User Endpoints

#### Get User Info

```
GET /api/v1/user/info?username=john_doe
```

**Response (200):**
Data will depend on whether the requester is the user themselves, a framily member, or an external user.
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "display_name": "John Doe"
  }
}
```

---

### Framily Endpoints

#### Create Framily

```
POST /api/v1/framily/create
```

**Request:**

```json
{}
```

**Response (201):**

```json
{
  "framily_code": "ABC123XY",
  "frame_token": "secret-long-lived-token-for-frame"
}
```

**Note:** Frame uses this endpoint without authentication. Framily code is human-readable. Frame uses the token for all future requests.

---

#### Connect to Framily

```
POST /api/v1/framily/connect
```

**Request:**

```json
{
  "framily_code": "ABC123XY"
}
```

**Response (200):**

```json
{}
```

**Error Cases:**

- 400: Invalid framily code format
- 404: Framily code not found
- 409: User already connected to this framily

**Note:** This endpoint only works for the first user connecting to a framily (makes them admin). It is part of the initial setup flow. Subsequent users must be invited.

---

#### Invite User to Framily

```
POST /api/v1/framily/invite
```

**Request:**

```json
{
  "framily_code": "ABC123XY",
  "username": "jane_doe"
}
```

**Response (200):**

```json
{
  "message": "Invitation sent"
}
```

**Permissions:** Admin only
**Error Cases:**

- 403: Not an admin
- 404: User not found

---

#### Accept/Decline Invitation

```
POST /api/v1/framily/join
```

**Request:**

```json
{
  "framily_code": "ABC123XY",
  "accepted": true
}
```

**Response (200):**

```json
{
  "message": "Invitation accepted"
}
```

---

#### Leave Framily

```
POST /api/v1/framily/leave
```

**Request:**

```json
{
  "framily_code": "ABC123XY"
}
```

**Response (200):**

```json
{
  "message": "Left framily"
}
```

**Special Cases:**

- If last member: Framily is auto-deleted
- If last admin: Cannot leave unless promote another admin first (returns 403)
- Frame will reset if no members remain

---

#### Kick User from Framily

```
POST /api/v1/framily/kick
```

**Request:**

```json
{
  "framily_code": "ABC123XY",
  "username": "jane_doe"
}
```

**Response (200):**

```json
{
  "message": "User kicked"
}
```

**Permissions:** Admin only
**Restrictions:** Cannot kick yourself

---

#### Change User Role

```
POST /api/v1/framily/promote
```

**Request:**

```json
{
  "framily_code": "ABC123XY",
  "username": "jane_doe",
  "new_role": 2
}
```

**Response (200):**

```json
{
  "message": "User role updated"
}
```

**Role Values:**

- 0 = Invited (pending response)
- 1 = Member
- 2 = Admin

**Permissions:** Admin only
**Restrictions:** Cannot demote last admin

---

#### Update Framily Settings

```
POST /api/v1/framily/settings
```

**Request:**

```json
{
  "framily_code": "ABC123XY",
  "settings": {
    "picture_duration": 10,
    "shuffle_mode": true,
    "transition_effect": "fade"
  }
}
```

**Response (200):**

```json
{
  "message": "Settings updated"
}
```

**Permissions:** Admin only

---

#### Get Framily Info

```
GET /api/v1/framily/info?framily_code=ABC123XY
```

**Response (200) - As Admin:**

```json
{
  "framily": {
    "id": 1,
    "code": "ABC123XY",
    "name": "Johnson Family",
    "initialized": true,
    "created_at": "2026-01-18T10:30:00Z",
    "settings": {
      "picture_duration": 10,
      "shuffle_mode": true,
      "transition_effect": "fade"
    },
    "members": [
      {
        "user_id": 1,
        "username": "john_doe",
        "display_name": "John Doe",
        "role": 2,
        "joined_date": "2026-01-18T10:30:00Z"
      },
      {
        "user_id": 2,
        "username": "jane_doe",
        "display_name": "Jane Doe",
        "role": 1,
        "joined_date": "2026-01-18T11:00:00Z"
      }
    ]
  }
}
```

**Response (200) - As Member:**

- Almost same as admin, only sensitive info are hidden (e.g., emails)

**Response (200) - As Invited/External:**

- Basic info only (name, member count)

---

#### Delete Framily

```
POST /api/v1/framily/delete
```

**Request:**

```json
{
  "framily_code": "ABC123XY"
}
```

**Response (200):**

```json
{
  "message": "Framily deleted"
}
```

**Permissions:** Admin only
**Cascading:** All photos, memberships, and settings are deleted. Frame will reset.

---

### Picture Endpoints

#### Upload Picture

```
POST /api/v1/pictures/upload
```

**Request:** (multipart/form-data)

```
framily_code: ABC123XY
file: <binary image data>
```

**Response (201):**

```json
{
  "picture": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "framily_id": 1,
    "url": "https://storage.example.com/550e8400-e29b-41d4-a716-446655440000.jpg",
    "uploaded_by": 1,
    "upload_date": "2026-01-18T14:30:00Z"
  }
}
```

**Validation:**

- Formats: JPEG, PNG, WebP (configurable)
- Max size: 10MB (configurable)
- Reencoded to standard format and framily quality (configurable)

---

#### Fetch Pictures (Frame)

```
GET /api/v1/pictures/fetch
```

**Response (200):**

```json
{
  "url": "https://storage.example.com/550e8400-e29b-41d4-a716-446655440000.jpg",
  "metadata": {
    "uploaded_by": "john_doe",
    "upload_date": "2026-01-18T14:30:00Z",
  }
}
```

**Authentication:** Uses frame token (not JWT)

---

#### Delete Picture

```
DELETE /api/v1/pictures/{picture_id}
```

**Response (200):**

```json
{
  "message": "Picture deleted"
}
```

**Permissions:**

- Own picture: Any member
- Others' pictures: Admin only

---

## Data Models

### User

```
{
  "id": int,                      // Primary key
  "username": string,             // Unique, 3-32 chars
  "email": string,                // Valid format, may not be unique
  "hashed_password": string,      // Bcrypt hash
  "display_name": string | null,  // Optional, user's display name
  "created_at": datetime          // Account creation timestamp
}
```

### Framily

```
{
  "id": int,                    // Primary key
  "code": string,               // Unique, 8 characters (A-Z, 0-9)
  "name": string,               // User-defined framily name
  "created_at": datetime,       // Creation timestamp
}
```

### FramilySettings

```
{
  "framily_id": int,            // Foreign key to Framily.id
  "picture_duration": int,      // Seconds per picture
  "shuffle_mode": string,       // Random, sequential, etc.
  "overlays": [
    {
      "type": string,           // e.g., timestamp, uploader name
      "position": string        // e.g., bottom-right, top-left
    }
  ]
}
```

### Membership

```
{
  "user_id": int,                 // Foreign key to User.id
  "framily_id": int,              // Foreign key to Framily.id
  "role": int,                    // 0=invited, 1=member, 2=admin
  "joined_date": datetime,        // When user joined/invited
  "unique": (user_id, framily_id) // One membership per user per framily
}
```

### Picture

```
{
  "id": string,                 // UUID (primary key)
  "framily_id": int,            // Foreign key to Framily.id
  "url": string,                // Object storage URL
  "uploaded_by": int,           // Foreign key to User.id (uploader)
  "upload_date": datetime,      // Upload timestamp
  "metadata": {
    "width": int,
    "height": int,
    "format": string,           // jpeg, png, webp, gif
    "file_size": int            // Bytes
  }
}
```

---

## Permissions & Roles

### Role Levels

| Action                  | External | Invited | Member  | Admin |
| ----------------------- | -------- | ------- | ------- | ----- |
| View framily info       | Limited  | Limited | Partial | Full  |
| Upload pictures         |          |         | OK      | OK    |
| Delete own picture      |          |         | OK      | OK    |
| Delete others' pictures |          |         |         | OK    |
| Invite new members      |          |         |         | OK    |
| Accept/decline invite   |          | OK      |         |       |
| Kick members            |          |         |         | OK    |
| Change member roles     |          |         |         | OK    |
| Update settings         |          |         |         | OK    |
| Delete framily          |          |         |         | OK    |
| Leave framily           |          |         | OK      | OK\*  |

\* Admins cannot leave if they're the last admin. Must promote another member first. If last member leaves, framily is auto-deleted.

### Key Rules

1. **First user to connect** becomes admin automatically
2. **Last admin rule**: At least one admin must always exist (cannot leave/demote if last)
3. **Last member rule**: If last member leaves/is kicked, framily is auto-deleted and frame resets (as it will receive an error on next fetch)
4. **No self-kick**: Admins cannot kick themselves
5. **Frame token**: Frame uses separate long-lived token, different from JWT

---

## Configuration

### Environment Variables

Use environment templates from `config/env`:

- `config/env/dev.env.example` for development
- `config/env/prod.env.example` for production
- `config/env/base.env.example` as a shared fallback template

`scripts/setup.sh` copies `config/env/dev.env.example` to `config/env/.env` and appends current UID/GID for local Docker volume permissions.

### Key Variables

```bash
# Runtime mode and security
ENVIRONMENT=development|production
SECRET_KEY=...
CORS_ORIGINS=https://your-frontend.example.com

# Backend static frontend serving
SERVE_FRONTEND=true|false
FRONTEND_DIST_DIR=/app/frontend-build

# Backend process model
BACKEND_WORKERS=2

# Data stores
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=framily
MINIO_SECURE=false
```

Production guardrails are enforced in backend settings:

- `SECRET_KEY` must not use the default placeholder value
- `CORS_ORIGINS` cannot be `*`

---

## Development

Development stack uses 4 services:

- postgres
- minio
- backend (reload enabled)
- frontend (Vite dev server)

The frontend talks directly to backend via `VITE_API_URL` (defaults to `http://localhost:8000/api/v1` in development).

Commands:

```bash
make setup
make start
```

Dev compose file: `config/compose/docker-compose.dev.yml`

---

## Production (Docker Compose)

Production stack removes nginx and frontend runtime containers. The backend image builds the Svelte frontend and serves static files directly.

Services in production:

- postgres
- minio
- backend

### 1. Prepare Environment

```bash
cp config/env/prod.env.example config/env/.env.prod
# then edit config/env/.env.prod values
```

### 2. Start Production Stack

```bash
make start-prod
```

Or detached:

```bash
make start-prodd
```

Stop:

```bash
make stop-prod
```

Production compose file: `config/compose/docker-compose.prod.yml`

### Notes

- TLS/HTTPS is expected to terminate outside compose (cloud load balancer or reverse proxy)
- Backend keeps API endpoints under `/api/v1`
- Non-API frontend routes are served with SPA fallback to `index.html`

---

## Installation

### Local Development

```bash
git clone <repo>
cd framily
make setup
make start
```

### Production Host

```bash
git clone <repo>
cd framily
cp config/env/prod.env.example config/env/.env.prod
# edit config/env/.env.prod
make start-prod
```
