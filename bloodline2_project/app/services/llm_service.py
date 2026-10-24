"""
LLM Service for Bloodline 2.0 (Phase 3)
Generates statutory show-cause notice drafts and case investigation files.
Uses Anthropic API when ANTHROPIC_API_KEY is available, with offline cached fallback.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional

class LLMService:
    _instance: Optional["LLMService"] = None

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.cached_drafts = {}

    @classmethod
    def get_instance(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = LLMService()
        return cls._instance

    def generate_case_file_and_notice(
        self,
        account_id: str,
        account_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generates:
          1. Investigation summary case file
          2. Statutory Show-Cause Notice draft under RBI guidelines
        """
        cache_key = f"{account_id}-{evidence.get('inbound_24h', 0)}"
        if cache_key in self.cached_drafts:
            return self.cached_drafts[cache_key]

        if self.api_key:
            try:
                result = self._call_anthropic_api(account_id, account_data, evidence)
                self.cached_drafts[cache_key] = result
                return result
            except Exception as e:
                print(f"[LLMService] Anthropic API call failed ({e}); switching to offline template.")

        # High-Fidelity Statutory Offline Fallback Template
        result = self._generate_offline_template(account_id, account_data, evidence)
        self.cached_drafts[cache_key] = result
        return result

    def _call_anthropic_api(
        self,
        account_id: str,
        account_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, str]:
        prompt = f"""
You are the Chief Compliance and Fraud Legal Officer for a major scheduled commercial bank regulated by the Reserve Bank of India (RBI).
Generate two structured legal artifacts for a suspected mule account:

ACCOUNT DETAILS:
- Account ID: {account_id}
- Account Label: {account_data.get('pseudonymous_label', 'Unknown')}
- Bank: {account_data.get('bank_id', 'Scheduled Commercial Bank')}
- Age: {account_data.get('account_age_days', 14)} days
- KYC Tier: {account_data.get('kyc_tier', 'TIER_1_BASIC')}

TRANSACTION & GRAPH EVIDENCE:
- Inbound Velocity (24h): INR {evidence.get('inbound_24h', 950000):,.2f}
- Outbound Pass-Through Ratio: {evidence.get('pass_through_ratio', 0.95) * 100:.1f}%
- Median Fund Dwell Time: {evidence.get('median_dwell_time_mins', 4.5):.1f} minutes
- Hardware Fingerprint Cluster: {evidence.get('shared_device_id', 'DEV-CLUSTER-01')}
- Structuring Signal: {evidence.get('structuring_signal', 3)} sub-threshold transactions

Format your response as valid JSON with two keys:
1. "investigation_summary": A concise factual dossier detailing the money laundering indicators, rapid dispersion topology, and regulatory breach.
2. "show_cause_notice": A formal statutory notice under Section 35A of the Banking Regulation Act, 1949 and RBI Master Directions on Fraud, giving 21 days for representation before lien and cybercrime escalation.
"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}]
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"]
            # Extract JSON block
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}") + 1]
                parsed = json.loads(json_str)
                return {
                    "investigation_summary": parsed.get("investigation_summary", text),
                    "show_cause_notice": parsed.get("show_cause_notice", text)
                }
            return {
                "investigation_summary": text[:500],
                "show_cause_notice": text
            }

    def _generate_offline_template(
        self,
        account_id: str,
        account_data: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, str]:
        bank = account_data.get("bank_id", "BANK_ALPHA")
        label = account_data.get("pseudonymous_label", account_id)
        inbound = evidence.get("inbound_24h", 950000.0)
        pass_ratio = evidence.get("pass_through_ratio", 0.96) * 100
        dwell = evidence.get("median_dwell_time_mins", 3.2)
        dev = evidence.get("shared_device_id", "DEV-MULE-CLUSTER-01")

        summary = (
            f"FORENSIC INVESTIGATION DOSSIER: Account {account_id} ({label}) registered under {bank}. "
            f"Within a 24-hour monitoring interval, the account demonstrated classic Aggregator-Layering "
            f"mule characteristics: total inbound electronic credits of INR {inbound:,.2f} followed by rapid "
            f"secondary dispersal ({pass_ratio:.1f}% pass-through) within a median dwell latency of {dwell:.1f} minutes. "
            f"Point-in-time device fingerprinting links this node directly to hardware cluster '{dev}'. "
            f"Behavioral pattern matches structured smurfing in contravention of RBI Prevention of Money Laundering (PMLA) norms."
        )

        notice = (
            f"STATUTORY SHOW-CAUSE NOTICE (DEMONSTRATION SAMPLE)\n"
            f"Issued by: Fraud Risk Monitoring & Compliance Directorate, {bank}\n"
            f"To: Account Holder ({label}), Account No: {account_id}\n"
            f"Subject: Notice to Show Cause within 21 Days under Banking Regulation Act, 1949 (Section 35A) "
            f"and RBI Master Directions on Fraud (RBI/DBS.CO/CFMC.BC.No.1/23.04.001/2016-17)\n\n"
            f"1. WHEREAS automated digital surveillance systems identified structured fund inflows totaling "
            f"INR {inbound:,.2f} followed by immediate multi-recipient dispersals ({pass_ratio:.1f}% within {dwell:.1f} minutes);\n"
            f"2. AND WHEREAS the registered device identifier ({dev}) is concurrently linked to multiple unverified accounts;\n"
            f"3. YOU ARE HEREBY NOTIFIED to submit a formal representation with verifiable source-of-funds documentation "
            f"within TWENTY-ONE (21) DAYS from the issuance hereof;\n"
            f"4. TAKE NOTICE that failure to submit adequate representation within the statutory clock shall lead to "
            f"confirmation of administrative hold/lien request and mandatory filing of Fraud Monitoring Return (FMR-1) "
            f"with the Central Fraud Registry (RBI CFR).\n\n"
            f"[Automated System Draft - Requires Designated Human Compliance Officer Approval]"
        )

        return {
            "investigation_summary": summary,
            "show_cause_notice": notice
        }
