# SOURCE — Deployment Guide & Best Practices

This document provides detailed guidance on deploying the SOURCE malicious IP intelligence feed in cloud and on-premises environments.

## Table of Contents

- [Deployment Strategies](#deployment-strategies)
- [Cloud Deployment](#cloud-deployment)
- [On-Premises Deployment](#on-premises-deployment)
- [Key Benefits](#key-benefits)
- [Operational Best Practices](#operational-best-practices)
- [Use Cases](#use-cases)
- [Integration Patterns](#integration-patterns)

---

## Deployment Strategies

### Cloud
### Cloud

- **Centralized Distribution:** One authoritative list can be pushed to many instances, edge services, and CDNs for fast, consistent protection across all regions
- **Auto-Scaling:** Scales automatically with autoscaling groups and integrates seamlessly with cloud firewalls and edge ACLs
- **Global Reach:** Deploy to multiple regions for low-latency threat blocking at the network edge
- **CI/CD Integration:** Automate list updates via GitHub Actions, AWS Lambda, Azure Functions, or GCP Cloud Functions

### On-Premises

- **Network Edge Enforcement:** Blocks malicious traffic at your network perimeter or security appliances before it reaches internal services
- **Offline Resilience:** Works without internet connectivity, ensuring protection even when external threat feeds are unavailable
- **Granular Control:** Provides tighter control over routing, VLAN segmentation, and critical allowlists
- **Compliance:** Keeps sensitive data on-prem to meet regulatory requirements

---

## Key Benefits

A curated malicious IP blocklist reduces risk by proactively blocking known bad actors before they reach your services or users. It complements signature-based and behavioral controls by providing deterministic, low-cost filtering that scales across environments.

### Security Benefits

- **Reduces Attack Surface** — Drops connections from known malicious hosts early, lowering load on IDS/IPS, application stacks, and logging pipelines
- **Lowers MTTM (Mean Time to Mitigate)** — Blocks repeat offenders immediately without per-incident remediation
- **Improves Telemetry Quality** — Fewer noisy or malicious flows means clearer analytics and alerting for real threats
- **Enforces Consistency** — Shared lists ensure uniform blocking policies across cloud regions and on-prem clusters

### Operational Benefits

- **Cost Reduction** — Reduces compute costs by blocking malicious traffic before it reaches application layers
- **Performance Optimization** — Improves application performance by filtering out scanning and attack traffic
- **Simplified Management** — Single source of truth for threat intelligence across all environments
- **Audit Trail** — Track blocked IPs with severity scores and geolocation for compliance reporting

---

## Cloud Deployment

### AWS

#### Security Group Rules

```bash
# Download latest IP list
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv -o badip_list.csv

# Convert to AWS Security Group deny rules
cat badip_list.csv | awk -F',' 'NR>1 {print $1"/32"}' > ip_ranges.txt

# Apply to security group (requires AWS CLI)
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --ip-permissions IpProtocol=-1,IpRanges='[{CidrIp=<IP>/32,Description="Blocked"}]'
```

#### AWS WAF Integration

```python
import boto3
import csv

waf = boto3.client('wafv2')

# Create IP Set
response = waf.create_ip_set(
    Name='SourceMaliciousIPs',
    Scope='CLOUDFRONT',  # or 'REGIONAL'
    IPAddressVersion='IPV4',
    Addresses=[
        # Load from badip_list.csv
        '1.2.3.4/32',
        '5.6.7.8/32',
    ]
)
```

#### Lambda Auto-Update Function

```python
import boto3
import requests

def lambda_handler(event, context):
    """Update WAF IP set with latest SOURCE data"""
    url = "https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv"
    response = requests.get(url)
    
    ips = [line.split(',')[0] + '/32' for line in response.text.split('\n')[1:] if line]
    
    waf = boto3.client('wafv2')
    waf.update_ip_set(
        Name='SourceMaliciousIPs',
        Scope='CLOUDFRONT',
        Id='<ip-set-id>',
        Addresses=ips,
        LockToken='<lock-token>'
    )
    
    return {"statusCode": 200, "body": f"Updated {len(ips)} IPs"}
```

### Azure

#### Network Security Group (NSG) Rules

```powershell
# Download IP list
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv" -OutFile "badip_list.csv"

# Import and block IPs
$ips = Import-Csv badip_list.csv
$priority = 100

foreach ($ip in $ips) {
    Add-AzNetworkSecurityRuleConfig `
        -Name "Block-$($ip.ip_address)" `
        -NetworkSecurityGroup $nsg `
        -Access Deny `
        -Direction Inbound `
        -Priority $priority `
        -SourceAddressPrefix $ip.ip_address `
        -SourcePortRange "*" `
        -DestinationAddressPrefix "*" `
        -DestinationPortRange "*" `
        -Protocol *
    
    $priority++
}

Set-AzNetworkSecurityGroup -NetworkSecurityGroup $nsg
```

### Google Cloud Platform (GCP)

#### Cloud Armor Security Policy

```bash
# Create security policy
gcloud compute security-policies create source-blocklist \
    --description "SOURCE malicious IP blocklist"

# Add blocking rule
gcloud compute security-policies rules create 1000 \
    --security-policy source-blocklist \
    --expression "origin.ip in ['1.2.3.4', '5.6.7.8']" \
    --action "deny-403" \
    --description "Block malicious IPs from SOURCE feed"
```

### Cloudflare

#### Firewall Rules

```bash
# Use Cloudflare API to create firewall rule
curl -X POST "https://api.cloudflare.com/client/v4/zones/<zone-id>/firewall/rules" \
  -H "Authorization: Bearer <api-token>" \
  -H "Content-Type: application/json" \
  --data '{
    "filter": {
      "expression": "ip.src in {1.2.3.4 5.6.7.8}"
    },
    "action": "block",
    "description": "SOURCE malicious IPs"
  }'
```

---

## On-Premises Deployment

### Firewall Integration (iptables)

```bash
#!/bin/bash
# Block malicious IPs using iptables

# Download latest list
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv -o /tmp/badip_list.csv

# Create ipset for efficient blocking
ipset create source-blocklist hash:ip hashsize 65536

# Load IPs into ipset
tail -n +2 /tmp/badip_list.csv | cut -d',' -f1 | while read ip; do
    ipset add source-blocklist "$ip" 2>/dev/null
done

# Block all IPs in the set
iptables -I INPUT -m set --match-set source-blocklist src -j DROP
iptables -I FORWARD -m set --match-set source-blocklist src -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
ipset save > /etc/ipset.conf

echo "Blocked $(ipset list source-blocklist | grep -c 'Number of entries') IPs"
```

### pfSense / OPNsense

1. Navigate to **Firewall > Aliases**
2. Click **Add**
3. Set Type: **URL Table (IPs)**
4. Set URL: `https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv`
5. Set Update Frequency: **Daily**
6. Create firewall rule: **Block** traffic from alias

### Nginx/Apache Integration

#### Nginx: Block IPs at Web Server

```nginx
# /etc/nginx/conf.d/blocklist.conf

# Include blocked IPs
include /etc/nginx/blocked_ips.conf;

server {
    listen 80;
    server_name example.com;
    
    # Deny blocked IPs
    if ($remote_addr ~* /etc/nginx/blocked_ips.conf) {
        return 403;
    }
}
```

Generate `/etc/nginx/blocked_ips.conf`:

```bash
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv | \
  tail -n +2 | cut -d',' -f1 | awk '{print "deny " $1 ";"}' > /etc/nginx/blocked_ips.conf

nginx -t && systemctl reload nginx
```

#### Apache: .htaccess Rules

```apache
# Generate .htaccess deny rules
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv | \
  tail -n +2 | cut -d',' -f1 | awk '{print "Deny from " $1}' >> /var/www/html/.htaccess
```

---

## Operational Best Practices

### 1. Automate Updates and Validation

- **CI/CD Pipelines** — Integrate list updates into your deployment pipeline
- **Version Control** — Track changes with Git, use signed commits for integrity
- **Validation** — Verify file hashes and signatures before deployment
- **Rollback Plan** — Keep previous versions for quick rollback if needed

### 2. Apply Tiered Blocking

Implement severity-based enforcement:

- **Severity 5 (Critical):** Block immediately at network edge
- **Severity 4 (High):** Block at firewall, alert SOC
- **Severity 3 (Elevated):** Log and monitor, rate limit
- **Severity 1-2 (Low-Moderate):** Monitor only, no blocking

### 3. Distribute Efficiently

- **Human-Readable Formats** — CSV/JSON for transparency and debugging
- **Optimized Formats** — Binary formats (ipset, mmdb) for faster lookups
- **CDN Distribution** — Cache lists at edge locations for low-latency access
- **Delta Updates** — Only sync changed IPs to reduce bandwidth

### 4. Monitor Effectiveness

Track key metrics:

- **Blocked Requests:** Count of denied connections per hour/day
- **False Positive Rate:** Legitimate traffic accidentally blocked
- **Top Blocked Countries:** Geographic distribution of threats
- **Severity Distribution:** Breakdown of threat levels blocked

### 5. Combine with Other Defenses

SOURCE is most effective as part of a defense-in-depth strategy:

- **Rate Limiting** — Prevent brute force and DDoS attacks
- **WAF Rules** — Block application-layer attacks (SQLi, XSS)
- **Anomaly Detection** — Identify zero-day threats and insider threats
- **SIEM Integration** — Correlate blocked IPs with other security events
- **Threat Intelligence Feeds** — Supplement with commercial feeds for coverage

### 6. Test Before Production

**Always test in staging first:**

```bash
# Staging deployment
# 1. Deploy list to staging environment
# 2. Monitor for false positives (24-48 hours)
# 3. Review logs for blocked legitimate traffic
# 4. Adjust allowlists as needed
# 5. Deploy to production

# Production deployment
# 1. Start with log-only mode
# 2. Review logs for 1 week
# 3. Enable blocking for severity 5 only
# 4. Gradually expand to severity 4, then 3
```

### 7. Maintain Allowlists

Critical IPs that should **never** be blocked:

- Internal network ranges (RFC 1918)
- CDN providers (Cloudflare, Akamai, Fastly)
- Monitoring services (Pingdom, UptimeRobot, StatusCake)
- Payment gateways (Stripe, PayPal, Square)
- API partners and vendors
- Security scanners (Qualys, Rapid7, Tenable)

```bash
# Example allowlist
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
# Cloudflare IPs
173.245.48.0/20
103.21.244.0/22
# Add your critical IPs here
```

---

## Use Cases

### 1. Enterprise Network Security

**Scenario:** Protect corporate network from external threats

**Implementation:**
- Deploy at perimeter firewall (pfSense, Cisco ASA, Palo Alto)
- Block severity 4+ at network edge
- Log severity 3 for SOC review
- Integrate with SIEM (Splunk, ELK, QRadar)

### 2. Web Application Protection

**Scenario:** Secure public-facing web applications

**Implementation:**
- Deploy at WAF layer (AWS WAF, Cloudflare, Imperva)
- Block severity 5 immediately
- Rate limit severity 4
- Monitor severity 3 for escalation

### 3. API Gateway Security

**Scenario:** Protect REST/GraphQL APIs from abuse

**Implementation:**
- Integrate with API gateway (Kong, Tyk, AWS API Gateway)
- Block known scanners and bots
- Combine with rate limiting (per-IP, per-endpoint)
- Monitor for credential stuffing patterns

### 4. Cloud Infrastructure Hardening

**Scenario:** Reduce attack surface of cloud workloads

**Implementation:**
- Apply to security groups (AWS), NSGs (Azure), firewall rules (GCP)
- Automate updates via Lambda/Functions
- Monitor blocked attempts for threat intelligence
- Integrate with CloudWatch/Azure Monitor for alerting

### 5. Threat Hunting & Analysis

**Scenario:** Enrich security logs with threat intelligence

**Implementation:**
- Import to SIEM as lookup table
- Correlate firewall logs with SOURCE data
- Identify compromised internal hosts (outbound connections to malicious IPs)
- Track threat actor infrastructure changes over time

---

## Integration Patterns

### Pattern 1: Pull-Based Updates

```bash
# Cron job to update blocklist daily
0 2 * * * /usr/local/bin/update-blocklist.sh

# update-blocklist.sh
#!/bin/bash
curl -sS https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv -o /tmp/badip_latest.csv
if [ $? -eq 0 ]; then
    mv /tmp/badip_latest.csv /etc/security/badip_list.csv
    /usr/local/bin/apply-blocklist.sh
    logger "SOURCE blocklist updated successfully"
fi
```

### Pattern 2: Push-Based Updates (Webhook)

```python
# Flask webhook endpoint
from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/webhook/source-update', methods=['POST'])
def update_blocklist():
    """Triggered by GitHub webhook on dataset updates"""
    subprocess.run(['/usr/local/bin/update-blocklist.sh'])
    return {"status": "updated"}, 200
```

### Pattern 3: SIEM Enrichment

```python
# Splunk lookup script
import csv
import requests

def enrich_ip(ip_address):
    """Check if IP is in SOURCE blocklist"""
    url = "https://raw.githubusercontent.com/OpenSource-For-Freedom/SOURCE/main/badip_list.csv"
    response = requests.get(url)
    
    for line in response.text.split('\n')[1:]:
        if line.startswith(ip_address):
            fields = line.split(',')
            return {
                'is_malicious': True,
                'severity': fields[1],
                'country': fields[5],
                'asn': fields[9]
            }
    
    return {'is_malicious': False}
```

---

## Performance Considerations

### Lookup Performance

| Method | Lookups/Second | Memory Usage | Best For |
|---|---|---|---|
| **ipset** (Linux) | 1M+ | ~20 MB (300K IPs) | Firewall rules |
| **MaxMind DB** | 500K+ | ~50 MB | Application integration |
| **Hash Table** (Python) | 100K+ | ~80 MB | Scripts, analysis |
| **SQL Database** | 10K+ | ~200 MB | Complex queries, reporting |

### Optimization Tips

- **Use Binary Formats** — Convert CSV to ipset, mmdb, or binary hash tables for faster lookups
- **Index on IP Address** — If using SQL, create indexes on `ip_address` column
- **Cache Results** — Cache lookup results for frequently checked IPs (TTL: 1 hour)
- **Delta Updates** — Only reload changed IPs, not entire list
- **Lazy Loading** — Load blocklist into memory on first request, not at startup

---

## Troubleshooting

### Common Issues

**Issue: Legitimate traffic is blocked**

Solution: Add IP to allowlist, review severity thresholds, check for IP reassignment

**Issue: Blocklist not updating**

Solution: Check cron job logs, verify GitHub raw URL access, check file permissions

**Issue: High memory usage**

Solution: Use ipset instead of iptables rules, optimize data structures, consider delta updates

**Issue: Slow firewall performance**

Solution: Use hardware-accelerated matching (ipset), reduce rule count, implement tiered blocking

---

## Support

For deployment assistance:

- **Documentation:** [README.md](../README.md) | [API Reference](API.md) | [Database Schema](DB.md)
- **Issues:** [GitHub Issues](https://github.com/OpenSource-For-Freedom/SOURCE/issues)
- **Contributing:** [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Security:** [SECURITY.md](../SECURITY.md)

---

**Last Updated:** January 2, 2026