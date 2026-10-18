# Security Policy

The NixManager Pro team takes the security of our application and the systems it manages seriously. This document outlines our security procedures, supported versions, and how to responsibly report vulnerabilities.

---

## Supported Versions

Security fixes and patches are prioritized for the following versions:

| Version | Supported          | Status |
| :------ | :----------------: | :----- |
| 1.7.x   | :white_check_mark: | Current Active Release |
| 1.6.x   | :white_check_mark: | Maintenance (Critical fixes only) |
| < 1.6.0 | :x:                | End of Life (Upgrade recommended) |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in NixManager Pro, please report it via private email:

* **Email**: [alsghyrblhh@gmail.com](mailto:alsghyrblhh@gmail.com)
* **Subject**: `[SECURITY VULNERABILITY] NixManager Pro - <Brief Description>`

### What to Include in Your Report:

To help us triage and resolve the issue quickly, please include:
1. **Type of vulnerability** (e.g., arbitrary command execution, privilege escalation, unauthorized file access, path traversal).
2. **Step-by-step reproduction instructions** or a Proof of Concept (PoC).
3. **Affected environment**: Operating System distribution, desktop environment, Nix version, and Python version.
4. **Impact assessment**: What an attacker could achieve if the vulnerability is exploited.
5. Any suggested remediations or mitigations.

---

## Response Timeline & SLA

* **Initial Acknowledgment**: Within **48 hours** of receiving your report.
* **Triage & Severity Assessment**: Within **5 business days**, confirming whether the issue is accepted as a vulnerability.
* **Resolution & Patching**: We aim to release a patch within **14 business days** for high/critical severity issues.
* **Public Disclosure**: Coordinated public disclosure will take place after the patch is published and users have had a reasonable window to update.

---

## Security Best Practices for Users

* Always run NixManager Pro under a regular unprivileged user account. NixManager Pro leverages `pkexec` or `sudo` only when strictly necessary for root-level multi-user daemon actions.
* Verify channel URLs before subscribing to untrusted third-party nixpkgs forks.
* Keep your Nix installation and Python environment updated to benefit from upstream security fixes.

Thank you for helping keep NixManager Pro safe for everyone! 🛡️
