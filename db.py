import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

account = "pm58521".upper()
user = "STREAMLITAI".upper()
qualified_username = account + "." + user
fingerprint_from_describe_user = "SHA256:3OngP5lVHGHb6tKCzjBNkIq7hOmAHNjzTxq4ZuHNll8="

def get_JWT():
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=59)
    
    # Construct JWT payload with issuer, subject, issue time, and expiration time
    payload = {
        "iss": qualified_username + '.' + fingerprint_from_describe_user,
        "sub": qualified_username,
        "iat": now,
        "exp": now + lifetime
    }
    
    encoding_algorithm = "RS256"
    
    private_key_path = "keys/rsa_key.p8"
    with open(private_key_path, "rb") as pem_in:
        private_key = load_pem_private_key(pem_in.read(), password=None, backend=default_backend())
        token = jwt.encode(payload, key=private_key, algorithm=encoding_algorithm)
    
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token
