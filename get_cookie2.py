import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')
if not os.path.exists(cookies_path):
    cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

conn = sqlite3.connect(f'file:{cookies_path}?mode=ro', uri=True)
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
    print("ERROR: sessionid not found - you may not be logged in on jimeng.jianying.com")

conn.close()
