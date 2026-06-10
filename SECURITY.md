# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Food Processing System seriously. If you discover a
vulnerability, **please do not open a public issue**. Instead, report it
privately:

- 📧 Email: **aashish@marketdoctorsonline.com**
- Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) if enabled on the repo.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce (proof of concept if possible).
- Affected version(s).

We aim to acknowledge reports within **72 hours** and to provide a remediation
timeline after triage.

## Security Practices in This Project

The codebase follows several defensive practices:

- **Parameterised queries** everywhere — no string-concatenated SQL (prevents SQL injection).
- **Password hashing** with salted PBKDF2-HMAC-SHA256; passwords are never stored or logged in plaintext.
- **No secrets in source** — all credentials come from environment variables; `.env` is git-ignored and `.env.example` is the only committed template.
- **Input validation** on all user-supplied data before it reaches the database.
- **Least privilege** — the app only needs `SELECT`/`INSERT`/`UPDATE` on its own tables.

## Hardening Recommendations for Operators

- Use a dedicated MySQL user with access limited to the `food` database.
- Store real credentials in a secrets manager, not a committed file.
- Rotate database passwords periodically.
