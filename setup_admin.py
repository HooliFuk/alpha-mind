# setup_admin.py
# AKUFIN - Run this ONCE to set up admin access
# DELETE THIS FILE immediately after running
import sys
import os
sys.path.append('.')

from control.access_control import AKUFINAccessControl

print("=" * 55)
print("   AKUFIN ACCESS CONTROL SETUP")
print("=" * 55)

access = AKUFINAccessControl()

# ══════════════════════════════════════════════
# STEP 1: SET YOUR SECRET ADMIN KEY
# Change this to something only YOU know
# Example: "AKUFIN_ADMIN_YourName_2026"
# ══════════════════════════════════════════════
ADMIN_KEY = "AKUFIN_ADMIN_CHANGE_THIS_NOW"

# Set up admin
access.setup_admin(ADMIN_KEY)
print(f"\n✅ Admin key configured successfully")
print(f"   Save this key somewhere safe:")
print(f"   Key: {ADMIN_KEY}")
print(f"   Username to login: admin")

# ══════════════════════════════════════════════
# STEP 2: CREATE YOUR VC USER
# Change VC_USERNAME and VC_PASSWORD
# ══════════════════════════════════════════════
VC_USERNAME = "vc_viewer"
VC_PASSWORD = "AKUFIN_VC_2026"
VC_ROLE = "viewer"
VC_DAYS = 30

result = access.approve_user(
    username=VC_USERNAME,
    admin_key=ADMIN_KEY,
    role=VC_ROLE,
    expires_days=VC_DAYS
)

pwd_result = access.set_user_password(
    VC_USERNAME,
    VC_PASSWORD,
    ADMIN_KEY
)

print(f"\n✅ VC user created successfully")
print(f"   Username : {VC_USERNAME}")
print(f"   Password : {VC_PASSWORD}")
print(f"   Role     : {VC_ROLE} (read only)")
print(f"   Expires  : {result['expires'][:10]}")

# ══════════════════════════════════════════════
# STEP 3: CREATE YOUR OWN PERSONAL LOGIN
# This is separate from the admin key
# ══════════════════════════════════════════════
MY_USERNAME = "founder"
MY_PASSWORD = "AKUFIN_Founder_2026"
MY_ROLE = "trader"

result2 = access.approve_user(
    username=MY_USERNAME,
    admin_key=ADMIN_KEY,
    role=MY_ROLE,
    expires_days=365
)

pwd_result2 = access.set_user_password(
    MY_USERNAME,
    MY_PASSWORD,
    ADMIN_KEY
)

print(f"\n✅ Founder account created")
print(f"   Username : {MY_USERNAME}")
print(f"   Password : {MY_PASSWORD}")
print(f"   Role     : {MY_ROLE}")
print(f"   Expires  : {result2['expires'][:10]}")

print(f"\n{'='*55}")
print(f"   AKUFIN SETUP COMPLETE")
print(f"{'='*55}")
print(f"\nLOGIN CREDENTIALS SUMMARY:")
print(f"{'─'*55}")
print(f"ADMIN ACCESS:")
print(f"  Username : admin")
print(f"  Password : {ADMIN_KEY}")
print(f"  Access   : Full admin + all features")
print(f"{'─'*55}")
print(f"FOUNDER ACCESS:")
print(f"  Username : {MY_USERNAME}")
print(f"  Password : {MY_PASSWORD}")
print(f"  Access   : Trading + approvals")
print(f"{'─'*55}")
print(f"VC ACCESS:")
print(f"  Username : {VC_USERNAME}")
print(f"  Password : {VC_PASSWORD}")
print(f"  Access   : View only (30 days)")
print(f"{'─'*55}")
print(f"\n⚠️  IMPORTANT SECURITY STEPS:")
print(f"1. Screenshot or write down these credentials")
print(f"2. DELETE this file immediately after")
print(f"3. NEVER commit this file to GitHub")
print(f"4. Add to .gitignore: setup_admin.py")
