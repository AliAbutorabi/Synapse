# Modified Synapse Fork

## Overview

Synapse is the core of the Matrix messenger, running the background processes for sending messages, handling requests, and managing other functions. This project involves custom modifications to the Synapse source code to implement additional features:

1. **Admin Rooms API Endpoint** - Displays all rooms where a specific user has admin privileges
2. **Message Count Column** - Tracks the total number of messages sent by each user
3. **Failed Logins Table** - Logs failed authentication attempts with detailed metadata

---

## Environment Setup

**Operating System:** Windows 11

Since Synapse is designed for Linux, I used Windows Subsystem for Linux (WSL) to set up the development environment. Below are the methods I've tested for installing Synapse on Windows.

---

## Step-by-Step Installation Guide

### Step 1: Install WSL

Since Synapse is built for Linux, we first need to install Windows Subsystem for Linux (WSL):

```bash
wsl --install
```

If you encounter issues (e.g., due to a previous incomplete WSL removal), try:

```bash
winget install Microsoft.wsl
```

This downloads and installs WSL directly on your Windows machine.

### Step 2: Install Ubuntu Distribution

Install Ubuntu on WSL:

```bash
wsl --install Ubuntu
```

### Step 3: Install Synapse

#### Clone my Synapse fork repository:

```bash
git clone https://github.com/AliAbutorabi/Synapse.git
cd Synapse
```

#### Create and activate a virtual environment

```bash
python3 -m venv env
source env/bin/activate
```

#### Install Synapse:

Using repositories files instead of site-packages files:

```bash
pip install -e .
```

#### Generate the default configuration (with localhost as the server name)

```bash
python -m synapse.app.homeserver --server-name localhost --config-path homeserver.yaml --generate-config --report-stats=no
```

#### Manual Server Start

To start Synapse manually, run:

```bash
cd /home/YOUR-USERNAME/synapse
source env/bin/activate
python -m synapse.app.homeserver -c homeserver.yaml
```

---

### Step 4. Verify the Installation

Open the following URL in your web browser:

```
http://127.0.0.1:8080/proxy/8008/_matrix/static/
```

If everything works, you'll see a confirmation that the Synapse server is successfully installed and running on your localhost.

### 9. Create an Admin User

Open a second terminal, activate the virtual environment again, and run:

```bash
register_new_matrix_user \
  -c homeserver.yaml \
  http://localhost:8008
```

Example:

```
New user localpart: alice
Password:
Confirm password:
Make admin [no]? yes
```

> **Important Configuration Note**: If you install Synapse twice on your system using different methods, change the port of the second server from `8008` to another (e.g., `8009`) so both servers can run simultaneously.

---

## Setting Up Synapse as a System Service

Starting the server manually each time is tedious. To make Synapse start automatically when Ubuntu launches, create a systemd service file:

```bash
sudo tee /etc/systemd/system/synapse.service << 'EOF'
[Unit]
Description=Matrix Synapse
After=network.target

[Service]
Type=simple
User=aliab
WorkingDirectory=/home/aliab/synapse
Environment="PATH=/home/aliab/synapse/env/bin"
ExecStart=/home/aliab/synapse/env/bin/python -m synapse.app.homeserver -c /home/aliab/synapse/homeserver.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable synapse
sudo systemctl start synapse
```

### Service Management Commands

| Command                            | Description                |
| ---------------------------------- | -------------------------- |
| `sudo systemctl status synapse`    | Check server status        |
| `sudo systemctl start synapse`     | Start the server           |
| `sudo systemctl stop synapse`      | Stop the server            |
| `sudo systemctl restart synapse`   | Restart the server         |
| `sudo journalctl -u synapse -f`    | View logs in real time     |
| `sudo journalctl -u synapse -n 20` | View last 20 lines of logs |

---

## Changing the Bind Address

By default, Synapse runs on:

