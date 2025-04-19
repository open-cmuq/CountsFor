# CountsFor Deployment Guide (Maintainer)

This guide provides instructions for maintainers to redeploy the CountsFor application hosted on the VM.

## Prerequisites

* Maintainer-level access.
* SSH client.
* Andrew ID credentials for SSH access.
* Connection to the CMU VPN (if accessing from off-campus).

## Accessing the Server

The application is hosted on a Virtual Machine (VM). The hostname is set to `countsfor.qatar.cmu.edu`.

Connect to the server using SSH with your Andrew credentials:

```bash
ssh <YourAndrewID>@countsfor.qatar.cmu.edu
```

**Note:** The project's root directory path used in the commands below (e.g., `/path/to/CountsFor/`) needs to be adjusted to the actual location where the application code resides on the VM. The path `/home/bbendou/GenEd-CMUQ` was used previously, confirm the correct path on the server.

## Redeployment Steps

Follow the relevant steps depending on whether you updated the backend, frontend, or both.

### 1. Redeploy Backend (FastAPI)

Use these steps when the FastAPI backend code (`backend/` directory) has been updated:

```bash
# Navigate to the backend directory (Update path if needed)
cd /path/to/CountsFor/backend

# Fetch latest changes from the Git repository
git pull

# Activate the Python virtual environment
source venv/bin/activate

# Install or update dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Deactivate environment (optional, good practice)
# deactivate

# Restart the FastAPI service using systemd
sudo systemctl restart fastapi

# Check the status of the service
sudo systemctl status fastapi
```

**Checking Backend Logs:**

```bash
# View the last 50 lines of the FastAPI service log
journalctl -u fastapi --no-pager --lines=50
```

### 2. Redeploy Frontend (React)

Use these steps when the React frontend code (`frontend/` directory) has been updated:

```bash
# Navigate to the frontend directory (Update path if needed)
cd /path/to/CountsFor/frontend

# Fetch latest changes from the Git repository
git pull

# Install or update Node modules (if package.json changed)
npm install

# Remove the previous build directory (ensure a clean build)
sudo rm -rf /path/to/CountsFor/frontend/build

# Create a new production build
npm run build

# Set correct ownership for Nginx to serve the files
sudo chown -R www-data:www-data /path/to/CountsFor/frontend/build

# Set correct permissions
sudo chmod -R 755 /path/to/CountsFor/frontend/build

# Restart Nginx to serve the updated frontend build
sudo systemctl restart nginx
```

### 3. Verify the Deployment

After deploying changes, verify that both the frontend and backend are accessible and working correctly:

* **Frontend Application:** Open [http://countsfor.qatar.cmu.edu](http://countsfor.qatar.cmu.edu) in your browser.
* **Backend API Docs:** Check [http://countsfor.qatar.cmu.edu/api/docs](http://countsfor.qatar.cmu.edu/api/docs).

**Troubleshooting with Logs:**

* **Nginx Errors (Frontend Serving):**
  ```bash
  sudo cat /var/log/nginx/error.log | tail -n 20
  ```
* **FastAPI Errors (Backend API):**
  ```bash
  journalctl -u fastapi --no-pager --lines=50
  ```

## Automating Redeployment (Optional Script)

For frequent updates, you can use a single script to redeploy both backend and frontend. Place this script within the project, for example, in a `scripts` directory.

**1. Create the script file (Update path if needed):**

```bash
# Example location: within a 'scripts' directory in the project root
sudo nano /path/to/CountsFor/scripts/redeploy.sh
```

**2. Paste the following content into the editor (Ensure PROJECT_DIR is correct):**

```bash
#!/bin/bash

# Define the project directory
PROJECT_DIR="/path/to/CountsFor" # <-- IMPORTANT: SET THIS TO THE CORRECT PATH

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Pulling latest changes for the entire project..."
cd "$PROJECT_DIR"
git pull

echo "Updating backend..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
# Consider adding error checking for pip install if needed
pip install -r requirements.txt
deactivate # Deactivate after use
sudo systemctl restart fastapi
echo "Backend service restarted."

echo "Updating frontend..."
cd "$PROJECT_DIR/frontend"
npm install
# Consider adding error checking for npm run build
npm run build
sudo chown -R www-data:www-data build
sudo chmod -R 755 build
sudo systemctl restart nginx
echo "Frontend build updated and Nginx restarted."

echo "Redeployment complete!"

exit 0
```

**3. Save the file** (e.g., `Ctrl+X`, then `Y`, then `Enter` in `nano`).

**4. Make the script executable (Update path if needed):**

```bash
sudo chmod +x /path/to/CountsFor/scripts/redeploy.sh
```

**5. Run the script after pulling changes (Update path if needed):**

```bash
sudo /path/to/CountsFor/scripts/redeploy.sh
```

## Final Notes

* Always use `git pull` within the appropriate directory (`backend/`, `frontend/`, or the root project directory) to fetch the latest code changes before deploying.
* Determine the correct project path on the VM (referred to as `/path/to/CountsFor/` in examples) and update commands accordingly.
* Restart the `fastapi` service if only backend changes were made.
* Rebuild the React app (`npm run build`) and restart `nginx` if only frontend changes were made.
* Use the `redeploy.sh` script if both parts were updated.
* Check service status (`systemctl status ...`) and logs (`journalctl`, Nginx logs) if issues arise after deployment.
