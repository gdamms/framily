# framily

A self-hosted digital photo frame system that connects families together. Family members can upload photos to a shared gallery, which are automatically displayed on a physical frame device in your home.

## Table of Contents

1. [What is Framily?](#what-is-framily)
2. [System Architecture](#system-architecture)
3. [Getting Started](#getting-started)
4. [Setup Flow](#setup-flow)
5. [Daily Usage](#daily-usage)
6. [API Documentation](#api-documentation)
7. [Data Models](#data-models)
8. [Permissions & Roles](#permissions--roles)
9. [Configuration](#configuration)
10. [Development](#development)

---

## What is Framily?

Framily consists of two main components:

- **Digital Frame Device**: A connected device that displays a rotating gallery of family photos
- **Web Application**: A web interface where family members can upload photos, manage the frame, and manage other members

Family members create user accounts, join a shared "framily" (family + frame) using a unique framily code, and can then upload and manage photos together.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Framily Frame Device                      │
│  - Connects to home Wi-Fi                                  │
│  - Displays rotating photo gallery                         │
│  - Polls server for new pictures every N seconds           │
│  - Can be configured via Wi-Fi hotspot when offline        │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ HTTPS requests
              │ (Frame has secret token for auth)
              │
┌─────────────▼───────────────────────────────────────────────┐
│               Framily Backend Server                        │
│  - REST API for authentication & framily management        │
│  - User account management                                 │
│  - Photo metadata storage & retrieval                      │
│  - Photo storage integration (MinIO)                       │
│  - Real-time notifications (future)                        │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ HTTPS requests
              │ (JWT token auth)
              │
┌─────────────▼───────────────────────────────────────────────┐
│            Framily Web Application                          │
│  - User authentication & account management                │
│  - Photo upload & gallery management                       │
│  - Framily member management                               │
│  - Frame configuration                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker Compose

```bash
# Start all services (backend, frontend, database, MinIO)
docker-compose -f docker-compose.dev.yml up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Setup Flow

### Phase 1: Frame Initial Setup (Offline)

1. **Frame powers on** → No internet yet
2. **Frame creates Wi-Fi hotspot** (SSID: `framily-setup`, no password)
3. **User connects to hotspot** via phone/computer
4. **User accesses `http://192.168.4.1:8080`** (frame's setup portal)
5. **User enters Wi-Fi credentials** → Frame connects to home network

### Phase 2: Frame Registration (First Online)

1. **Frame connects to server** using unauthenticated endpoints
2. **Frame calls `POST /api/v1/framily/create`** → Receives `framily_code` (e.g., `ABC123XY`)
3. **Frame stores code locally** and displays it on screen
4. **Frame generates frame token** (long-lived secret) for future requests

### Phase 3: User Account Creation & Connection

1. **User opens web app** (from phone/computer on home network or remote)
2. **User registers account** via `POST /api/v1/auth/register`
   - Username, email, password
   - Receives JWT token
3. **User logs in** to web application
4. **User enters framily code** (from frame display or QR code)
5. **User calls `POST /api/v1/framily/connect`** with framily code
   - Frame now knows this user exists
6. **User becomes framily admin** (first user to connect)

### Phase 4: Framily Initialization

1. **Admin initializes framily** via `POST /api/v1/framily/init`
   - Sets framily name (e.g., "Johnson Family")
2. **Admin customizes settings** via `POST /api/v1/framily/settings`
   - Picture display duration
   - Shuffle/order mode
   - Transition effects

### Phase 5: Adding Family Members

1. **Admin invites users** via `POST /api/v1/framily/invite` (by username)
2. **Invited user receives invitation** (shown in web app)
3. **Invited user accepts** via `POST /api/v1/framily/join` with `accepted: true`
   - User is now a member and can upload photos

---

## Daily Usage

### Uploading Photos (Web App)

1. **User logs in** to web application
2. **User navigates to gallery**
3. **User selects photos** to upload
4. **Upload process**:
   - Photos sent to `POST /api/v1/pictures/upload`
   - Files stored in MinIO object storage
   - Metadata saved to database
5. **Frame fetches new pictures** on next poll (within N seconds)
6. **New photos appear on frame** automatically

### Viewing Photos on Frame

1. **Frame periodically polls** `GET /api/v1/pictures/fetch` (e.g., every 30 seconds)
2. **Frame receives list** of new/updated pictures
3. **Frame displays photos** in configured order/duration
4. **Transitions automatically** between photos

### Managing Frame & Members (Web App)

- **Add member**: Admin invites new user
- **Remove member**: Admin kicks user or user leaves
- **Change roles**: Admin promotes/demotes members
- **Delete photos**: User deletes own photos or admin deletes any
- **Framily settings**: Admin adjusts display preferences
- **Delete framily**: Admin can permanently delete framily (also deletes all photos)

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
  "data": { /* response payload */ },
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

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (e.g., duplicate username) |
| 500 | Server error |

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "display_name": null
  }
}
```

**Validation Rules:**
- Username: 3-32 characters, alphanumeric + underscore
- Email: Valid email format, unique
- Password: Minimum 8 characters

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "display_name": "John Doe"
  }
}
```

---

### User Endpoints

#### Get User Info
```
GET /api/v1/user/info?username=john_doe
```

**Response (200):**
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

**Note:** Frame uses this endpoint without authentication. Framily code is 8 characters, human-readable. Frame uses the token for all future requests.

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
{
  "framily": {
    "id": 1,
    "code": "ABC123XY",
    "name": null,
    "initialized": false,
    "created_at": "2026-01-18T10:30:00Z"
  }
}
```

**Error Cases:**
- 400: Invalid framily code format
- 404: Framily code not found
- 409: User already connected to this framily

---

#### Initialize Framily
```
POST /api/v1/framily/init
```

**Request:**
```json
{
  "framily_code": "ABC123XY",
  "name": "Johnson Family"
}
```

**Response (200):**
```json
{
  "framily": {
    "id": 1,
    "code": "ABC123XY",
    "name": "Johnson Family",
    "initialized": true,
    "created_at": "2026-01-18T10:30:00Z"
  }
}
```

**Permissions:** Only first user (admin) can initialize

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
- Frame is notified to reset when framily is deleted

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
- Same as above but limited settings

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
**Cascading:** All photos, memberships, and settings are deleted

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
- Formats: JPEG, PNG, WebP, GIF
- Max size: 50 MB
- Dimensions: 800x600 minimum

---

#### Fetch Pictures (Frame)
```
GET /api/v1/pictures/fetch?framily_code=ABC123XY&since=2026-01-18T10:00:00Z
```

**Response (200):**
```json
{
  "pictures": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://storage.example.com/550e8400-e29b-41d4-a716-446655440000.jpg",
      "uploaded_by": "john_doe",
      "upload_date": "2026-01-18T14:30:00Z"
    }
  ]
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
  "email": string,                // Unique, valid format
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
  "initialized": bool,          // true after init endpoint called
  "settings": {
    "picture_duration": int,    // Seconds to display each photo (5-60)
    "shuffle_mode": bool,       // Random or sequential display
    "transition_effect": string // "fade", "slide", "none"
  }
}
```

### Membership
```
{
  "user_id": int,               // Foreign key to User.id
  "framily_id": int,            // Foreign key to Framily.id
  "role": int,                  // 0=invited, 1=member, 2=admin
  "joined_date": datetime,      // When user joined/invited
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
| Action | Invited | Member | Admin | Owner |
|--------|---------|--------|-------|-------|
| View framily info | Limited | Full | Full | Full |
| Upload pictures | ✗ | ✓ | ✓ | ✓ |
| Delete own picture | ✗ | ✓ | ✓ | ✓ |
| Delete others' pictures | ✗ | ✗ | ✓ | ✓ |
| Invite new members | ✗ | ✗ | ✓ | ✓ |
| Accept/decline invite | ✓ | N/A | N/A | N/A |
| Kick members | ✗ | ✗ | ✓ | ✓ |
| Change member roles | ✗ | ✗ | ✓ | ✓ |
| Update settings | ✗ | ✗ | ✓ | ✓ |
| Delete framily | ✗ | ✗ | ✓ | ✓ |
| Leave framily | ✓ | ✓ | ✓* | ✓* |

\* Admins cannot leave if they're the last admin. Must promote another member first.

### Key Rules
1. **First user to connect** becomes admin automatically
2. **Last admin rule**: At least one admin must always exist (cannot leave/demote if last)
3. **Last member rule**: If last member leaves/is kicked, framily is auto-deleted
4. **No self-kick**: Admins cannot kick themselves
5. **Frame token**: Frame uses separate long-lived token, different from JWT

---

## Configuration

### Environment Variables

**Backend (`backend/.env`):**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/framily

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# MinIO (object storage)
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=framily-pictures

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Frontend (`frontend/.env`):**
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Framily
```

### Docker Compose Configuration

See `docker-compose.dev.yml` for local development setup with:
- PostgreSQL database
- MinIO object storage
- FastAPI backend
- SvelteKit frontend

---

## Development

### Project Structure

```
framily/
├── backend/              # FastAPI Python backend
│   ├── api/             # API route handlers
│   ├── core/            # Config, database, security
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── migrations/      # Alembic database migrations
│   └── main.py          # Application entry point
├── frontend/            # SvelteKit TypeScript frontend
│   ├── src/
│   │   ├── routes/      # Page components
│   │   ├── lib/
│   │   │   ├── components/  # Reusable UI components
│   │   │   ├── stores/      # Svelte stores (auth, etc.)
│   │   │   └── api.ts       # API client
│   │   └── app.html     # HTML template
│   └── package.json
├── docker-compose.dev.yml
└── README.md
```

### Running Locally

```bash
# Start with Docker Compose (recommended)
docker-compose -f docker-compose.dev.yml up

# Or run services separately
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

---

## Future Enhancements

- Real-time notifications (WebSocket)
- Mobile app
- Photo organization (folders, albums)
- Advanced search & filtering
- Scheduled picture uploads
- Integration with cloud storage (Google Photos, etc.)
- Multi-frame support per framily
