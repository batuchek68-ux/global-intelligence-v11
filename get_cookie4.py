import os
import json
import base64
import sqlite3
import subprocess
import tempfile
import win32crypt
from Crypto.Cipher import AES

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

tmp = os.path.join(tempfile.gettempdir(), 'chrome_cookies_copy.db')
r = subprocess.run(['cmd', '/c', 'copy', '/Y', cookies_path, tmp], capture_output=True, text=True)
print(f"copy result: {r.stdout} {r.stderr}")
print(f"file exists: {os.path.exists(tmp)}, size: {os.path.getsize(tmp) if os.path.exists(tmp) else 0}")

conn = sqlite3.connect(tmp)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(f"tables: {cursor.fetchall()}")

cursor.execute("SELECT host_key, name FROM cookies WHERE host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%'")
print(f"all jimeng cookies: {cursor.fetchall()}")

conn.close()
