import os
import json
from dotenv import load_dotenv

def _obfuscate_secret(secret: str) -> str:
    if not secret:
        return ""
    length = len(secret)
    if length <= 4:
        return "*" * length  # Obfuscate short secrets entirely
    return secret[0] + "*" * (length - 2) + secret[-1]

def load_application_secrets():
    """
    Loads application secrets following a hierarchy:
    1. Environment variables (default)
    2. .env file (overwrites environment variables)
    3. secrets.json file (overwrites .env and environment variables)
    """
    
    # 1. Load environment variables (already done by OS, but good to note)
    # This function primarily handles .env and secrets.json on top of existing env vars.

    # 2. Load .env file
    load_dotenv()

    # 3. Load secrets.json file
    secrets_file_path = "secrets.json"
    if os.path.exists(secrets_file_path):
        try:
            with open(secrets_file_path, 'r') as f:
                secrets = json.load(f)
            for key, value in secrets.items():
                os.environ[key] = str(value)
            print(f"Successfully loaded secrets from {secrets_file_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {secrets_file_path}. Skipping.")
        except Exception as e:
            print(f"Error loading {secrets_file_path}: {e}")
    else:
        print(f"Info: {secrets_file_path} not found. Skipping.")

if __name__ == "__main__":
    # Example usage for testing
    print("Loading application secrets...")
    load_application_secrets()
    print("\n--- Loaded Secrets (Examples) ---")
    print(f"GITHUB_TOKEN: {_obfuscate_secret(os.getenv('GITHUB_TOKEN', 'Not Set'))}")
    print(f"SLACK_API_TOKEN: {_obfuscate_secret(os.getenv('SLACK_API_TOKEN', 'Not Set'))}")
    print(f"REPOMIX_API_KEY: {_obfuscate_secret(os.getenv('REPOMIX_API_KEY', 'Not Set'))}")
    print("\nRemember: Actual sensitive values are not printed for security.") 