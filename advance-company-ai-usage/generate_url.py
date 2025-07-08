import os
import secrets
from dotenv import load_dotenv
from mighty_sdk_core.auth.oauth import generate_code_verifier, get_authorization_url
from mighty_sdk_core.auth.types import CodeChallengeMethod, OAuthAuthorizationParam

load_dotenv()

application_api_key = os.getenv("MIGHTY_APPLICATION_API_KEY")
application_id = os.getenv("MIGHTY_APPLICATION_ID")
application_private_key = os.getenv("MIGHTY_APPLICATION_PRIVATE_KEY")
mighty_base_url = os.getenv("MIGHTY_BASE_URL")

# Ensure all credentials are set
if not all([application_api_key, application_id, application_private_key, mighty_base_url]):
    raise ValueError("Missing required environment variables for OAuth authentication.")

# Generate a secure OAuth state and code verifier
state = secrets.token_urlsafe(16)

# This variable will contain both the code_challenge and code_verifier
code_verifier_response = generate_code_verifier()

# Save the code verifier to a file
with open("code_verifier.txt", "w") as file:
    file.write(code_verifier_response.code_verifier)

# Configure OAuth parameters
oauth_config = OAuthAuthorizationParam(
    client_id=application_id,
    redirect_uri="http://localhost:8501",  # Your Application's Redirect URI
    state=state,
    code_challenge=code_verifier_response.code_challenge,  # Get the code_challenge
    code_challenge_method=CodeChallengeMethod.SHA256
)

# Generate the authorization URL
authorization_url = get_authorization_url(oauth_config)
print(f"Authorize the application by visiting this URL:\n\n{authorization_url}\n\n")