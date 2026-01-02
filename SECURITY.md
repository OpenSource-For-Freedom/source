# Security Policy

## Reporting a Vulnerability

The SOURCE project takes security seriously. If you discover a security vulnerability within this repository, we appreciate your help in disclosing it to us responsibly.

### How to Report

**Please do NOT create a public GitHub issue for security vulnerabilities.**

Instead, report security issues via one of these methods:

1. **GitHub Security Advisories** (preferred)  
   Navigate to the [Security tab](https://github.com/OpenSource-For-Freedom/SOURCE/security/advisories) and click "Report a vulnerability"

2. **Email**  
   Contact the maintainers directly with details of the vulnerability

### What to Include

Please provide the following information in your report:

- **Description** — Clear explanation of the vulnerability
- **Impact** — Potential security impact and attack scenarios
- **Reproduction Steps** — Step-by-step instructions to reproduce the issue
- **Affected Components** — Scripts, data files, or workflows impacted
- **Suggested Fix** — If you have recommendations (optional)
- **Your Contact Information** — For follow-up questions

### Scope

This security policy covers:

**In Scope:**
- Data integrity issues (malformed data, injection vulnerabilities)
- Authentication/authorization issues in workflows or scripts
- Vulnerabilities in dependencies (Python packages, GitHub Actions)
- Information disclosure vulnerabilities
- Script execution vulnerabilities (arbitrary code execution)
- Supply chain security issues

**Out of Scope:**
- Issues with third-party threat intelligence sources (report to those providers)
- False positives in IP data (use issue tracker for data quality reports)
- Theoretical vulnerabilities without proof of concept
- Social engineering attacks
- DoS attacks against GitHub infrastructure

### Response Timeline

- **Initial Response:** Within 48 hours of report submission
- **Triage & Assessment:** Within 7 days
- **Resolution Target:** Critical issues within 30 days; moderate issues within 90 days
- **Public Disclosure:** Coordinated with reporter after fix is deployed

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations and data destruction
- Report vulnerabilities promptly and privately
- Give us reasonable time to fix issues before public disclosure
- Do not exploit vulnerabilities beyond what is necessary to demonstrate the issue

Researchers following these guidelines will not face legal action from the project maintainers.

### Security Best Practices for Users

When deploying SOURCE data:

**Warning:** Never auto-block IPs without validation — Review data and test in staging first
**Warning:** Validate data integrity — Check file hashes and workflow signatures
**Warning:** Use allowlists — Prevent blocking critical infrastructure
**Warning:** Monitor false positives — Set up alerting for blocked legitimate traffic
**Warning:** Keep dependencies updated — Regularly update Python packages and GeoIP databases  

### Security Updates

Security fixes will be:

- Released as soon as possible after verification
- Documented in release notes with CVE references (if applicable)
- Announced via GitHub Security Advisories
- Backported to supported versions when relevant

---

**Last Updated:** January 2, 2026
