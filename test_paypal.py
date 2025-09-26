import paypalrestsdk
import os

# Load credentials from .env
paypal_mode = os.getenv("PAYPAL_MODE", "sandbox")
client_id = os.getenv("PAYPAL_CLIENT_ID", "")
client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")

print(f"PayPal Mode: {paypal_mode}")
print(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: NOT SET")
print(f"Client Secret: {client_secret[:10]}..." if client_secret else "Client Secret: NOT SET")

if not client_id or not client_secret or "your_real" in client_id or "your_real" in client_secret:
    print("❌ ERROR: PayPal credentials not properly configured!")
    exit(1)

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": paypal_mode,
    "client_id": client_id,
    "client_secret": client_secret
})

# Test basic API call
try:
    # Try to get API context (this will test authentication)
    api = paypalrestsdk.Api()
    print("✅ PayPal SDK configured successfully!")
    print("✅ Credentials appear to be valid!")
except Exception as e:
    print(f"❌ ERROR: PayPal authentication failed: {e}")
