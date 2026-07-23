import browser_cookie3

cj = browser_cookie3.chrome(domain_name='.jimeng.jianying.com')
for cookie in cj:
    if cookie.name == 'sessionid':
        print(f"SESSION_ID={cookie.value}")
        break
else:
    print("sessionid not found for jimeng.jianying.com")
    print("All cookies found:")
    for cookie in cj:
        print(f"  {cookie.name}={cookie.value[:20]}...")
