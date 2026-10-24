// TypeScript Interfaces for Bloodline 2.0

export interface ReasonCode {
  code: string;
  label: string;
  feature_value: number;
  contribution: number;
}

export interface NextHop {
  account_id: string;
  label: string;
  bank_id: string;
  probability: number;
  historical_tx_count: number;
  is_held: boolean;
  is_external: boolean;
  reason: string;
}

export interface TimelineItem {
  txn_id: string;
  timestamp: string;
  type: 'INFLOW' | 'OUTFLOW';
  counterparty: string;
  amount: number;
  channel: string;
}

export interface GraphNode {
  data: {
    id: string;
    label: string;
    bank_id: string;
    mule_score: number;
    is_mule: boolean;
    role: string;
    is_held: boolean;
    is_center: boolean;
    is_external: boolean;
  };
}

export interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    amount?: number;
    channel?: string;
    is_dashed?: boolean;
    is_held?: boolean;
    label?: string;
    type?: string;
  };
}

export interface NeighbourhoodGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ScanResponse {
  account_id: string;
  account_label: string;
  bank_id: string;
  probability: number;
  verdict: 'ALLOW' | 'DELAY' | 'HOLD';
  threshold_hold: number;
  threshold_delay: number;
  iso_anomaly_score: number;
  honeypot_proximity_boost: number;
  top_reasons: ReasonCode[];
  plain_language_reasons: string[];
  counterfactual: string;
  features: Record<string, number>;
  next_hops: NextHop[];
  neighbourhood: NeighbourhoodGraph;
  timeline: TimelineItem[];
  is_simulated: boolean;
}

export interface LineageNode {
  id: string;
  account_id: string;
  label: string;
  layer: number;
  bank_id: string;
  role: string;
  is_mule: number;
  is_held: boolean;
  is_external: boolean;
  inflow: number;
  outflow: number;
}

export interface LineageLink {
  source: string;
  target: string;
  source_account: string;
  target_account: string;
  amount: number;
  timestamp: string;
  epoch_seconds: number;
  channel: string;
  is_held: boolean;
}

export interface LineageResponse {
  origin_ref: string;
  nodes: LineageNode[];
  links: LineageLink[];
  timeline: Array<{
    txn_id: string;
    source: string;
    target: string;
    amount: number;
    timestamp: string;
    epoch_seconds: number;
    is_held: boolean;
  }>;
  total_tracked_inr: number;
  total_held_inr: number;
  total_exited_inr: number;
  hold_active: boolean;
  is_estimated: boolean;
}

export interface CaseItem {
  case_id: string;
  account_id: string;
  stage: string;
  created_ts: string;
  show_cause_deadline_days: number;
  fmr_deadline_days: number;
  elapsed_days: number;
  show_cause_countdown_days: number;
  fmr_countdown_days: number;
  evidence: Record<string, any>;
  llm_case_summary?: string;
  show_cause_draft?: string;
  human_approved: number;
}

export interface MuleAccountItem {
  id: string;
  pseudonymous_label: string;
  bank_id: string;
  role: string;
  chain_id: string;
  layer: number;
  initial_balance: number;
  current_balance: number;
  kyc_tier: string;
  shared_devices: number;
  is_held: boolean;
  mule_score: number;
}

export interface LiveTransactionItem {
  id: string;
  ts: string;
  epoch_seconds: number;
  sender: string;
  sender_name?: string;
  sender_bank?: string;
  receiver: string;
  receiver_name?: string;
  receiver_bank?: string;
  amount: number;
  channel: string;
  ref: string;
  is_mule_flow: number;
  chain_id?: string;
  status: string;
}

export interface InvoiceItem {
  invoice_id: string;
  vendor_id: string;
  vendor_name: string;
  amount: number;
  due_date: string;
  account_id: string;
  bank_id: string;
  flag_bank_detail_change: number;
  status: string;
  is_attacked: number;
  attack_description?: string;
  original_account_id: string;
}

export interface LiveStats {
  prevented_inr: number;
  at_risk_inr: number;
  lost_inr: number;
  exposure_avoided_inr: number;
  rule_only_prevented_inr: number;
  false_positive_cost_inr: number;
  current_threshold_hold: number;
  current_threshold_delay: number;
  active_watch_accounts: number;
  interactive_holds_count: number;
  is_simulated: boolean;
}

export interface EvalMetrics {
  evaluation_timestamp: string;
  dataset_summary: {
    total_samples: number;
    train_samples: number;
    test_samples: number;
    test_mules: number;
  };
  ml_model: {
    name: string;
    pr_auc: number;
    precision: number;
    recall: number;
    false_positive_rate: number;
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
  };
  rule_baseline: {
    name: string;
    pr_auc: number;
    precision: number;
    recall: number;
    false_positive_rate: number;
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
  };
  robustness_holdout_test: {
    chain_id: string;
    detected_mules: number;
    total_mules: number;
    robustness_score: number;
    status: string;
  };
  feature_importances: Record<string, number>;
}
