import os
import json
import base64
import sqlite3
import tempfile
import shutil
import win32crypt
from Crypto.Cipher import AES

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

tmp = os.path.join(tempfile.gettempdir(), 'chrome_cookies_tmp.db')
shutil.copy2(cookies_path, tmp)

for suffix in ['-wal', '-shm']:
    src = cookies_path + suffix
    if os.path.exists(src):
        shutil.copy2(src, tmp + suffix)

conn = sqlite3.connect(tmp)
cursor = conn.cursor()

cursor.execute("SELECT host_key, name, encrypted_value, value FROM cookies WHERE host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%'")
rows = cursor.fetchall()

def decrypt_cookie(encrypted_value, key):
    if encrypted_value[:3] in (b'v10', b'v20'):
        enc = encrypted_value[3:]
        nonce = enc[:12]
        ciphertext = enc[12:-16]
        tag = enc[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
    return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')

if not rows:
    print("ERROR: no jimeng cookies found")
else:
    for host, name, enc_val, val in rows:
        if name == 'sessionid':
            if val:
                print(f"SESSION_ID={val}")
            elif enc_val:
                result = decrypt_cookie(enc_val, decrypted_key)
                print(f"SESSION_ID={result}")
            break
    else:
        print("ERROR: sessionid not found")
        for host, name, enc_val, val in rows:
            print(f"  {host} -> {name}")

conn.close()
os.remove(tmp)
for suffix in ['-wal', '-shm']:
    p = tmp + suffix
    if os.path.exists(p):
        os.remove(p)
