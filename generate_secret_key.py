import secrets

def generate_secret_key():
    return secrets.token_hex(24)

if __name__ == "__main__":
    new_secret_key = generate_secret_key()
    print(f"New SECRET_KEY: {new_secret_key}")
    print("Copy this key and paste it into your .env file as SECRET_KEY=<generated_key>")
