# Bloodline 2.0 Threat Model & Security Posture

## Adversarial Threat Scenarios

### 1. Rapid Pass-Through & Layering Syndicates
- **Adversary Goal**: Disperse stolen funds before victim notices or bank automated rules trigger.
- **Tactic**: Aggregation into a first-hop hub, followed by rapid splitting (<30 minutes) across 3-5 intermediary accounts and immediate off-ramp into crypto exchanges or overseas wires.
- **Bloodline Mitigation**:
  - Pre-payment risk scoring detects sudden velocity spikes and dormant account activation.
  - Money DNA tracks tainted fund pools in real time.
  - Next-Hop prediction identifies likely cashout nodes before exit transfers clear.

### 2. Smurfing & Sub-Threshold Structuring
- **Adversary Goal**: Avoid mandatory regulatory reporting thresholds (e.g., $10,000 CTR/STR triggers).
- **Tactic**: Series of repeated transfers between $9,000 and $9,950 within hours.
- **Bloodline Mitigation**:
  - Graph multigraph aggregates rolling 24-hour windows across directed cycles and counterparties, triggering `STRUCTURING_SUSPECTED`.

### 3. Business Email Compromise (BEC) & Vendor Invoice Tampering
- **Adversary Goal**: Trick corporate treasury into routing large invoice payouts to adversary-controlled mule accounts.
- **Tactic**: Compromise vendor email or submit false banking instruction changing remittance details hours prior to invoice release.
- **Bloodline Mitigation**:
  - Business Shield checks vendor beneficiary history. If bank details changed within 72 hours and destination account exhibits high mule indicators or divergence, automated freeze and dual-authorization callback are mandated.

### 4. Shared Device / Fingerprint Obfuscation
- **Adversary Goal**: Operate multiple mule accounts simultaneously while evading KYC linked-account checks.
- **Bloodline Mitigation**:
  - Heterogeneous graph models `USED_DEVICE` and `USED_IP` as investigative context links, flagging syndicate coordination without exposing raw personally identifiable information (PII).
