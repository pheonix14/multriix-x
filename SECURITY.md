# 🛡️ SECURITY POLICY — MULTRIIX X

## Supported Versions

We are committed to providing a secure and unrestricted local AI development environment. Security updates are regularly released for the following versions:

| Version | Supported | Security Hotfixes |
| :--- | :---: | :--- |
| **v1.0.x** |  ✅  | Fully Supported (Current) |
| **< v1.0.0** |  ❌  | Unsupported (Please Upgrade) |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities via public GitHub issues.** 

If you discover a security-critical vulnerability in the local sandbox isolation model, localhost binding routines, or filesystem API endpoints, please report it privately:

1. Open a private inquiry or issue directly with **ZeroX** (aka **pheonix14** on GitHub).
2. Detail the exact steps to reproduce the issue, including environment properties, port specifications, and potential exploit payloads.
3. Allow up to 48 hours for a direct security review and private hotfix patch before disclosing publicly.

---

## Local Hardening & Safeguards (Sovereignty Defaults)

**MULTRIIX X** operates under a highly strict security posture to prevent remote code execution (RCE) on your host PC:

1. **Strict Localhost Binding:** The backend server explicitly binds to `127.0.0.1` (localhost) to completely reject inbound requests from other machines on your local network or public internet.
2. **Dynamic Range Scanning:** The system implements automated port hunting in the secure range of `3000` to `3099` to isolate your local nodes.
3. **No Centralized Logs or Telemetry:** There are no cloud callbacks, user metrics aggregators, or telemetry log push systems. Your interactions with local AI weights remain 100% offline, private, and contained on your physical machine.
