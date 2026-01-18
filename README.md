# framily
Connected self-hosted frame to share pictures with your family.

## Overview

While offline, the framily frame open a Wi-Fi access point to allow users to connect and set up some internal configuration. Once online, the frame will connect to the framily server to create the framily if needed, or fetch new pictures to display. On setup, the frame will first fetch /api/v1/framily/create to create a new framily. It will then display the framily code to the user and keep a secret token for future requests. The user can then connect their account to the framily by using /api/v1/framily/connect. The user can then initialize the framily with some basic information using /api/v1/framily/init.

Users can create an account from /api/v1/auth/register and log in using /api/v1/auth/login. Upon successful login, a JWT token is returned which must be included in the Authorization header for all subsequent requests. Users can fetch their own information and other users' information using /api/v1/user/info. They can also update their information using /api/v1/user/update.

Framilies can be managed using the various framily endpoints. Users can invite others to join the framily, accept or decline invitations, leave the framily, kick members, promote or demote members, and delete the framily. When a framily is deleted, all associated pictures and memberships are also deleted. The concerned frame will be notified to reset itself (i.e., forget the framily and create a new one, and display the new framily code).

Pictures can be uploaded to the framily using /api/v1/pictures/upload. The framily frame will periodically fetch new pictures to display through /api/v1/pictures/fetch.

Pictures can be managed using several picture endpoints. Users can delete pictures that they have uploaded. Admins can also delete any picture in the framily.


## Data structure

User:
- id: int (primary key)
- username: string (unique, not null)
- email: string (not null)
- hashed_password: string (not null)
- display_name: string (nullable)

Framily:
- id: int (primary key)
- code: string (unique, not null)
- name: string (not null)
- created_at: datetime (not null)
- initialized: bool (not null, default false)

Picture:
- id: string (primary key)
- framily_id: string (foreign key to Framily.id, not null)
- url: string (not null)
- uploaded_by: int (foreign key to User.id, not null)
- upload_date: datetime (not null)

Membership:
- user_id: int (foreign key to User.id, not null)
- framily_id: string (foreign key to Framily.id, not null)
- role: int (not null, e.g., 0 for invited, 1 for member, 2 for admin)
- unique constraint on (user_id, framily_id)
- joined_date: datetime (not null)


## Routes

/api/v1/auth/register [POST]
- Request body: { "username": string, "email": string, "password": string }
- Returns: { "token": string }
Creates a new user account and returns a JWT token.

/api/v1/auth/login [POST]
- Request body: { "username": string, "password": string }
- Returns: { "token": string }
Authenticates a user and returns a JWT token.

/api/v1/user/info [GET]
- Request body: { "username": string }
- Returns: { "user": { ... } }
Fetches information about a user. It is also used to get the current user's info.

/api/v1/framily/create [POST]
- Request body: {}
- Returns: { "framily_code": string }
Creates a new framily and returns its ID.

/api/v1/framily/connect [POST]
- Request body: { "framily_code": string }
- Returns: {}
This endpoint is used to make the first connection to an existing framily.

/api/v1/framily/init [POST]
- Request body: { "framily_code": string, "name": string }
- Returns: {}
Initializes the framily with a name.

/api/v1/framily/invite [POST]
- Request body: { "framily_code": string, "username": string }
- Returns: {}
Invites a user to join the framily by username.

/api/v1/framily/join [POST]
- Request body: { "framily_code": string, "accepted": bool }
- Returns: {}
Accepts or declines an invitation to join a framily.

/api/v1/framily/leave [POST]
- Request body: { "framily_code": string, "username": optional string }
- Returns: {}
Leaves the specified framily.
If the user is the last member, the framily is deleted.
If the user is the last admin, it has to choose a new admin before leaving.

/api/v1/framily/kick [POST]
- Request body: { "framily_code": string, "username": string }
- Returns: {}
Kicks a user from the framily. Only admins can perform this action. (They cannot kick themselves.)

/api/v1/framily/promote [POST]
- Request body: { "framily_code": string, "username": string, "new_role": int }
- Returns: {}
Promotes or demotes a user in the framily. Only admins can perform this action.

/api/v1/framily/delete [POST]
- Request body: { "framily_code": string }
- Returns: {}
Deletes the framily. Only admins can perform this action.

/api/v1/framily/settings [POST]
- Request body: { "framily_code": string, "settings": { ... } }
- Returns: {}
Updates one or more framily settings (e.g., picture display duration, shuffle mode). Only admins can perform this action.

/api/v1/framily/info [GET]
- Query parameters: { "framily_code": string }
- Returns: { "framily": { ... } }
Fetches information about the framily. External members can only see limited information, members can see more details, and admins can see everything.
