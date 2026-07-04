"""
omniroute_auto_recovery.py
==========================
Active re-testing script for cooldown connections in OmniRoute.
Temp-unlocks the connection in DB to bypass OmniRoute's local short-circuit,
sends a test request, and restores the block if the upstream still fails.
"""
import sqlite3
import json
import urllib.request
import time
import datetime

DB = "/data/docker/volumes/omniroute-data/_data/storage.sqlite"
URL = 'http://localhost:20128/v1/chat/completions'
KEY = 'sk-cac9fb818e70e6bb-f4dcba-60525661'

def now_ts():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')

# Mapping of providers to standard test models
TEST_MODELS = {
    "openrouter": "openrouter/nvidia/nemotron-3-nano-30b-a3b:free",
    "mistral": "mistral/devstral-medium-latest",
    "sambanova": "sambanova/DeepSeek-V3.1",
    "cloudflare-ai": "cloudflare-ai/@cf/meta/llama-3.2-3b-instruct",
    "nvidia": "nvidia/deepseek-ai/deepseek-v4-flash",
    "codex": "codex/codex-mini-latest",
    "agy": "agy/claude-sonnet-4-6",
    "cerebras": "cerebras/gemma-4-31b"
}

def retest_connection(conn_id, provider, conn_name):
    model = TEST_MODELS.get(provider)
    if not model:
        return False, "Unsupported provider for retest"
    
    headers = {
        'Authorization': f'Bearer {KEY}',
        'Content-Type': 'application/json',
        'X-OmniRoute-Connection': conn_id
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'ping'}],
        'max_tokens': 5,
        'stream': False
    }
    
    try:
        req = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                body = resp.read().decode('utf-8')
                try:
                    js = json.loads(body)
                    content = js['choices'][0]['message']['content'].strip()
                    if content:
                        return True, f"Success: {content[:30]}"
                except Exception as ex:
                    return False, f"JSON parse error: {str(ex)}"
            return False, f"HTTP status: {resp.status}"
    except Exception as e:
        err = str(e)
        if hasattr(e, 'read'):
            try:
                err += " -> " + e.read().decode('utf-8')[:120]
            except:
                pass
        return False, f"Request failed: {err}"

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Query all connections that are currently cooling down OR have a non-active test_status
    c.execute("""
        SELECT id, name, provider, test_status, rate_limited_until, error_code, last_error, backoff_level
        FROM provider_connections
        WHERE is_active = 1
          AND (rate_limited_until IS NOT NULL 
               OR test_status IN ('rate_limited', 'credits_exhausted', 'unavailable'))
    """)
    cooldowns = [dict(r) for r in c.fetchall()]
    
    if not cooldowns:
        print("No connections in cooldown to retest.")
        conn.close()
        return
        
    print(f"Found {len(cooldowns)} connections in cooldown. Starting active recovery tests...")
    
    rec_count = 0
    for conn_info in cooldowns:
        cid = conn_info['id']
        name = conn_info['name']
        provider = conn_info['provider']
        orig_rate_limit = conn_info['rate_limited_until']
        orig_status = conn_info['test_status']
        orig_error_code = conn_info['error_code']
        orig_last_error = conn_info['last_error']
        orig_backoff = conn_info['backoff_level']
        
        # Determine if we can retest
        if provider not in TEST_MODELS:
            print(f"Skipping {provider} connection '{name}' ({cid[:8]}) — No test model defined.")
            continue
            
        print(f"Test-Unblocking '{name}' ({cid[:8]}) locally for active verification...")
        
        # Temp unlock in DB
        c.execute("""
            UPDATE provider_connections
            SET rate_limited_until = NULL, 
                test_status = 'active', 
                error_code = NULL, 
                last_error = NULL
            WHERE id = ?
        """, (cid,))
        conn.commit()
        
        # Run test
        success, msg = retest_connection(cid, provider, name)
        
        if success:
            print(f"  [RECOVERED] Key '{name}' is fully functional again! Kept unlocked.")
            rec_count += 1
        else:
            print(f"  [RESTORED] Key '{name}' is still failing: {msg}. Restoring cooldown.")
            # Restore original cooldown and state
            c.execute("""
                UPDATE provider_connections
                SET rate_limited_until = ?, 
                    test_status = ?, 
                    error_code = ?, 
                    last_error = ?
                WHERE id = ?
            """, (orig_rate_limit, orig_status, orig_error_code, orig_last_error, cid))
            conn.commit()
            
    conn.close()
    print(f"\nActive recovery run finished. Successfully recovered {rec_count} connections.")

if __name__ == '__main__':
    main()