```
http://127.0.0.1:8080/proxy/8008/_matrix/static/
```

To access it directly on port 8008, edit the `homeserver.yaml` file:

```bash
nano ~/synapse/homeserver.yaml
```

Update the listeners section as follows:

```yaml
listeners:
  - bind_addresses:
      - 0.0.0.0 # Changed from default
    port: 8008
    resources:
      - compress: false
        names:
          - client
          - federation
    tls: false
    type: http
    x_forwarded: true
```

Then restart the server:

```bash
sudo systemctl restart synapse
```

Now Synapse will be accessible at:

```
http://127.0.0.1:8008
```

---

## Installing a Client (Element)

As per the Matrix documentation, you need a client app to test your server and log in with your local account. I recommend Element.

Download Element for Windows:  
[Element Setup](https://packages.element.io/desktop/install/win32/x64/Element%20Setup.exe)

After installation, log in with your local user account and password. **Important:** Change the homeserver from `matrix.org` to `http://localhost:8008`.

---

## Summary of Installed Components

- ✅ WSL
- ✅ Ubuntu
- ✅ Synapse
- ✅ Element

---

## [Admin-API's Management Website](https://github.com/AliAbutorabi/Django-Based-Synapse-Admin-Api-s-Management-UI)
A web-based interface built with the Django framework and allow you to manage and send Synapse admin-API's (Just through admin users). You have to install that through it's installation guide section.

---

## Implemented Changes

### 1. Admin Rooms API Endpoint

Displays all rooms where a specific user holds administrative privileges.

#### Workflow

1. **Create the endpoint definition** in `synapse/rest/admin/admin_rooms.py`:
   ```python
   PATTERNS = admin_patterns("/admin_rooms/(?P<user_id>[^/]*)$", "v4")
   ```
   This exposes the endpoint at:
   ```
   http://{homeserver}/_matrix/client/v3/admin_rooms/{user_id}
   ```
   The implementation verifies that the requesting user is an administrator and returns all rooms where the specified user has admin privileges. The number of returned rooms can be controlled via a `limit` query parameter.

2. **Register the endpoint** in `synapse/rest/admin/admin_rooms.py` to ensure Synapse recognizes and serves the new API route.

3. **Create the data access layer** in `synapse/storage/databases/main/admin_rooms.py`:
   This module retrieves all rooms a user has joined, checks whether the user holds admin privileges in each room, and returns the results as a JSON response containing room details.

4. **Register the storage function** in `synapse/storage/databases/main/__init__.py`:
   After registration, the function becomes available via:
   ```python
   self.store = hs.get_datastores().main
   room_ids = await self.store.get_rooms_for_user(user_id, limit=limit)
   ```

---

### 2. Message Count Column

Adds a `message_count` column to the users table to track the total number of messages each user has sent.

#### Workflow

1. **Update the database schema** for both SQLite and PostgreSQL in:
   - `synapse/storage/schema/main/full_schemas/72/full.sql.postgres`
   - `synapse/storage/schema/main/full_schemas/72/full.sql.sqlite`
   
   Add the following column to the `users` table:
   ```sql
   message_count BIGINT DEFAULT 0 NOT NULL
   ```
   This ensures the column is automatically created during database initialization or migration.

2. **Create the data access module** in `synapse/storage/databases/main/messages_count.py`:
   This module contains a class with functions responsible for storing and incrementing the message count in the database.

3. **Register the new class** so that message count operations become available throughout the codebase.

4. **Modify the room event handler** in `synapse/rest/client/room.py`:
   This file handles room message-sending events. The logic was updated to increment the message count for the sending user on each message event:
   ```python
   await self.store.store_messages_count(user_id)
   ```

---

### 3. Failed Logins Table

Logs failed authentication attempts with detailed metadata including user ID, IP address, user agent, and timestamp.

#### Workflow

1. **Create the database migration** at `synapse/storage/schema/main/delta/95/failed_logins.sql`:
   This schema defines the `failed_logins` table. For existing databases, execute the following commands to apply the migration manually:
   ```bash
   sudo systemctl stop synapse
   sqlite3 /home/aliab/synapse/homeserver.db ".tables"
   sqlite3 /home/aliab/synapse/homeserver.db << 'EOF'
   CREATE TABLE IF NOT EXISTS failed_logins (
       user_id TEXT,
       ip_address TEXT,
       user_agent TEXT,
       failure_time BIGINT
   );
   EOF
   sudo systemctl start synapse
   ```

2. **Update the schema version** in `synapse/storage/schema/__init__.py`:
   ```python
   SCHEMA_VERSION = 95  # remember to update the list below when updating
   ```
   This ensures Synapse recognizes and applies the new migration.

3. **Create the database interaction layer** for the `failed_logins` table, providing the following operations:
   - `store_failed_login` — Records a failed login attempt for a specific user
   - `get_all_failed_logins` — Retrieves all failed login attempt records
   - `get_failed_logins` — Retrieves failed login attempts for a specific user ID
   - `delete_failed_logins` — Deletes all failed login records for a specific user ID

4. **Register the new class and its functions** in `synapse/storage/databases/main/__init__.py` so they are recognized by Synapse.

5. **Integrate with the authentication handler** in `synapse/handlers/auth.py`:
   The `validate_login` function handles user login operations. Within the `except LoginError` block, the implementation calls the storage function to log the failed attempt.

6. **Capture request metadata** in `synapse/rest/client/login.py`:
   The client IP address and user agent are extracted from the request and passed to the `validate_login` function:
   ```python
   canonical_user_id, callback = await self.auth_handler.validate_login(
       login_submission, request_info, ratelimit=True
   )
   ```

7. **Expose the API endpoints** by creating `synapse/rest/client/failed_logins.py` with the following patterns:
   ```python
   PATTERNS = client_patterns("/failed_logins")
   PATTERNS = client_patterns("/failed_logins/(?P<user_id>[^/]*)")
   ```
   These expose:
   - `http://{homeserver}/_matrix/client/v3/failed_logins`
   - `http://{homeserver}/_matrix/client/v3/failed_logins/{user_id}`
   
   **Access control** is enforced via `synapse/rest/client/utils.py`:
   - Regular users can only view their own failed login records
   - Administrators have access to all users' records

8. **Register the endpoints** in `synapse/rest/__init__.py`.

---

## Test

you can test new API endpoints through code below:

```python
import requests
from pprint import pprint


def get_access_token(homeserver, user_id, password):
    login_url = f"{homeserver}/_matrix/client/v3/login"
    login_data = {
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": user_id},
        "password": password,
    }

    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code == 200:
        access_token = login_response.json().get("access_token")
    else:
        access_token = None
        print(
            f"Error access token: {login_response.status_code} - {login_response.text}"
        )

    return access_token


def get_user_failed_logins(homeserver, access_token, user_id):
    url = f"{homeserver}/_matrix/client/v3/failed_logins/{user_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        failed_logins = response.json()["failed_logins"]
        return failed_logins
    else:
        print(f"Error: {response.status_code} - {response.text}")


def admin_rooms(homeserver, access_token, user_id):
    url = f"{homeserver}/_synapse/admin/v4/admin_rooms/{user_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        admin_rooms = response.json()["admin_rooms"]
        return admin_rooms
    else:
        print(f"Error: {response.status_code} - {response.text}")


homeserver = "http://localhost:8008"
user_id = "@aliab:localhost"
password = "aliab"
access_token = get_access_token(homeserver, user_id, password)

result = get_user_failed_logins(homeserver, access_token, user_id)
result = admin_rooms("http://localhost:8008", access_token, user_id)
pprint(result)
```
replace your own username, password and homeserver instead of example (aliab).

---

*Authored by Ali Abutorabi*