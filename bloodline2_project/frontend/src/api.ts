import {
  ScanResponse,
  LineageResponse,
  CaseItem,
  InvoiceItem,
  LiveStats,
  EvalMetrics
} from './types';

const API_BASE = '';

export async function fetchStats(): Promise<LiveStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function runScan(
  payeeAccountId: string,
  amount: number,
  senderAccountId: string = 'ACC-VIC-01',
  remark: string = 'Payment'
): Promise<ScanResponse> {
  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      payee_account_id: payeeAccountId,
      amount,
      sender_account_id: senderAccountId,
      remark
    })
  });
  if (!res.ok) throw new Error('Scan failed');
  return res.json();
}

export async function fetchLineage(originRef: string = 'ORIGIN-MULE-CHAIN-01'): Promise<LineageResponse> {
  const res = await fetch(`${API_BASE}/lineage/${originRef}`);
  if (!res.ok) throw new Error('Failed to fetch Money DNA lineage');
  return res.json();
}

export async function fetchCases(): Promise<CaseItem[]> {
  const res = await fetch(`${API_BASE}/cases`);
  if (!res.ok) throw new Error('Failed to fetch cases');
  const data = await res.json();
  return Array.isArray(data) ? data : (data.cases || []);
}

export async function advanceCase(
  caseId: string,
  targetStage?: string,
  humanApproved: boolean = false,
  simulateDays: number = 0
): Promise<any> {
  const res = await fetch(`${API_BASE}/case/${caseId}/advance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_stage: targetStage,
      human_approved: humanApproved,
      simulate_days: simulateDays
    })
  });
  if (!res.ok) throw new Error('Failed to advance case');
  return res.json();
}

export async function fetchInvoices(): Promise<InvoiceItem[]> {
  const res = await fetch(`${API_BASE}/invoices`);
  if (!res.ok) throw new Error('Failed to fetch invoices');
  const data = await res.json();
  return data.invoices || [];
}

export async function checkVendor(
  vendorId: string,
  destAccount: string,
  amount: number
): Promise<any> {
  const res = await fetch(`${API_BASE}/vendor-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      vendor_id: vendorId,
      destination_account: destAccount,
      amount
    })
  });
  if (!res.ok) throw new Error('Vendor check failed');
  return res.json();
}

export async function submitDecision(
  accountId: string,
  outcome: string,
  txnId?: string,
  analystNote?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      account_id: accountId,
      txn_id: txnId,
      outcome,
      analyst_note: analystNote
    })
  });
  if (!res.ok) throw new Error('Failed to record decision');
  return res.json();
}

export async function requestLienHold(accountId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/hold-request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId })
  });
  if (!res.ok) throw new Error('Failed to request lien hold');
  return res.json();
}

export async function executeHandoff(
  caseId: string,
  transferRef: string,
  receiverAccount: string,
  amount: number,
  reasonCodes: string[]
): Promise<any> {
  const res = await fetch(`${API_BASE}/trace-handoff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      case_id: caseId,
      transfer_ref: transferRef,
      receiver_account: receiverAccount,
      amount,
      reason_codes: reasonCodes
    })
  });
  if (!res.ok) throw new Error('Cross-bank handoff failed');
  return res.json();
}

export async function fetchMetrics(): Promise<EvalMetrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch eval metrics');
  return res.json();
}

export async function resetDemo(): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reset demo');
  return res.json();
}

export async function fetchDemoStory(): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/story`);
  if (!res.ok) throw new Error('Failed to fetch demo story');
  return res.json();
}

export async function fetchDetectedMules(): Promise<{ mules: any[]; total_count: number }> {
  const res = await fetch(`${API_BASE}/mules`);
  if (!res.ok) throw new Error('Failed to fetch detected mules');
  return res.json();
}

export async function fetchLiveTransactions(limit: number = 150): Promise<{ transactions: any[]; total_count: number }> {
  const res = await fetch(`${API_BASE}/transactions?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch live transactions');
  return res.json();
}
