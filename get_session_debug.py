import os
import json
import base64
import sqlite3
import tempfile
import shutil
import win32crypt
from Cryptodome.Cipher import AES

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
encrypted_key = base64.b64decode(encrypted_key_b64)
print(f"Key prefix: {encrypted_key[:5]}")
encrypted_key = encrypted_key[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
print(f"Key length: {len(decrypted_key)}")

tmp = os.path.join(tempfile.gettempdir(), 'chrome_cookies_tmp2.db')
shutil.copy2(cookies_path, tmp)
for suffix in ['-wal', '-shm']:
    src = cookies_path + suffix
    if os.path.exists(src):
        shutil.copy2(src, tmp + suffix)

conn = sqlite3.connect(tmp)
cursor = conn.cursor()

cursor.execute("SELECT host_key, name, encrypted_value, value FROM cookies WHERE name = 'sessionid' AND (host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%')")
rows = cursor.fetchall()

if not rows:
    cursor.execute("SELECT DISTINCT host_key FROM cookies WHERE host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%'")
    print(f"jimeng hosts: {cursor.fetchall()}")
    cursor.execute("SELECT host_key, name FROM cookies WHERE host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%' LIMIT 20")
    print(f"jimeng cookies: {cursor.fetchall()}")

for host, name, enc_val, val in rows:
    print(f"Host: {host}, Name: {name}, prefix: {enc_val[:5] if enc_val else 'N/A'}, plaintext: {val}")
    if val:
        print(f"SESSION_ID={val}")
    elif enc_val:
        prefix = enc_val[:3]
        print(f"Encrypted prefix bytes: {prefix}, hex: {enc_val[:10].hex()}")
        enc = enc_val[3:]
        nonce = enc[:12]
        ciphertext_and_tag = enc[12:]
        ciphertext = ciphertext_and_tag[:-16]
        tag = ciphertext_and_tag[-16:]
        print(f"Nonce: {nonce.hex()}, Tag: {tag.hex()}, CT len: {len(ciphertext)}")
        
        try:
            cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=nonce)
            result = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
            print(f"SESSION_ID={result}")
        except Exception as e:
            print(f"AES-GCM failed: {e}")
            try:
                result = win32crypt.CryptUnprotectData(enc_val, None, None, None, 0)[1].decode('utf-8')
                print(f"SESSION_ID={result}")
            except Exception as e2:
                print(f"CryptUnprotectData also failed: {e2}")

conn.close()
try:
    os.remove(tmp)
    for suffix in ['-wal', '-shm']:
        p = tmp + suffix
        if os.path.exists(p):
            os.remove(p)
except:
    pass
