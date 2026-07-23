import sys
import json
from dreamina_cli_client import DreaminaCLIClient


def main():
    client = DreaminaCLIClient()

    print("Dreamina CLI Login Helper")
    print("=" * 40)

    print("\n1. Starting login process...")
    try:
        result = client.login(headless=False)
        print(f"Login result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Login error: {e}")
        print("\nPlease run this in a terminal:")
        print(f'  & "{client.cli_path}" login')
        return

    print("\n2. Checking login status...")
    try:
        status = client.check_login()
        print(f"Login status: {json.dumps(status, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Check login error: {e}")

    print("\n3. Checking credits...")
    try:
        credits = client.user_credit()
        print(f"Credits: {json.dumps(credits, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Credits error: {e}")


if __name__ == "__main__":
    main()
