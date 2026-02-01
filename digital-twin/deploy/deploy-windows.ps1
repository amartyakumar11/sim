# AWS EC2 Deployment Commands for PowerShell
# =============================================

# STEP 1: Set your EC2 details
$EC2_IP = "YOUR_EC2_PUBLIC_IP"           # e.g., "54.123.45.67"
$KEY_PATH = "C:\path\to\your-key.pem"    # Path to your .pem file
$EC2_USER = "ec2-user"                    # or "ubuntu" for Ubuntu AMI

# STEP 2: Fix key permissions (run once)
icacls $KEY_PATH /inheritance:r /grant:r "$($env:USERNAME):(R)"

# STEP 3: Copy project to EC2 (from your project root)
# Option A: Using SCP (if git is not set up on EC2)
scp -i $KEY_PATH -r ./digital-twin "${EC2_USER}@${EC2_IP}:~/"

# Option B: Just SSH in and clone from git (recommended)
ssh -i $KEY_PATH "${EC2_USER}@${EC2_IP}"

# STEP 4: On EC2, run these commands:
# =====================================
# cd digital-twin
# chmod +x deploy/deploy.sh
# ./deploy/deploy.sh
# =====================================

# STEP 5: Verify deployment
# Open in browser: http://$EC2_IP

# -----------------------------------------
# QUICK REFERENCE COMMANDS
# -----------------------------------------

# SSH into EC2
# ssh -i $KEY_PATH "${EC2_USER}@${EC2_IP}"

# View logs
# ssh -i $KEY_PATH "${EC2_USER}@${EC2_IP}" "cd digital-twin && docker compose logs -f"

# Restart services
# ssh -i $KEY_PATH "${EC2_USER}@${EC2_IP}" "cd digital-twin && docker compose restart"

# Update and redeploy
# ssh -i $KEY_PATH "${EC2_USER}@${EC2_IP}" "cd digital-twin && git pull && docker compose up -d --build"
