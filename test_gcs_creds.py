# test_gcs_creds.py
import json, os
from google.oauth2 import service_account
from google.auth.transport.requests import Request

def load_sa_json():
    # 1) env var
    sa_json = os.environ.get("GCP_SA_KEY_JSON")
    if sa_json:
        return sa_json

    # 2) try .streamlit/secrets.toml in root and app/.streamlit/secrets.toml
    try:
        import toml
    except Exception:
        return None

    candidates = [".streamlit/secrets.toml", os.path.join("app", ".streamlit", "secrets.toml")]
    for path in candidates:
        if os.path.exists(path):
            try:
                data = toml.load(path)
                val = data.get("GCP_SA_KEY_JSON")
                if val:
                    return val
            except Exception:
                continue
    return None

sa_json = load_sa_json()
if not sa_json:
    raise SystemExit("No GCP_SA_KEY_JSON encontrado en env ni en .streamlit/secrets.toml (busqué root y app/.streamlit)")

try:
    parsed = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
except Exception:
    # If direct json.loads fails, try a safer repair strategy:
    # 1) locate the JSON object inside the string (first '{' ... last '}')
    # 2) escape any raw newlines inside the PEM block between BEGIN/END markers
    import re

    raw = sa_json
    # extract the JSON-like substring
    first_brace = raw.find('{')
    last_brace = raw.rfind('}')
    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        raise
    candidate = raw[first_brace:last_brace+1]

    # Escape raw newline characters inside PEM block to valid JSON \n
    def escape_pem_newlines(s: str) -> str:
        pem_re = re.compile(r"(-----BEGIN PRIVATE KEY-----.+?-----END PRIVATE KEY-----)", re.DOTALL)
        def esc(m):
            pem = m.group(1)
            # Replace CRLF or LF with literal backslash-n
            pem_escaped = pem.replace('\\', '\\\\')
            pem_escaped = pem_escaped.replace('\r\n', '\\n')
            pem_escaped = pem_escaped.replace('\n', '\\n')
            return pem_escaped
        return pem_re.sub(esc, s)

    repaired = escape_pem_newlines(candidate)
    parsed = json.loads(repaired)

print("private_key_id:", parsed.get("private_key_id"))

# Normalizar newlines igual que la app
pk = parsed.get("private_key")
if isinstance(pk, str) and "\\n" in pk:
    parsed['private_key'] = pk.replace("\\n", "\n")

creds = service_account.Credentials.from_service_account_info(parsed)
try:
    creds.refresh(Request())
    print("Token refresh OK")
except Exception as e:
    print("Token refresh FAILED:", type(e).__name__, str(e))