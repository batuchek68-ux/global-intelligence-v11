import os
import json
import base64
import sqlite3
import shutil
import tempfile
import win32crypt
from Crypto.Cipher import AES
import subprocess

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')
if not os.path.exists(cookies_path):
    cookies_path = es_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

tmp_dir = tempfile.mkdtemp()
tmp_cookies = os.path.join(tmp_dir, 'Cookies')
tmp_journal = os.path.join(tmp_dir, 'Cookies-journal')
tmp_wal = os.path.join(tmp_dir, 'Cookies-wal')

subprocess.run(['cmd', '/c', 'copy', cookies_path, tmp_cookies], capture_output=True)
journal_path = cookies_path + '-journal'
wal_path = cookies_path + '-wal'
if os.path.exists(journal_path):
    subprocess.run(['cmd', '/c', 'copy', journal_path, tmp_journal], capture_output=True)
if os.path.exists(wal_path):
    subprocess.run(['cmd', '/c', 'copy', wal_path, tmp_wal], capture_output=True)

conn = sqlite3.connect(tmp_cookies)
cursor = conn.cursor()
cursor.execute(
    "SELECT name, encrypted_value, value FROM cookies WHERE host_key LIKE '%jimeng%' AND name = 'sessionid'"
)

found = False
for name, encrypted_value, value in cursor.fetchall():
    found = True
    if value:
        print(f"SESSION_ID={value}")
    elif encrypted_value:
        if encrypted_value[:3] == b'v10':
            encrypted_value = encrypted_value[3:]
            nonce = encrypted_value[:12]
            ciphertext = encrypted_value[12:-16]
            tag = encrypted_value[-16:]
            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=nonce)
            result = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
            print(f"SESSION_ID={result}")
        else:
            result = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
            print(f"SESSION_ID={result}")
    break

if not found:
    cursor.execute("SELECT DISTINCT host_key FROM cookies WHERE host_key LIKE '%jimeng%'")
    hosts = cursor.fetchall()
    print(f"ERROR: sessionid not found. jimeng hosts: {hosts}")
    cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%jimeng%' LIMIT 10")
    names = cursor.fetchall()
    print(f"Available cookie names: {names}")

conn.close()
shutil.rmtree(tmp_dir, ignore_errors=True)
