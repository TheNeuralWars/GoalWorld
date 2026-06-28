# GoalWorld — Domain Email Setup Guide

**Created:** 2026-06-28
**Status:** DNS verified — domain on Unstoppable Domains NS, no MX records configured.

---

## Current DNS State (verified 2026-06-28)

| Record | Value | Status |
|--------|-------|--------|
| NS | ns1/ns2.unstoppabledomains.com | ✅ Active |
| A | 76.76.21.21 (Vercel) | ✅ Active |
| MX | — | ❌ Not configured |
| TXT (SPF) | — | ❌ Not configured |
| TXT (_dmarc) | — | ❌ Not configured |

**Problem:** No MX records = no email for @goalworld.fun. All startup applications prefer a custom domain email over Gmail.

---

## Recommended: Zoho Mail (Free, fastest)

Zoho Mail offers a free plan for custom domains (up to 5 users, 5GB each).

### Steps

1. **Go to** https://www.zoho.com/mail/zohomail-pricing.html → click "Free Plan"
2. **Sign up** with nico@goalworld.fun (it will prompt you to verify domain ownership)
3. **Verify domain:** Zoho will give you a TXT record to add:
   - Go to Unstoppable Domains dashboard: https://unstoppabledomains.com/
   - Log in → find goalworld.fun → DNS settings
   - Add TXT record: `zoho-verification=XXXXXXXXXX.zmverify.zoho.com`
4. **Add MX records** (in Unstoppable Domains DNS):
   ```
   MX  mx.zoho.com      priority 10
   MX  mx2.zoho.com     priority 20
   MX  mx3.zoho.com     priority 50
   ```
5. **Add SPF (TXT record):**
   ```
   TXT  v=spf1 include:zoho.com ~all
   ```
6. **Add _dmarc (TXT record):**
   ```
   _dmarc.goalworld.fun  TXT  v=DMARC1; p=none; rua=mailto:nico@goalworld.fun
   ```
7. **Create mailbox:** nico@goalworld.fun
8. **Wait 15-30 min** for DNS propagation
9. **Test:** Send an email to nico@goalworld.fun from a Gmail account

### Alternative: Google Workspace ($6/mo)
- More professional, includes full Google suite
- Go to https://workspace.google.com → sign up → verify domain → add MX records:
  ```
  MX  aspmx.l.google.com      priority 1
  MX  alt1.aspmx.l.google.com priority 5
  MX  alt2.aspmx.l.google.com priority 5
  MX  alt3.aspmx.l.google.com priority 10
  MX  alt4.aspmx.l.google.com priority 10
  ```

---

## DNS Management via Unstoppable Domains

**Portal:** https://unstoppabledomains.com/
**Domain:** goalworld.fun

Unstoppable Domains uses their own nameservers. DNS records are managed through their dashboard (not a traditional registrar DNS panel). All TXT, MX, A, CNAME records can be added there.

**Note:** If Unstoppable Domains DNS panel is limited, alternative is to transfer NS to Cloudflare (free) for full DNS control:
1. Create Cloudflare account → add goalworld.fun
2. Change NS at Unstoppable Domains to Cloudflare NS
3. Manage all DNS in Cloudflare (better MX/TXT support)

---

*Prepared by Manager — 2026-06-28*
