#!/usr/bin/env python3
import sys
import os
import sqlite3
import hashlib
import binascii
from datetime import datetime, timezone
import json
import argparse
import subprocess

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: 'cryptography' library is not installed. Install it with: pip install cryptography")
    sys.exit(1)

ENV_PATH = "/data/docker/volumes/omniroute-data/_data/server.env"
DB_PATH = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"

def get_encryption_key():
    if not os.path.exists(ENV_PATH):
        print(f"ERROR: env file not found at {ENV_PATH}")
        sys.exit(1)
    
    secret = None
    with open(ENV_PATH, "r") as f:
        for line in f:
            if line.startswith("STORAGE_ENCRYPTION_KEY="):
                secret = line.split("=")[1].strip()
                break
                
    if not secret:
        print("ERROR: STORAGE_ENCRYPTION_KEY not found in server.env")
        sys.exit(1)
        
    salt = b"omniroute-field-encryption-v1"
    # Derive 32-byte key via scrypt
    derived_key = hashlib.scrypt(secret.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)
    return derived_key

def encrypt_val(derived_key, plain_text):
    iv = os.urandom(16)
    aesgcm = AESGCM(derived_key)
    ct_tag = aesgcm.encrypt(iv, plain_text.encode('utf-8'), None)
    ct = ct_tag[:-16]
    tag = ct_tag[-16:]
    
    iv_hex = binascii.hexlify(iv).decode('utf-8')
    ct_hex = binascii.hexlify(ct).decode('utf-8')
    tag_hex = binascii.hexlify(tag).decode('utf-8')
    
    return f"enc:v1:{iv_hex}:{ct_hex}:{tag_hex}"

def get_next_account_number(cursor, provider):
    # Check current connections to find highest account suffix
    cursor.execute("""
        SELECT id FROM provider_connections 
        WHERE provider = ? OR id LIKE ?
    """, (provider, f"{provider}-account-%"))
    
    highest = 0
    for (conn_id,) in cursor.fetchall():
        if conn_id.startswith(f"{provider}-account-"):
            try:
                num = int(conn_id.split("-")[-1])
                if num > highest:
                    highest = num
            except ValueError:
                pass
    return highest + 1

def add_keys(provider, keys_list):
    key = get_encryption_key()
    
    if not os.path.exists(DB_PATH):
        print(f"ERROR: SQLite database file not found at {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Establish details for specific providers
    db_providers = {
        'groq': ('apikey', 'Groq Account', '{"importFreeModelsOnly":true}'),
        'gemini': ('apikey', 'Gemini Account', '{"importFreeModelsOnly":false}'),
        'openrouter': ('apikey', 'OpenRouter Account', '{"importFreeModelsOnly":false,"autoSync":true}'),
        'nvidia': ('apikey', 'Nvidia NIM Account', '{"importFreeModelsOnly":false}'),
        'mistral': ('apikey', 'Mistral Account', '{"importFreeModelsOnly":false}'),
        'cohere': ('apikey', 'Cohere Account', '{"importFreeModelsOnly":false}'),
        'github-models': ('apikey', 'GitHub Models Account', '{"importFreeModelsOnly":false}'),
        'cerebras': ('apikey', 'Cerebras Account', '{"importFreeModelsOnly":false}'),
        'sambanova': ('apikey', 'SambaNova Account', '{"importFreeModelsOnly":false}'),
        'morph': ('apikey', 'Morph Account', '{"importFreeModelsOnly":false,"autoSync":true}'),
    }
    
    if provider not in db_providers:
        # Default openai-compatible or fallback API key configuration
        auth_type = 'apikey'
        display_name_base = f"{provider.capitalize()} Account"
        spec_data = '{"importFreeModelsOnly":false}'
    else:
        auth_type, display_name_base, spec_data = db_providers[provider]
        
    now = datetime.now(timezone.utc).isoformat()
    
    starting_num = get_next_account_number(c, provider)
    
    added_count = 0
    for idx, raw_key in enumerate(keys_list):
        if not raw_key.strip():
            continue
        acc_num = starting_num + idx
        node_id_conn = f"{provider}-account-{acc_num}"
        name = f"{display_name_base} #{acc_num}"
        priority = 50 + acc_num  # Escalated weights / load bal priority
        
        encrypted_key = encrypt_val(key, raw_key.strip())
        
        c.execute("""
            INSERT OR REPLACE INTO provider_connections (
                id, provider, auth_type, name, priority, is_active, api_key,
                provider_specific_data, created_at, updated_at, test_status
            ) VALUES (
                ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, 'active'
            )
        """, (node_id_conn, provider, auth_type, name, priority, encrypted_key, spec_data, now, now))
        
        print(f"-> Registered connection row '{node_id_conn}' ('{name}') under priority={priority}")
        added_count += 1
        
    conn.commit()
    conn.close()
    print(f"\nSuccessfully added {added_count} active connections for provider '{provider}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add multiple API keys to OmniRoute provider pool.")
    parser.add_argument("--provider", required=True, help="Provider name (e.g. groq, gemini, openrouter, nvidia, mistral, cohere, github-models, cerebras, sambanova, morph)")
    parser.add_argument("--keys", help="Comma-separated API keys")
    parser.add_argument("--file", help="Path to text file containing one key per line")
    parser.add_argument("--restart", action="store_true", help="Automatically restart the OmniRoute docker container after database update")
    
    args = parser.parse_args()
    
    keys_list = []
    if args.keys:
        keys_list = [k.strip() for k in args.keys.split(",") if k.strip()]
        
    if args.file:
        if not os.path.exists(args.file):
            print(f"ERROR: Key file not found at {args.file}")
            sys.exit(1)
        with open(args.file, "r") as f:
            keys_list.extend([line.strip() for line in f if line.strip()])
            
    if not keys_list:
        print("ERROR: No keys provided. Please specify --keys or --file.")
        sys.exit(1)
        
    add_keys(args.provider, keys_list)
    
    if args.restart:
        print("\nRestarting omniroute container...")
        res = subprocess.run(["sudo", "docker", "restart", "omniroute"], capture_output=True, text=True)
        if res.returncode == 0:
            print("Container restarted successfully.")
        else:
            print(f"Error restarting container: {res.stderr}")
