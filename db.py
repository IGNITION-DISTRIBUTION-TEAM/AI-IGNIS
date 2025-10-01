import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import urllib3
import snowflake.connector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_snowflake_connection():
    account = "pm58521.east-us-2.azure"   # Snowflake account
    user = "STREAMLITAI"                   # Snowflake user

    private_key_path = "keys/rsa_key.p8"
    with open(private_key_path, "rb") as pem_in:
        private_key = load_pem_private_key(pem_in.read(), password=None, backend=default_backend())

    conn = snowflake.connector.connect(
        user=user,
        account=account,
        private_key=private_key,
        warehouse="CORTEX_WH",
        database="SNOWFLAKE_INTELLIGENCE",
        schema="STREAMLITAI"
    )
    return conn

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

def get_user_by_email(email: str):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT USER, PASSWORD, ROLE FROM SNOWFLAKE_INTELLIGENCE.STREAMLITAI.TM_EMPLOYEE_CREDENTIALS WHERE USER=%s",
            (email,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def set_user_password(email: str, password: str):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE SNOWFLAKE_INTELLIGENCE.STREAMLITAI.TM_EMPLOYEE_CREDENTIALS SET PASSWORD=%s WHERE USER=%s",
            (password, email)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
