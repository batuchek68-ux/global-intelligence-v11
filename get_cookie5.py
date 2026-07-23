import os
import json
import base64
import sqlite3
import tempfile
import ctypes
import win32crypt
from Crypto.Cipher import AES

def copy_file(src, dst):
    try:
        ctypes.windll.kernel32.CopyFileW(src, dst, False)
        return True
    except:
        return False

local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Local State')
cookies_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\Default\Network\Cookies')

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

tmp = os.path.join(tempfile.gettempdir(), 'chrome_cookies_tmp.db')
tmp_wal = tmp + '-wal'
tmp_shm = tmp + '-shm'

copy_file(cookies_path, tmp)
copy_file(cookies_path + '-wal', tmp_wal)
copy_file(cookies_path + '-shm', tmp_shm)

print(f"exists: {os.path.exists(tmp)}, size: {os.path.getsize(tmp) if os.path.exists(tmp) else 0}")

conn = sqlite3.connect(tmp)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(f"tables: {cursor.fetchall()}")

cursor.execute("SELECT host_key, name FROM cookies WHERE host_key LIKE '%jimeng%' OR host_key LIKE '%jianying%'")
rows = cursor.fetchall()
print(f"jimeng cookies: {len(rows)}")
for r in rows:
    print(f"  {r}")

if not rows:
    cursor.execute("SELECT DISTINCT host_key FROM cookies LIMIT 20")
    print(f"all hosts: {cursor.fetchall()}")

conn.close()
