# How to Get Dreamina Session ID

## Quick Method (30 seconds)

1. Open: https://jimeng.jianying.com/
2. Login to your account
3. Press **F12** → **Console** tab
4. Paste this and press Enter:

```javascript
document.cookie.split(';').find(c => c.trim().startsWith('sessionid=')).split('=')[1]
```

5. Copy the output value
6. Update `.env` file:

```
DREAMINA_SESSION_ID=pasted_value_here
```

## Alternative Method

1. Open: https://jimeng.jianying.com/
2. Login
3. Press **F12** → **Application** tab
4. Click **Cookies** → `https://jimeng.jianying.com`
5. Find `sessionid` row
6. Copy the **Value** column
7. Update `.env` file

## For International Users

If you're outside China, use regional prefix:
- US: add `us-` prefix
- Hong Kong: `hk-`
- Japan: `jp-`
- Singapore: `sg-`

Example:
```
DREAMINA_SESSION_ID=us-your_value_here
```

## Verify It Works

```bash
python test_api.py
```
