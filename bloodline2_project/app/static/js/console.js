// Bloodline 2.0 - Easy-to-Use UI & Analyst Console Controller
let cy = null;
let currentAppMode = 'simple'; // 'simple' or 'expert'
let currentTab = 'tab-walkthrough';
let showNextHopOverlay = true;
let lineageData = null;
let selectedCaseId = 'CASE-2026-ALPHA-01';
let currentScenario = 'mule_attack';

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  // Initialize Simple Mode on first load with default scenario
  launchScenario('mule_attack');

  // Preload backend data for instant expert tab access
  loadNetworkGraph();
  loadMoneyDNA();
  loadNextHopPredictions();
  loadCases();
  loadImpactMetrics();
});

// ========================================================
// 1. SIMPLE MODE vs EXPERT MODE CONTROLLER
// ========================================================
function setAppMode(mode) {
  currentAppMode = mode;
  const simpleView = document.getElementById('view-simple-mode');
  const expertView = document.getElementById('view-expert-mode');
  const expertNav = document.getElementById('expert-nav-tabs');
  const btnSimple = document.getElementById('btn-mode-simple');
  const btnExpert = document.getElementById('btn-mode-expert');

  if (mode === 'simple') {
    simpleView.classList.remove('hidden');
    expertView.classList.add('hidden');
    expertNav.classList.add('hidden');

    btnSimple.className = 'px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 bg-crimson-600 text-white shadow transition';
    btnExpert.className = 'px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 transition';
  } else {
    simpleView.classList.add('hidden');
    expertView.classList.remove('hidden');
    expertNav.classList.remove('hidden');

    btnSimple.className = 'px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 transition';
    btnExpert.className = 'px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 bg-crimson-600 text-white shadow transition';

    switchTab(currentTab);
    if (cy) {
      setTimeout(() => { cy.resize(); cy.fit(); }, 150);
    }
  }

  if (window.lucide) lucide.createIcons();
}

// ========================================================
// 2. EASY MODE: SCENARIO LAUNCHER & STORYBOARD
// ========================================================
async function launchScenario(scenKey) {
  currentScenario = scenKey;

  // Highlight selected card
  ['mule', 'vendor', 'struct', 'payroll'].forEach(k => {
    const card = document.getElementById(`card-scen-${k}`);
    if (card) {
      card.classList.remove('border-crimson-600', 'border-amber-600', 'border-indigo-600', 'border-emerald-600', 'bg-slate-850');
      card.classList.add('border-slate-800', 'bg-slate-900');
    }
  });

  const activeCardId = scenKey === 'mule_attack' ? 'card-scen-mule'
    : scenKey === 'vendor_bec' ? 'card-scen-vendor'
    : scenKey === 'structuring_loop' ? 'card-scen-struct' : 'card-scen-payroll';

  const activeColor = scenKey === 'mule_attack' ? 'border-crimson-600'
    : scenKey === 'vendor_bec' ? 'border-amber-600'
    : scenKey === 'structuring_loop' ? 'border-indigo-600' : 'border-emerald-600';

  const activeCard = document.getElementById(activeCardId);
  if (activeCard) {
    activeCard.classList.remove('border-slate-800', 'bg-slate-900');
    activeCard.classList.add(activeColor, 'bg-slate-850');
  }

  const storyboard = document.getElementById('simple-storyboard');

  if (scenKey === 'mule_attack') {
    // Scenario 1: $75,000 Mule Smurfing Attack
    storyboard.innerHTML = `
      <div class="space-y-6">
        <!-- Stage 1: Pre-Payment Decision -->
        <div class="bg-slate-900 p-6 rounded-2xl border border-crimson-900/60 shadow-xl space-y-4">
          <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <span class="text-[11px] font-bold text-crimson-400 uppercase tracking-wider flex items-center space-x-1.5">
                <span class="w-2 h-2 rounded-full bg-crimson-500 pulse-live"></span>
                <span>Stage 1: Live Pre-Payment Interception</span>
              </span>
              <h2 class="text-lg font-bold text-white mt-1">Wire Transfer: $75,000.00 USD</h2>
              <div class="text-xs text-slate-400 font-mono mt-0.5">
                Sender: <strong class="text-slate-200">ACC-VICTIM-01 (Estate Trust)</strong> &rarr; Beneficiary: <strong class="text-crimson-400">ACC-MULE-HUB1 (Pioneer Digital)</strong>
              </div>
            </div>

            <div class="text-right">
              <div class="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-crimson-950 border border-crimson-600 text-crimson-300 font-black text-sm badge-glow">
                <i data-lucide="shield-alert" class="w-4 h-4"></i>
                <span>VERDICT: HOLD & FREEZE</span>
              </div>
              <div class="text-xs text-slate-400 font-mono mt-1">Risk Score: <strong class="text-crimson-400 font-bold">0.93 / 1.00</strong> • Latency: 3.8 ms</div>
            </div>
          </div>

          <!-- Why was this flagged? (Simple bullets) -->
          <div class="space-y-2">
            <h4 class="text-xs font-bold text-slate-300 flex items-center space-x-1.5">
              <i data-lucide="info" class="w-3.5 h-3.5 text-crimson-400"></i>
              <span>Why Did Bloodline Flag This Transfer?</span>
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div class="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <span class="font-bold text-crimson-400 block">&excl; Rapid Pass-Through</span>
                <p class="text-slate-400 text-[11px]">Beneficiary moved 98.4% of inbound money out to other accounts within 32 minutes.</p>
              </div>
              <div class="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <span class="font-bold text-crimson-400 block">&excl; Shared Hardware Link</span>
                <p class="text-slate-400 text-[11px]">Computer device ID <strong>DEV-SYN-901</strong> is simultaneously used by 3 other suspect accounts.</p>
              </div>
              <div class="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <span class="font-bold text-crimson-400 block">&excl; Brand New Payee</span>
                <p class="text-slate-400 text-[11px]">Account was created only 14 days ago and suddenly received high-velocity funds.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Stage 2: Money DNA Fund Flow -->
        <div class="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Stage 2: Money DNA Flow Visualizer</span>
              <h3 class="text-base font-bold text-white mt-0.5">Where Did the Stolen Funds Travel?</h3>
              <p class="text-xs text-slate-400">Estimated proportional tracing reveals how $75,000 splits across the smurfing chain.</p>
            </div>
            <button onclick="animateMoneyFlow()" id="btn-play-flow" class="px-3.5 py-1.5 bg-crimson-600 hover:bg-crimson-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition">
              <i data-lucide="play" class="w-3.5 h-3.5"></i>
              <span>Replay Money Flow</span>
            </button>
          </div>

          <!-- Visual Flow Diagram -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs pt-1" id="money-flow-boxes">
            <!-- Hop 0 -->
            <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div class="text-[10px] uppercase font-bold text-slate-500">Hop 0: Victim</div>
              <div class="font-mono font-bold text-white">ACC-VICTIM-01</div>
              <div class="text-slate-400 text-[11px]">Private Wealth Account</div>
              <div class="text-crimson-400 font-mono font-bold text-sm">$75,000.00</div>
              <div class="text-[10px] text-slate-500">Compromised Wire</div>
            </div>

            <!-- Hop 1 -->
            <div class="p-4 rounded-xl bg-slate-950 border border-crimson-800/80 space-y-2">
              <div class="text-[10px] uppercase font-bold text-crimson-400">Hop 1: Inbound Hub</div>
              <div class="font-mono font-bold text-white">ACC-MULE-HUB1</div>
              <div class="text-slate-400 text-[11px]">Pioneer Digital Trading</div>
              <div class="text-crimson-400 font-mono font-bold text-sm">$75,000.00</div>
              <div class="text-[10px] text-crimson-300 font-semibold">Immediate 3-Way Split</div>
            </div>

            <!-- Hop 2 -->
            <div class="p-4 rounded-xl bg-slate-950 border border-amber-800/80 space-y-2">
              <div class="text-[10px] uppercase font-bold text-amber-400">Hop 2: 3 Layering Mules</div>
              <div class="font-mono text-white text-[11px] space-y-0.5">
                <div>• ACC-MULE-002 ($25.0k)</div>
                <div>• ACC-MULE-003 ($24.5k)</div>
                <div>• ACC-MULE-004 ($24.3k)</div>
              </div>
              <div class="text-amber-400 font-mono font-bold text-sm">$73,800.00 Dispersed</div>
              <div class="text-[10px] text-amber-300 font-semibold">Smurfing Pass-Through</div>
            </div>

            <!-- Hop 3 -->
            <div class="p-4 rounded-xl bg-slate-950 border border-emerald-800/80 space-y-2">
              <div class="text-[10px] uppercase font-bold text-emerald-400">Hop 3: Intercepted Exits</div>
              <div class="font-mono font-bold text-white">ACC-EXIT-CRYPTO</div>
              <div class="text-slate-400 text-[11px]">Virtual Asset Gateway</div>
              <div class="text-emerald-400 font-mono font-bold text-sm">$24,800 HELD</div>
              <div class="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold inline-block">
                PREEMPTIVELY FROZEN
              </div>
            </div>
          </div>
        </div>

        <!-- Stage 3 & 4: Next-Hop Radar & Compliance Action -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Next-Hop Radar -->
          <div class="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span class="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">Stage 3: Next-Hop Prediction</span>
                <h3 class="text-sm font-bold text-white mt-0.5">Where Will Funds Try to Exit?</h3>
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                Top-1 Accuracy: 81.3%
              </span>
            </div>

            <div class="space-y-2.5 text-xs">
              <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <div class="font-mono font-bold text-amber-400">ACC-EXIT-CRYPTO</div>
                  <div class="text-[11px] text-slate-400">Overseas Virtual Asset Gateway</div>
                  <div class="text-[10px] text-slate-500 mt-0.5">Established counterparty with shared device</div>
                </div>
                <div class="text-right">
                  <div class="font-mono font-bold text-emerald-400 text-base">84.2%</div>
                  <button onclick="simpleFreezeAlert('ACC-EXIT-CRYPTO')" class="mt-1 px-2.5 py-1 bg-crimson-600 hover:bg-crimson-500 text-white rounded text-[10px] font-bold">
                    Preemptive Freeze
                  </button>
                </div>
              </div>

              <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <div class="font-mono font-bold text-slate-300">ACC-EXIT-RUNNER</div>
                  <div class="text-[11px] text-slate-400">ATM Runner Services</div>
                  <div class="text-[10px] text-slate-500 mt-0.5">High-frequency cashout pattern</div>
                </div>
                <div class="text-right">
                  <div class="font-mono font-bold text-slate-300 text-base">15.8%</div>
                  <button onclick="simpleFreezeAlert('ACC-EXIT-RUNNER')" class="mt-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px]">
                    Preemptive Freeze
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Compliance Action Center -->
          <div class="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Stage 4: Case Clock & Enforcement</span>
                <h3 class="text-sm font-bold text-white mt-0.5">Auditable Bank Actions</h3>
              </div>
              <div class="text-right">
                <div class="text-sm font-mono font-bold text-amber-400">47:48:12</div>
                <div class="text-[9px] text-slate-500 uppercase">Statutory Clock</div>
              </div>
            </div>

            <div class="space-y-2 text-xs">
              <p class="text-slate-400 text-[11px]">
                Case <strong class="text-white font-mono">CASE-2026-ALPHA-01</strong> is currently in the statutory representation window. Actions are digitally signed in the append-only audit trail.
              </p>

              <div class="grid grid-cols-2 gap-2 pt-2">
                <button onclick="openSarModal()" class="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-semibold text-left transition flex items-center space-x-2">
                  <i data-lucide="file-text" class="w-4 h-4 text-indigo-400 shrink-0"></i>
                  <span>View SAR Filing</span>
                </button>
                <button onclick="simpleActionAlert('Show Cause notice delivered to beneficiary account holder.')" class="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-semibold text-left transition flex items-center space-x-2">
                  <i data-lucide="mail" class="w-4 h-4 text-amber-400 shrink-0"></i>
                  <span>Send Show-Cause</span>
                </button>
                <button onclick="simpleActionAlert('Provisional freeze order executed under Section 102.')" class="p-2.5 rounded-xl bg-crimson-950 hover:bg-crimson-900 border border-crimson-700 text-crimson-200 text-xs font-semibold text-left transition flex items-center space-x-2">
                  <i data-lucide="lock" class="w-4 h-4 text-crimson-400 shrink-0"></i>
                  <span>Order Full Freeze</span>
                </button>
                <button onclick="simpleActionAlert('Case cleared as False Positive. Friction offset logged.')" class="p-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 text-xs font-semibold text-left transition flex items-center space-x-2">
                  <i data-lucide="check" class="w-4 h-4 text-emerald-400 shrink-0"></i>
                  <span>Mark False Positive</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else if (scenKey === 'vendor_bec') {
    // Scenario 2: Business Shield BEC
    storyboard.innerHTML = `
      <div class="bg-slate-900 p-6 rounded-2xl border border-amber-900/60 shadow-xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Business Shield — Invoice Fraud Detection</span>
            <h2 class="text-lg font-bold text-white mt-1">Vendor Invoice Payout: $85,000.00 USD</h2>
            <div class="text-xs text-slate-400">Vendor: <strong>Apex Facilities & Cloud Supplies Ltd</strong> • Invoice: <strong>INV-2026-891</strong></div>
          </div>
          <div class="text-right">
            <span class="px-3.5 py-1.5 rounded-full bg-crimson-950 border border-crimson-600 text-crimson-300 font-black text-sm">
              ACTION: FREEZE & CALLBACK REQUIRED
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
          <div class="p-4 bg-slate-950 rounded-xl border border-crimson-800/80 space-y-1">
            <span class="font-bold text-crimson-400 block">&excl; Bank Account Swapped</span>
            <p class="text-slate-400 text-[11px]">Bank payment details were changed <strong>3.2 hours ago</strong> (within 72h attack window).</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-crimson-800/80 space-y-1">
            <span class="font-bold text-crimson-400 block">&excl; Destination Divergence</span>
            <p class="text-slate-400 text-[11px]">New account <strong>ACC-MULE-HUB1</strong> diverges completely from historical verified supplier account.</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-crimson-800/80 space-y-1">
            <span class="font-bold text-crimson-400 block">&excl; High Mule Score (0.93)</span>
            <p class="text-slate-400 text-[11px]">Destination account shares device with known money laundering syndicates.</p>
          </div>
        </div>

        <div class="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-300 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <i data-lucide="phone-call" class="w-5 h-5 text-amber-400 shrink-0"></i>
            <span>Dual-Authorization Callback Protocol Initiated: Payout placed on administrative hold until CFO verbally confirms via phone.</span>
          </div>
          <button onclick="simpleActionAlert('Verified via CFO callback. Fraud wire blocked successfully!')" class="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded-lg text-xs shrink-0 ml-3">
            Simulate Callback Verification
          </button>
        </div>
      </div>
    `;
  } else if (scenKey === 'structuring_loop') {
    // Scenario 3: Structuring Loop
    storyboard.innerHTML = `
      <div class="bg-slate-900 p-6 rounded-2xl border border-indigo-900/60 shadow-xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">Structuring & Cycle Detection</span>
            <h2 class="text-lg font-bold text-white mt-1">Circular Laundering Loop: 3x $9,500.00 Transfers</h2>
            <div class="text-xs text-slate-400">Ring Nodes: <strong>ACC-RING-A &rarr; ACC-RING-B &rarr; ACC-RING-C &rarr; ACC-RING-A</strong></div>
          </div>
          <div class="text-right">
            <span class="px-3.5 py-1.5 rounded-full bg-indigo-950 border border-indigo-600 text-indigo-300 font-black text-sm">
              VERDICT: DELAY & REVIEW
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
          <div class="p-4 bg-slate-950 rounded-xl border border-indigo-800/80 space-y-1">
            <span class="font-bold text-indigo-400 block">&excl; Sub-Threshold Structuring</span>
            <p class="text-slate-400 text-[11px]">Transfers of $9,500, $9,450, and $9,400 are calibrated just beneath the $10,000 regulatory reporting threshold.</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-indigo-800/80 space-y-1">
            <span class="font-bold text-indigo-400 block">&excl; Directed Cycle Detected</span>
            <p class="text-slate-400 text-[11px]">Graph analysis identified a closed 3-node loop rotating funds back to the original originator.</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-indigo-800/80 space-y-1">
            <span class="font-bold text-indigo-400 block">&excl; Shared Device DEV-RING-77</span>
            <p class="text-slate-400 text-[11px]">All three ostensible business accounts are operated from the identical hardware device.</p>
          </div>
        </div>

        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
          <span class="text-slate-300">Would you like to examine the circular multigraph topology in the Expert Network View?</span>
          <button onclick="setAppMode('expert'); switchTab('tab-network');" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold">
            Open in Graph Explorer &rarr;
          </button>
        </div>
      </div>
    `;
  } else if (scenKey === 'legit_payroll') {
    // Scenario 4: Legitimate Payroll
    storyboard.innerHTML = `
      <div class="bg-slate-900 p-6 rounded-2xl border border-emerald-900/60 shadow-xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Zero Customer Friction Baseline</span>
            <h2 class="text-lg font-bold text-white mt-1">Commercial Payroll Payment: $3,200.00 USD</h2>
            <div class="text-xs text-slate-400">Meridian Enterprise Logistics &rarr; Sarah Jenkins (Retail Checking)</div>
          </div>
          <div class="text-right">
            <span class="px-3.5 py-1.5 rounded-full bg-emerald-950 border border-emerald-600 text-emerald-300 font-black text-sm">
              VERDICT: INSTANTLY APPROVED
            </span>
            <div class="text-xs text-slate-400 font-mono mt-1">Risk Score: <strong class="text-emerald-400">0.05 / 1.00</strong> • Latency: 1.2 ms</div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
          <div class="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
            <span class="font-bold text-emerald-400 block">&check; 1,200 Day Account Age</span>
            <p class="text-slate-400 text-[11px]">Established commercial logistics entity with clean historical compliance record.</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
            <span class="font-bold text-emerald-400 block">&check; Normal Bi-Weekly Velocity</span>
            <p class="text-slate-400 text-[11px]">ACH salary transfer corresponds perfectly with historical bi-weekly payroll schedules.</p>
          </div>
          <div class="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
            <span class="font-bold text-emerald-400 block">&check; Zero Suspicious Links</span>
            <p class="text-slate-400 text-[11px]">No shared hardware devices, proxy IPs, or high-risk counterparty associations.</p>
          </div>
        </div>

        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
          <span class="text-slate-300">Bloodline achieved a <strong>1.8% False Positive Rate</strong> compared to 8.5% in rule-only systems, preserving customer trust.</span>
          <button onclick="setAppMode('expert'); switchTab('tab-impact');" class="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold">
            View Comparative Benchmark &rarr;
          </button>
        </div>
      </div>
    `;
  }

  if (window.lucide) lucide.createIcons();
}

function animateMoneyFlow() {
  const boxes = document.querySelectorAll('#money-flow-boxes > div');
  boxes.forEach((b, i) => {
    setTimeout(() => {
      b.classList.add('ring-2', 'ring-crimson-500', 'bg-slate-850');
      setTimeout(() => {
        b.classList.remove('ring-2', 'ring-crimson-500', 'bg-slate-850');
      }, 700);
    }, i * 400);
  });
}

function simpleFreezeAlert(accountId) {
  alert(`Provisional freeze order issued for destination account: ${accountId}. Outbound crypto liquidation prevented.`);
}

function simpleActionAlert(msg) {
  alert(`${msg}\nAction logged to append-only audit trail.`);
}

function openSarModal() {
  const modal = document.getElementById('sar-modal');
  if (modal) modal.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeSarModal() {
  const modal = document.getElementById('sar-modal');
  if (modal) modal.classList.add('hidden');
}

// ========================================================
// 3. EXPERT MODE TAB SWITCHER
// ========================================================
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('text-crimson-400', 'border-crimson-500');
    btn.classList.add('text-slate-400', 'border-transparent');
  });

  const activeContent = document.getElementById(tabId);
  const activeBtn = document.getElementById(`btn-${tabId}`);
  if (activeContent) activeContent.classList.remove('hidden');
  if (activeBtn) {
    activeBtn.classList.remove('text-slate-400', 'border-transparent');
    activeBtn.classList.add('text-crimson-400', 'border-crimson-500');
  }

  currentTab = tabId;
  if (tabId === 'tab-network' && cy) {
    setTimeout(() => {
      cy.resize();
      cy.fit();
    }, 150);
  }
  if (window.lucide) lucide.createIcons();
}

// ========================================================
// 4. EXPERT WALKTHROUGH RUNNER (7 STEPS)
// ========================================================
async function runWalkthroughStep(stepNum) {
  for (let i = 1; i <= 7; i++) {
    const btn = document.getElementById(`wt-step-${i}`);
    if (btn) {
      if (i === stepNum) {
        btn.className = 'wt-btn p-3 rounded-lg bg-crimson-950/80 border border-crimson-600 text-left transition';
        btn.querySelector('span').className = 'text-[10px] font-bold text-crimson-400 uppercase tracking-wider block';
      } else {
        btn.className = 'wt-btn p-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-left transition';
        btn.querySelector('span').className = 'text-[10px] font-bold text-slate-500 uppercase tracking-wider block';
      }
    }
  }

  const container = document.getElementById('walkthrough-display-card');

  if (stepNum === 1) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 1 of 7</span>
            <h3 class="text-base font-bold text-white">Generate Synthetic Data: Legitimate Account vs Mule Chain</h3>
          </div>
          <button onclick="switchTab('tab-network')" class="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 font-medium">
            Inspect Full Graph &rarr;
          </button>
        </div>
        <p class="text-xs text-slate-300">
          The synthetic generator populates realistic multi-layer topologies: legitimate corporate entities beside smurfing hubs, rapid pass-through mules, and shared device networks.
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div class="p-4 rounded-xl bg-slate-950 border border-emerald-900/50 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>ACC-LEGIT-CORP</span>
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-medium">Risk Score: 0.04</span>
            </div>
            <div class="text-xs text-white font-medium">Meridian Enterprise Logistics</div>
            <div class="text-[11px] text-slate-400 space-y-1">
              <div>Type: Commercial Logistics • Age: 1,200 days</div>
              <div>Velocity In/Out (24h): $125k / $118k (Normal payroll)</div>
              <div>Shared hardware/IPs: None detected</div>
              <div class="text-emerald-400 font-medium pt-1">&check; Verified behavioral pattern with zero dispute markers</div>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-slate-950 border border-crimson-900/60 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-crimson-400 flex items-center space-x-1.5">
                <span class="w-2 h-2 rounded-full bg-crimson-500"></span>
                <span>ACC-MULE-HUB1</span>
              </span>
              <span class="text-[10px] px-2 py-0.5 rounded bg-crimson-950 text-crimson-300 border border-crimson-800 font-medium">Mule Score: 0.93</span>
            </div>
            <div class="text-xs text-white font-medium">Pioneer Digital Trading (Primary Hub)</div>
            <div class="text-[11px] text-slate-400 space-y-1">
              <div>Type: New Business • Age: 14 days</div>
              <div>Velocity In/Out (24h): $75k in &rarr; $73.8k out (98.4% pass-through in 32m)</div>
              <div>Shared hardware: DEV-SYN-901 (Shares device with 3 downstream mules)</div>
              <div class="text-crimson-400 font-medium pt-1">&excl; High-velocity fan-out smurfing dispersal node</div>
            </div>
          </div>
        </div>
        <div class="flex justify-end pt-3">
          <button onclick="runWalkthroughStep(2)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 2: Payment Scoring</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  } else if (stepNum === 2) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 2 of 7</span>
            <h3 class="text-base font-bold text-white">Payment Risk Scoring: Explain Reasons via API</h3>
          </div>
          <button onclick="executeDemoScoringStep2()" class="text-xs px-3 py-1.5 bg-crimson-600 hover:bg-crimson-500 text-white rounded font-medium">
            Run POST /api/v1/score Live
          </button>
        </div>
        <p class="text-xs text-slate-300">
          Scoring transaction <span class="font-mono text-amber-400">TXN-ORIGIN-75K</span> ($75,000 from Estate Trust Client <span class="font-mono text-slate-200">ACC-VICTIM-01</span> to Pioneer Digital <span class="font-mono text-slate-200">ACC-MULE-HUB1</span>).
        </p>

        <div id="step2-score-output" class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div class="text-center py-4 text-xs text-slate-400">Click "Run POST /api/v1/score Live" or view the API response.</div>
        </div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(3)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 3: Cooling-Off Queue</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
    executeDemoScoringStep2();
  } else if (stepNum === 3) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 3 of 7</span>
            <h3 class="text-base font-bold text-white">Cooling-Off Review Queue & Customer Outcome Simulation</h3>
          </div>
          <span class="text-xs px-2.5 py-1 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
            Policy: PSR-APP-2026 (2-Hour Pause)
          </span>
        </div>
        <p class="text-xs text-slate-300">
          The transaction was placed on a 2-hour delay recommendation (<span class="font-mono text-amber-400">DELAY_REVIEW</span>). Banks can pause release, contact the customer, and record the outcome via <span class="font-mono text-slate-300">POST /api/v1/payments/{payment_id}/outcomes</span>.
        </p>

        <div class="p-5 rounded-xl bg-slate-950 border border-amber-900/40 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xs font-bold text-amber-400">Active Cooling-Off Hold: TXN-ORIGIN-75K</div>
              <div class="text-[11px] text-slate-400 mt-0.5">Beneficiary: Pioneer Digital Trading ($75,000.00 USD)</div>
            </div>
            <div class="text-right">
              <div class="text-lg font-mono font-bold text-amber-400">01:48:22</div>
              <div class="text-[10px] text-slate-500 uppercase tracking-wider">Time Remaining in Cooling-Off</div>
            </div>
          </div>

          <div class="bg-slate-900 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
            <span class="font-semibold text-slate-200">Customer Interaction Log:</span>
            <p class="text-slate-400">
              "Customer contacted via bank security app. Notified of newly added beneficiary displaying high-velocity smurfing flags. Customer asked to confirm invoice authenticity."
            </p>
          </div>

          <div class="pt-2">
            <span class="text-xs font-semibold text-slate-300 block mb-2">Simulate Recorded Customer Outcome:</span>
            <div class="grid grid-cols-4 gap-3 text-xs">
              <button onclick="recordDemoOutcome('CANCELLED')" class="py-2 px-3 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-700 text-emerald-300 font-medium transition">
                &check; Cancelled by Sender (Prevented)
              </button>
              <button onclick="recordDemoOutcome('HELD')" class="py-2 px-3 rounded-lg bg-amber-950 hover:bg-amber-900 border border-amber-700 text-amber-300 font-medium transition">
                &excl; Hold for Case Investigation
              </button>
              <button onclick="recordDemoOutcome('RELEASED')" class="py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 font-medium transition">
                Proceed (Customer Confirmed)
              </button>
              <button onclick="recordDemoOutcome('BLOCKED')" class="py-2 px-3 rounded-lg bg-crimson-950 hover:bg-crimson-900 border border-crimson-700 text-crimson-300 font-medium transition">
                Hard Block & Freeze
              </button>
            </div>
          </div>
          <div id="outcome-status-msg" class="text-xs text-emerald-400 font-medium hidden"></div>
        </div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(2)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(4)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 4: Money DNA & Replay</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  } else if (stepNum === 4) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 4 of 7</span>
            <h3 class="text-base font-bold text-white">Money DNA: Proportional Tracing & Timeline Replay</h3>
          </div>
          <button onclick="switchTab('tab-lineage')" class="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 font-medium">
            Open Full Money DNA View &rarr;
          </button>
        </div>
        <p class="text-xs text-slate-300">
          Estimated proportional tracing follows $75,000 from origin through splitting, layering, and exit stages. Proportional tracing is an attribution assumption, not a legal finding.
        </p>

        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div class="grid grid-cols-4 gap-3 text-center text-xs">
            <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span class="text-[10px] text-slate-500 uppercase block font-bold">Hop 0: Origin</span>
              <span class="font-bold text-white block mt-1">ACC-VICTIM-01</span>
              <span class="text-crimson-400 font-mono text-xs">$75,000.00 (100%)</span>
            </div>
            <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span class="text-[10px] text-slate-500 uppercase block font-bold">Hop 1: Inbound Hub</span>
              <span class="font-bold text-white block mt-1">ACC-MULE-HUB1</span>
              <span class="text-crimson-400 font-mono text-xs">$75,000.00 (Aggregated)</span>
            </div>
            <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span class="text-[10px] text-slate-500 uppercase block font-bold">Hop 2: Smurfing Splits</span>
              <span class="font-bold text-white block mt-1">3 Layering Mules</span>
              <span class="text-amber-400 font-mono text-xs">3x ~$24.8k Splits</span>
            </div>
            <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
              <span class="text-[10px] text-slate-500 uppercase block font-bold">Hop 3: Exit Off-Ramps</span>
              <span class="font-bold text-white block mt-1">Crypto & ATM Runners</span>
              <span class="text-emerald-400 font-mono text-xs">$24.8k HELD / $24.1k Out</span>
            </div>
          </div>
        </div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(3)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(5)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 5: Next-Hop Prediction</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  } else if (stepNum === 5) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 5 of 7</span>
            <h3 class="text-base font-bold text-white">Next-Hop Prediction & Preemptive Hold Intervention</h3>
          </div>
          <button onclick="switchTab('tab-nexthop')" class="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 font-medium">
            Open Next-Hop Console &rarr;
          </button>
        </div>
        <p class="text-xs text-slate-300">
          Before layering mule <span class="font-mono text-white">ACC-MULE-002</span> completes an exit transfer, Bloodline ranks predicted next-hop destinations using shared device graphs, historical co-occurrence, and mule vulnerability scores.
        </p>

        <div id="step5-candidates-box" class="space-y-3"></div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(4)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(6)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 6: Case Clock Workflow</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
    loadStep5NextHopDemo();
  } else if (stepNum === 6) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 6 of 7</span>
            <h3 class="text-base font-bold text-white">Case Clock: Configurable State Machine & Audit History</h3>
          </div>
          <button onclick="switchTab('tab-cases')" class="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 font-medium">
            Open Case Manager &rarr;
          </button>
        </div>
        <p class="text-xs text-slate-300">
          Enforces role-based approvals across configurable statutory states with append-only audit tracking:
          <span class="font-mono text-amber-400 text-[11px] block mt-1">suspected &rarr; show_cause_pending &rarr; representation_window &rarr; order_pending &rarr; classified &rarr; reported_closed</span>
        </p>

        <div id="step6-case-clock-card" class="p-5 rounded-xl bg-slate-950 border border-indigo-900/40 space-y-4"></div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(5)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(7)" class="px-4 py-2 bg-crimson-600 hover:bg-crimson-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <span>Proceed to Step 7: Impact Ledger & Baseline</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
    loadStep6CaseDemo();
  } else if (stepNum === 7) {
    container.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <span class="text-xs font-bold text-crimson-400 uppercase">Walkthrough Step 7 of 7</span>
            <h3 class="text-base font-bold text-white">Impact Ledger & Comparative Rule-Only Baseline</h3>
          </div>
          <button onclick="switchTab('tab-impact')" class="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 font-medium">
            View Complete Impact Table &rarr;
          </button>
        </div>
        <p class="text-xs text-slate-300">
          Rigorous benchmarking against documented static rule baseline on synthetic held-out scenarios (N=10,000 transfers). State clearly that all metrics are synthetic.
        </p>

        <div class="grid grid-cols-4 gap-3 text-xs">
          <div class="p-3 bg-slate-950 rounded-lg border border-emerald-900/60">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Prevented Amount</span>
            <span class="text-lg font-bold font-mono text-emerald-400">$450,000</span>
            <span class="text-[10px] text-slate-500 block mt-0.5">18 Intercepted Chains</span>
          </div>
          <div class="p-3 bg-slate-950 rounded-lg border border-amber-900/60">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">At Risk (Cooling-Off)</span>
            <span class="text-lg font-bold font-mono text-amber-400">$98,500</span>
            <span class="text-[10px] text-slate-500 block mt-0.5">4 Active Reviews</span>
          </div>
          <div class="p-3 bg-slate-950 rounded-lg border border-crimson-900/60">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Lost (Exit Cleared)</span>
            <span class="text-lg font-bold font-mono text-crimson-400">$32,000</span>
            <span class="text-[10px] text-slate-500 block mt-0.5">Prior to behavioral onset</span>
          </div>
          <div class="p-3 bg-slate-950 rounded-lg border border-slate-800">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Detection Precision</span>
            <span class="text-lg font-bold font-mono text-indigo-400">92.4% vs 54.1%</span>
            <span class="text-[10px] text-emerald-400 block mt-0.5">+38.3% over static rules</span>
          </div>
        </div>

        <div class="flex justify-between pt-3">
          <button onclick="runWalkthroughStep(6)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded">&larr; Back</button>
          <button onclick="runWalkthroughStep(1)" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5">
            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
            <span>Walkthrough Complete • Restart</span>
          </button>
        </div>
      </div>
    `;
  }

  if (window.lucide) lucide.createIcons();
}

async function executeDemoScoringStep2() {
  const container = document.getElementById('step2-score-output');
  try {
    const res = await fetch('/api/v1/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transaction_id: 'TXN-ORIGIN-75K',
        amount: 75000.0,
        currency: 'USD',
        sender_account_id: 'ACC-VICTIM-01',
        receiver_account_id: 'ACC-MULE-HUB1',
        channel: 'WIRE'
      })
    });
    const data = await res.json();
    container.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold text-white font-mono">${data.transaction_id}</span>
          <span class="px-2 py-0.5 text-[10px] rounded font-bold ${data.recommended_action === 'DELAY_REVIEW' ? 'bg-amber-950 text-amber-300 border border-amber-700' : 'bg-crimson-950 text-crimson-300'}">
            Verdict: ${data.recommended_action}
          </span>
        </div>
        <span class="text-xs font-mono text-slate-400">Latency: ${data.latency_ms} ms</span>
      </div>
      <div class="grid grid-cols-3 gap-2 text-xs">
        <div><span class="text-slate-500">Risk Score:</span> <span class="font-bold text-crimson-400 font-mono text-base ml-1">${data.risk_score}</span></div>
        <div><span class="text-slate-500">Model:</span> <span class="font-mono text-slate-300 ml-1">${data.model_version}</span></div>
        <div><span class="text-slate-500">Policy:</span> <span class="font-mono text-slate-300 ml-1">${data.policy_version}</span></div>
      </div>
      <div class="space-y-1.5 pt-1">
        <span class="text-[11px] font-semibold text-slate-300">Evidence Reason Codes:</span>
        ${data.reason_codes.map(r => `
          <div class="p-2 rounded bg-slate-900 border border-slate-800 flex items-start space-x-2 text-xs">
            <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-crimson-950 text-crimson-300 border border-crimson-800 shrink-0">${r.code}</span>
            <span class="text-slate-300">${r.evidence}</span>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="text-crimson-400 text-xs">Error scoring transaction: ${err.message}</div>`;
  }
}

async function recordDemoOutcome(outcome) {
  const msgEl = document.getElementById('outcome-status-msg');
  try {
    const res = await fetch('/api/v1/payments/TXN-ORIGIN-75K/outcomes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_id: 'TXN-ORIGIN-75K',
        outcome: outcome,
        analyst_id: 'analyst_primary',
        notes: `Simulated walkthrough outcome recorded: ${outcome}`
      })
    });
    const data = await res.json();
    msgEl.classList.remove('hidden');
    msgEl.textContent = `Outcome ${outcome} successfully committed to payment core audit ledger!`;
  } catch (err) {
    alert(err.message);
  }
}

async function loadStep5NextHopDemo() {
  const box = document.getElementById('step5-candidates-box');
  try {
    const res = await fetch('/api/v1/predictions/next-hop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id: 'ACC-MULE-002', top_k: 3 })
    });
    const data = await res.json();
    box.innerHTML = data.candidates.map(c => `
      <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-mono font-bold text-amber-400">Rank #${c.rank}: ${c.account_id}</span>
            <span class="text-slate-300 font-medium">(${c.pseudonymous_label})</span>
          </div>
          <div class="text-[11px] text-slate-400 mt-1">${c.evidence.join(' • ')}</div>
        </div>
        <div class="text-right flex items-center space-x-3">
          <div>
            <div class="font-mono font-bold text-emerald-400 text-sm">${(c.predicted_probability * 100).toFixed(1)}%</div>
            <div class="text-[9px] text-slate-500 uppercase">Probability</div>
          </div>
          <button onclick="simulatePreemptiveFreeze('${c.account_id}')" class="px-2.5 py-1.5 bg-crimson-950 hover:bg-crimson-900 border border-crimson-700 text-crimson-300 font-semibold rounded text-[11px] transition">
            Simulate Hold
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    box.innerHTML = `<div class="text-crimson-400 text-xs">Error loading next-hop predictions: ${err.message}</div>`;
  }
}

function simulatePreemptiveFreeze(accountId) {
  alert(`Preemptive holding order dispatched for candidate ${accountId}. Predicted next-hop edge flagged as INTERCEPTED.`);
}

async function loadStep6CaseDemo() {
  const box = document.getElementById('step6-case-clock-card');
  try {
    const res = await fetch('/api/v1/cases/CASE-2026-ALPHA-01');
    const c = await res.json();
    box.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span class="font-mono text-xs font-bold text-indigo-400">${c.case_id}</span>
          <span class="text-xs text-slate-300 ml-2">Target Account: <strong class="font-mono text-white">${c.account_id}</strong></span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-[10px] px-2 py-0.5 rounded font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
            Current State: ${c.current_state}
          </span>
          <span class="text-[10px] px-2 py-0.5 rounded font-mono bg-amber-950 text-amber-300 border border-amber-800">
            Clock: ~34h remaining
          </span>
        </div>
      </div>

      <div class="text-xs space-y-2">
        <span class="font-semibold text-slate-300">Regulatory Draft Memo (Advisory):</span>
        <div class="p-3 bg-slate-900 rounded border border-slate-800 text-[11px] text-slate-400 font-mono">
          ${c.draft_document ? c.draft_document.summary : 'Drafting memorandum...'}
        </div>
      </div>

      <div class="pt-2">
        <span class="text-xs font-semibold text-slate-300 block mb-2">Role-Based Transition Gate (Authorized Role: ${c.assigned_role_required}):</span>
        <div class="flex items-center space-x-2 text-xs">
          <button onclick="transitionCaseDemo('order_pending', 'senior_investigator')" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded transition">
            Issue Provisional Order &rarr;
          </button>
          <button onclick="transitionCaseDemo('false_positive_closed', 'analyst')" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-medium rounded transition">
            Close as False Positive
          </button>
        </div>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div class="text-crimson-400 text-xs">Error loading case: ${err.message}</div>`;
  }
}

async function transitionCaseDemo(toState, role) {
  try {
    const res = await fetch(`/api/v1/cases/CASE-2026-ALPHA-01/transitions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to_state: toState,
        actor_id: 'investigator_dan',
        actor_role: role,
        reason: 'Authorized transition executed during walkthrough review',
        approval_token: 'TOKEN-AUTH-8891'
      })
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Transition rejected: ${err.detail}`);
      return;
    }
    alert(`Case transitioned to ${toState}!`);
    loadStep6CaseDemo();
  } catch (err) {
    alert(err.message);
  }
}

// ========================================================
// 5. TRANSACTION RISK SCORING SIMULATOR
// ========================================================
function loadScoringPreset() {
  const preset = document.getElementById('scoring-preset').value;
  const txIdEl = document.getElementById('score-tx-id');
  const senderEl = document.getElementById('score-sender');
  const recEl = document.getElementById('score-receiver');
  const amtEl = document.getElementById('score-amount');
  const chEl = document.getElementById('score-channel');

  if (preset === 'mule_hub') {
    txIdEl.value = 'TXN-SIM-75K';
    senderEl.value = 'ACC-VICTIM-01';
    recEl.value = 'ACC-MULE-HUB1';
    amtEl.value = '75000';
    chEl.value = 'FAST_PAY';
  } else if (preset === 'legit_payroll') {
    txIdEl.value = 'TXN-SIM-PAYROLL';
    senderEl.value = 'ACC-LEGIT-CORP';
    recEl.value = 'ACC-LEGIT-RETAIL';
    amtEl.value = '3200';
    chEl.value = 'ACH';
  } else if (preset === 'structuring') {
    txIdEl.value = 'TXN-SIM-STRUCT';
    senderEl.value = 'ACC-RING-A';
    recEl.value = 'ACC-RING-B';
    amtEl.value = '9500';
    chEl.value = 'WIRE';
  } else if (preset === 'dormant') {
    txIdEl.value = 'TXN-SIM-DORMANT';
    senderEl.value = 'ACC-VICTIM-01';
    recEl.value = 'ACC-DORMANT-01';
    amtEl.value = '45000';
    chEl.value = 'WIRE';
  }
}

async function executeScoring() {
  const reqBody = {
    transaction_id: document.getElementById('score-tx-id').value,
    amount: parseFloat(document.getElementById('score-amount').value),
    currency: 'USD',
    sender_account_id: document.getElementById('score-sender').value,
    receiver_account_id: document.getElementById('score-receiver').value,
    channel: document.getElementById('score-channel').value
  };

  const placeholder = document.getElementById('scoring-result-placeholder');
  const resultBox = document.getElementById('scoring-result-content');

  try {
    const res = await fetch('/api/v1/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody)
    });
    const data = await res.json();

    placeholder.classList.add('hidden');
    resultBox.classList.remove('hidden');

    let badgeClass = 'bg-emerald-950 text-emerald-300 border-emerald-700';
    if (data.recommended_action === 'HOLD_FREEZE') badgeClass = 'bg-crimson-950 text-crimson-300 border-crimson-700';
    else if (data.recommended_action === 'DELAY_REVIEW') badgeClass = 'bg-amber-950 text-amber-300 border-amber-700';
    else if (data.recommended_action === 'REVIEW') badgeClass = 'bg-indigo-950 text-indigo-300 border-indigo-700';

    resultBox.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span class="text-xs text-slate-400">Scored Transaction ID:</span>
          <div class="text-base font-bold font-mono text-white">${data.transaction_id}</div>
        </div>
        <div class="text-right">
          <span class="px-3 py-1 text-xs rounded-full border font-bold ${badgeClass}">
            Verdict: ${data.recommended_action}
          </span>
          <div class="text-[10px] text-slate-500 mt-1 font-mono">Latency: ${data.latency_ms} ms</div>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
        <div>
          <span class="text-slate-500 block">Risk Score</span>
          <span class="text-lg font-bold font-mono ${data.risk_score >= 0.7 ? 'text-crimson-400' : 'text-emerald-400'}">${data.risk_score}</span>
        </div>
        <div>
          <span class="text-slate-500 block">Cooling-Off</span>
          <span class="text-slate-300 font-mono">${data.cooling_off_hours ? `${data.cooling_off_hours} Hours` : 'None'}</span>
        </div>
        <div>
          <span class="text-slate-500 block">Model Version</span>
          <span class="text-slate-300 font-mono">${data.model_version}</span>
        </div>
        <div>
          <span class="text-slate-500 block">Decision ID</span>
          <span class="text-slate-300 font-mono">${data.decision_id}</span>
        </div>
      </div>

      ${data.customer_warning ? `
        <div class="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-xs text-amber-300">
          <strong>Customer Advisory:</strong> ${data.customer_warning}
        </div>
      ` : ''}

      <div class="space-y-2">
        <h4 class="text-xs font-semibold text-slate-300">Evidence Reason Codes (${data.reason_codes.length}):</h4>
        <div class="space-y-1.5">
          ${data.reason_codes.map(r => `
            <div class="p-2.5 bg-slate-950 border border-slate-800 rounded-lg flex items-start space-x-2 text-xs">
              <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-crimson-950 text-crimson-300 border border-crimson-800 font-semibold shrink-0">
                ${r.code}
              </span>
              <span class="text-slate-300">${r.evidence}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    alert(`Scoring error: ${err.message}`);
  }
}

// ========================================================
// 6. CYTOSCAPE NETWORK GRAPH VIEW
// ========================================================
async function loadNetworkGraph() {
  const accountSelect = document.getElementById('graph-account-select');
  if (!accountSelect) return;
  const accountId = accountSelect.value;
  const hops = document.getElementById('graph-hops-select').value;

  try {
    const res = await fetch(`/api/v1/accounts/${accountId}/network?hop_depth=${hops}`);
    const data = await res.json();

    let predictedEdges = [];
    if (showNextHopOverlay && (accountId.includes('MULE') || accountId.includes('HUB'))) {
      try {
        const predRes = await fetch('/api/v1/predictions/next-hop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ account_id: accountId, top_k: 2 })
        });
        const predData = await predRes.json();
        predictedEdges = predData.candidates.map(c => ({
          data: {
            id: `pred-${accountId}-${c.account_id}`,
            source: accountId,
            target: c.account_id,
            label: `PREDICTED (${(c.predicted_probability * 100).toFixed(0)}%)`,
            is_predicted: true
          }
        }));
      } catch (e) {
        console.warn('Prediction overlay fetch skipped:', e);
      }
    }

    renderCytoscape(data, predictedEdges);
  } catch (err) {
    console.error('Network load error:', err);
  }
}

function renderCytoscape(graphData, predictedEdges = []) {
  const canvas = document.getElementById('network-canvas');
  if (!canvas) return;

  const elements = [];

  graphData.nodes.forEach(n => {
    let nodeColor = '#38bdf8';
    let nodeShape = 'ellipse';

    if (n.type === 'device') {
      nodeColor = '#a855f7';
      nodeShape = 'diamond';
    } else if (n.type === 'ip') {
      nodeColor = '#06b6d4';
      nodeShape = 'rectangle';
    } else if (n.type === 'honeypot') {
      nodeColor = '#f43f5e';
      nodeShape = 'star';
    } else if (n.risk_score && n.risk_score >= 0.8) {
      nodeColor = '#e11d48';
    } else if (n.id.includes('VICTIM')) {
      nodeColor = '#f59e0b';
    } else if (n.id.includes('LEGIT')) {
      nodeColor = '#10b981';
    }

    elements.push({
      data: {
        id: n.id,
        label: n.label || n.id,
        type: n.type,
        risk_score: n.risk_score,
        color: nodeColor,
        shape: nodeShape,
        meta: n.metadata
      }
    });
  });

  graphData.edges.forEach(e => {
    elements.push({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
        amount: e.amount,
        label: e.amount ? `$${(e.amount / 1000).toFixed(1)}k` : e.type,
        is_predicted: false
      }
    });
  });

  if (showNextHopOverlay) {
    elements.push(...predictedEdges);
  }

  cy = cytoscape({
    container: canvas,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': 'data(color)',
          'shape': 'data(shape)',
          'label': 'data(label)',
          'color': '#f8fafc',
          'font-size': '10px',
          'text-valign': 'bottom',
          'text-margin-y': 5,
          'width': 34,
          'height': 34,
          'border-width': 2,
          'border-color': '#0f172a'
        }
      },
      {
        selector: 'edge[?is_predicted]',
        style: {
          'line-color': '#f59e0b',
          'line-style': 'dashed',
          'width': 3,
          'target-arrow-color': '#f59e0b',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'color': '#fbbf24',
          'font-size': '9px'
        }
      },
      {
        selector: 'edge[!is_predicted]',
        style: {
          'line-color': '#475569',
          'width': 2,
          'target-arrow-color': '#475569',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'color': '#94a3b8',
          'font-size': '9px'
        }
      }
    ],
    layout: {
      name: 'concentric',
      animate: false,
      concentric: function(node) {
        return node.data('risk_score') ? node.data('risk_score') * 10 : 2;
      },
      levelWidth: function() { return 2; }
    }
  });

  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    inspectGraphNode(node.data());
  });
}

function inspectGraphNode(nodeData) {
  const inspector = document.getElementById('graph-inspector');
  if (!inspector) return;
  inspector.innerHTML = `
    <h4 class="font-bold text-white border-b border-slate-800 pb-2">Entity: ${nodeData.id}</h4>
    <div class="space-y-2 text-xs">
      <div><span class="text-slate-400">Label:</span> <span class="text-slate-200">${nodeData.label}</span></div>
      <div><span class="text-slate-400">Type:</span> <span class="font-mono text-slate-300 uppercase">${nodeData.type}</span></div>
      ${nodeData.risk_score !== undefined ? `
        <div><span class="text-slate-400">Risk Score:</span> <span class="font-mono font-bold ${nodeData.risk_score >= 0.8 ? 'text-crimson-400' : 'text-emerald-400'}">${nodeData.risk_score}</span></div>
      ` : ''}
      ${nodeData.meta ? `
        <div class="pt-2 border-t border-slate-800 space-y-1">
          <div><span class="text-slate-400">Balance:</span> <span class="font-mono text-slate-200">$${(nodeData.meta.balance || 0).toLocaleString()}</span></div>
          <div><span class="text-slate-400">24h Outflow:</span> <span class="font-mono text-slate-200">$${(nodeData.meta.velocity_out_24h || 0).toLocaleString()}</span></div>
          <div><span class="text-slate-400">Dormant Re-activated:</span> <span class="font-mono ${nodeData.meta.is_dormant_reactivated ? 'text-amber-400 font-bold' : 'text-slate-400'}">${nodeData.meta.is_dormant_reactivated ? 'YES' : 'NO'}</span></div>
        </div>
      ` : ''}
    </div>
  `;
}

function toggleNextHopOverlay() {
  showNextHopOverlay = !showNextHopOverlay;
  const btn = document.getElementById('btn-toggle-overlay');
  if (btn) {
    if (showNextHopOverlay) {
      btn.className = 'px-3 py-1.5 rounded-lg bg-amber-950 text-amber-300 border border-amber-700/60 font-medium transition';
      btn.textContent = 'Next-Hop Overlay: ON';
    } else {
      btn.className = 'px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 border border-slate-700 font-medium transition';
      btn.textContent = 'Next-Hop Overlay: OFF';
    }
  }
  loadNetworkGraph();
}

// ========================================================
// 7. MONEY DNA (SANKEY FLOW & TIMELINE)
// ========================================================
async function loadMoneyDNA() {
  try {
    const res = await fetch('/api/v1/lineage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin_transaction_id: 'TXN-ORIGIN-75K',
        time_window_hours: 72,
        max_hops: 4
      })
    });
    lineageData = await res.json();
    renderMoneyDNASankey(lineageData);

    const stats = document.getElementById('dna-summary-stats');
    if (stats) {
      stats.innerHTML = `
        <span class="text-slate-400">Origin: <strong class="text-white">$${lineageData.origin_amount.toLocaleString()}</strong></span>
        <span class="text-slate-400">Tracked: <strong class="text-amber-400">$${lineageData.total_tainted_tracked.toLocaleString()}</strong></span>
        <span class="text-slate-400">Frozen: <strong class="text-emerald-400">$${lineageData.total_frozen.toLocaleString()}</strong></span>
      `;
    }

    const slider = document.getElementById('timeline-slider');
    if (slider && lineageData.timeline_steps.length > 0) {
      slider.max = lineageData.timeline_steps.length;
      slider.value = 1;
      updateTimelineScrubber(1);
    }
  } catch (err) {
    console.error('Money DNA error:', err);
  }
}

function renderMoneyDNASankey(data) {
  const grid = document.getElementById('sankey-nodes-grid');
  if (!grid) return;

  const hops = { 0: [], 1: [], 2: [], 3: [] };
  data.nodes.forEach(n => {
    if (hops[n.hop_layer] !== undefined) {
      hops[n.hop_layer].push(n);
    }
  });

  const titles = [
    'Hop 0: Origin Compromise',
    'Hop 1: Inbound Aggregator',
    'Hop 2: Smurfing Splits',
    'Hop 3: Exits & Freezes'
  ];

  grid.innerHTML = [0, 1, 2, 3].map(h => `
    <div class="flex flex-col space-y-3 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${titles[h]}</span>
      <div class="space-y-2 flex-1 overflow-y-auto">
        ${hops[h].map(n => `
          <div class="p-2.5 rounded-lg bg-slate-950 border ${n.frozen_status ? 'border-emerald-600/60' : 'border-slate-800'} space-y-1 text-xs">
            <div class="flex items-center justify-between">
              <span class="font-mono font-bold text-slate-200">${n.account_id}</span>
              ${n.frozen_status ? '<span class="px-1.5 py-0.2 rounded text-[9px] bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold">FROZEN</span>' : ''}
            </div>
            <div class="text-[11px] text-slate-400 truncate">${n.account_label}</div>
            <div class="text-[11px] text-amber-400 font-mono font-semibold">
              $${n.tainted_amount_received.toLocaleString()} tainted
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

function updateTimelineScrubber(val) {
  if (!lineageData || !lineageData.timeline_steps) return;
  const step = lineageData.timeline_steps[val - 1];
  if (!step) return;

  const label = document.getElementById('scrubber-time-label');
  const desc = document.getElementById('scrubber-description');
  if (label) label.textContent = `Step ${val} of ${lineageData.timeline_steps.length}`;
  if (desc) desc.textContent = step.description;
}

// ========================================================
// 8. NEXT-HOP PREDICTION
// ========================================================
async function loadNextHopPredictions() {
  const accountSelect = document.getElementById('nexthop-account-select');
  if (!accountSelect) return;
  const accountId = accountSelect.value;
  const container = document.getElementById('nexthop-candidates-list');

  try {
    const res = await fetch('/api/v1/predictions/next-hop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id: accountId, top_k: 4 })
    });
    const data = await res.json();

    container.innerHTML = data.candidates.map(c => `
      <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs space-x-4">
        <div class="space-y-1 flex-1">
          <div class="flex items-center space-x-2">
            <span class="font-mono font-bold text-amber-400 text-sm">Rank #${c.rank}: ${c.account_id}</span>
            <span class="text-slate-300 font-medium">${c.pseudonymous_label}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
              Est. Amount: ${c.predicted_amount_range}
            </span>
          </div>
          <div class="text-slate-400 text-[11px]">${c.evidence.join(' • ')}</div>
        </div>

        <div class="flex items-center space-x-4 shrink-0">
          <div class="text-right">
            <div class="text-lg font-bold font-mono text-emerald-400">${(c.predicted_probability * 100).toFixed(1)}%</div>
            <div class="text-[9px] text-slate-500 uppercase">Calibrated Confidence</div>
          </div>
          <button onclick="simulatePreemptiveFreeze('${c.account_id}')" class="px-3 py-2 bg-crimson-600 hover:bg-crimson-500 text-white font-semibold rounded-lg text-xs transition">
            Simulate Hold Order
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    if (container) container.innerHTML = `<div class="text-crimson-400 text-xs">Error loading next-hop predictions: ${err.message}</div>`;
  }
}

// ========================================================
// 9. CASE CLOCK & WORKFLOW
// ========================================================
async function loadCases() {
  const container = document.getElementById('cases-list-container');
  if (!container) return;

  try {
    const res = await fetch('/api/v1/cases');
    const cases = await res.json();

    container.innerHTML = cases.map(c => `
      <div onclick="selectCase('${c.case_id}')" class="p-3 rounded-lg border ${c.case_id === selectedCaseId ? 'bg-slate-850 border-indigo-600' : 'bg-slate-950 border-slate-800 hover:border-slate-700'} cursor-pointer transition space-y-1">
        <div class="flex items-center justify-between">
          <span class="font-mono font-bold text-white">${c.case_id}</span>
          <span class="px-1.5 py-0.5 rounded text-[9px] font-mono ${c.priority === 'HIGH' ? 'bg-crimson-950 text-crimson-300' : 'bg-slate-800 text-slate-300'}">${c.priority}</span>
        </div>
        <div class="text-[11px] text-slate-400">${c.account_id}</div>
        <div class="flex items-center justify-between text-[10px] text-indigo-400 font-mono pt-1">
          <span>${c.current_state}</span>
          <span>${c.time_remaining_minutes !== null ? `~${Math.round(c.time_remaining_minutes / 60)}h left` : 'Closed'}</span>
        </div>
      </div>
    `).join('');

    if (selectedCaseId) {
      renderCaseDetail(selectedCaseId);
    }
  } catch (err) {
    if (container) container.innerHTML = `<div class="text-crimson-400 text-xs">Error loading cases: ${err.message}</div>`;
  }
}

function selectCase(caseId) {
  selectedCaseId = caseId;
  loadCases();
}

async function renderCaseDetail(caseId) {
  const detailBox = document.getElementById('case-detail-container');
  if (!detailBox) return;

  try {
    const res = await fetch(`/api/v1/cases/${caseId}`);
    const c = await res.json();

    const states = [
      'suspected',
      'show_cause_pending',
      'representation_window',
      'order_pending',
      'classified',
      'reported_closed'
    ];

    detailBox.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span class="font-mono text-sm font-bold text-indigo-400">${c.case_id}</span>
          <div class="text-xs text-slate-400 mt-0.5">Account: <strong class="text-white font-mono">${c.account_id}</strong> • Transaction: <span class="font-mono text-slate-300">${c.transaction_id || 'N/A'}</span></div>
        </div>
        <div class="text-right">
          <span class="px-3 py-1 rounded bg-amber-950 border border-amber-800 text-amber-300 font-mono text-xs">
            Clock: ${c.time_remaining_minutes !== null ? `${Math.round(c.time_remaining_minutes / 60)} Hours Remaining` : 'Closed'}
          </span>
          <div class="text-[10px] text-slate-500 mt-1 font-mono">Role Required: ${c.assigned_role_required}</div>
        </div>
      </div>

      <div class="space-y-1.5 pt-2">
        <span class="text-xs font-semibold text-slate-300">Case State Pipeline:</span>
        <div class="grid grid-cols-6 gap-1 text-center text-[10px] font-mono">
          ${states.map(s => {
            const isCurrent = (s === c.current_state);
            const isPassed = states.indexOf(s) < states.indexOf(c.current_state);
            let cls = 'bg-slate-950 text-slate-500 border-slate-800';
            if (isCurrent) cls = 'bg-indigo-950 text-indigo-300 border-indigo-600 font-bold';
            else if (isPassed) cls = 'bg-slate-900 text-slate-400 border-slate-700';
            return `<div class="p-2 rounded border ${cls}">${s.replace(/_/g, ' ')}</div>`;
          }).join('')}
        </div>
      </div>

      ${c.draft_document ? `
        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-200">Regulatory Draft Document</span>
            <span class="text-[10px] text-slate-500 font-mono">${c.draft_document.reference_no || 'DOC-2026-DRAFT'}</span>
          </div>
          <p class="text-slate-400 font-mono text-[11px]">${c.draft_document.summary}</p>
          <div class="text-[10px] text-amber-400/80 italic">Advisory notice: Automated AI / schema draft; requires officer approval.</div>
        </div>
      ` : ''}

      <div class="space-y-2 pt-2">
        <span class="text-xs font-semibold text-slate-300">Append-Only Audit History (${c.audit_history.length} Events):</span>
        <div class="space-y-1.5 max-h-40 overflow-y-auto pr-1 text-xs font-mono">
          ${c.audit_history.map(a => `
            <div class="p-2 rounded bg-slate-950 border border-slate-800 flex items-start justify-between text-[11px]">
              <div>
                <span class="text-indigo-400 font-bold">${a.prior_state} &rarr; ${a.new_state}</span>
                <span class="text-slate-400 ml-2">(${a.reason})</span>
              </div>
              <span class="text-slate-500 text-[10px] shrink-0 ml-2">${a.actor_id}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (err) {
    detailBox.innerHTML = `<div class="text-crimson-400 text-xs">Error loading case details: ${err.message}</div>`;
  }
}

// ========================================================
// 10. BUSINESS SHIELD (VENDOR CHECK)
// ========================================================
async function executeVendorCheck() {
  const reqBody = {
    vendor_id: document.getElementById('vendor-select').value,
    vendor_name: 'Apex Facilities & Cloud Supplies Ltd',
    proposed_destination_account: document.getElementById('vendor-dest-account').value,
    invoice_number: document.getElementById('vendor-invoice-no').value,
    amount: parseFloat(document.getElementById('vendor-amount').value)
  };

  const box = document.getElementById('vendor-result-box');
  try {
    const res = await fetch('/api/v1/vendor-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody)
    });
    const data = await res.json();

    let bgClass = 'bg-emerald-950 border-emerald-800 text-emerald-300';
    if (data.risk_level === 'CRITICAL') bgClass = 'bg-crimson-950 border-crimson-800 text-crimson-300';
    else if (data.risk_level === 'HIGH') bgClass = 'bg-amber-950 border-amber-800 text-amber-300';

    box.className = `bg-slate-950 p-5 rounded-xl border border-slate-800 text-xs space-y-4`;
    box.innerHTML = `
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-white">Vendor Protection Audit Result</span>
        <span class="px-2.5 py-1 rounded text-xs font-bold border ${bgClass}">
          Risk: ${data.risk_level}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-2 text-xs">
        <div><span class="text-slate-400">Hours Since Detail Change:</span> <strong class="text-amber-400 ml-1">${data.hours_since_bank_change}h</strong></div>
        <div><span class="text-slate-400">Destination Mule Index:</span> <strong class="text-crimson-400 ml-1">${data.account_mule_score}</strong></div>
        <div><span class="text-slate-400">Account Divergence:</span> <strong class="text-crimson-400 ml-1">${data.divergence_flag ? 'YES' : 'NO'}</strong></div>
        <div><span class="text-slate-400">Action:</span> <strong class="text-white ml-1">${data.recommended_action}</strong></div>
      </div>

      <div class="space-y-1 pt-1">
        <span class="font-semibold text-slate-300">Evidence Signals:</span>
        ${data.evidence.map(e => `
          <div class="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[11px]">&excl; ${e}</div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    alert(err.message);
  }
}

// ========================================================
// 11. IMPACT LEDGER & BASELINE METRICS
// ========================================================
async function loadImpactMetrics() {
  try {
    const res = await fetch('/api/v1/impact');
    const data = await res.json();

    const kpi = document.getElementById('impact-kpi-cards');
    if (kpi) {
      kpi.innerHTML = `
        <div class="p-4 bg-slate-900 rounded-xl border border-emerald-900/50 space-y-1">
          <span class="text-[10px] text-slate-400 uppercase font-bold">Prevented Amount</span>
          <div class="text-2xl font-bold font-mono text-emerald-400">$${data.prevented_amount_usd.toLocaleString()}</div>
          <span class="text-[11px] text-slate-400">18 Confirmed Ring Halts</span>
        </div>
        <div class="p-4 bg-slate-900 rounded-xl border border-amber-900/50 space-y-1">
          <span class="text-[10px] text-slate-400 uppercase font-bold">At-Risk (Active Reviews)</span>
          <div class="text-2xl font-bold font-mono text-amber-400">$${data.at_risk_amount_usd.toLocaleString()}</div>
          <span class="text-[11px] text-slate-400">Cooling-Off Delays</span>
        </div>
        <div class="p-4 bg-slate-900 rounded-xl border border-crimson-900/50 space-y-1">
          <span class="text-[10px] text-slate-400 uppercase font-bold">Confirmed Lost</span>
          <div class="text-2xl font-bold font-mono text-crimson-400">$${data.lost_amount_usd.toLocaleString()}</div>
          <span class="text-[11px] text-slate-400">Instant Cashout Exits</span>
        </div>
        <div class="p-4 bg-slate-900 rounded-xl border border-indigo-900/50 space-y-1">
          <span class="text-[10px] text-slate-400 uppercase font-bold">Net Fraud Savings</span>
          <div class="text-2xl font-bold font-mono text-indigo-400">$${data.net_prevented_savings_usd.toLocaleString()}</div>
          <span class="text-[11px] text-emerald-400 font-medium">After FP friction offset</span>
        </div>
      `;
    }

    const tbody = document.getElementById('baseline-comparison-tbody');
    if (tbody && data.comparison_with_rule_baseline && data.comparison_with_rule_baseline.metrics) {
      tbody.innerHTML = data.comparison_with_rule_baseline.metrics.map(m => `
        <tr class="border-b border-slate-800 hover:bg-slate-900/50">
          <td class="py-3 px-4 font-semibold text-white">${m.metric}</td>
          <td class="py-3 px-4 text-slate-400">${m.category}</td>
          <td class="py-3 px-4 font-mono font-bold text-emerald-400">${m.bloodline_2}</td>
          <td class="py-3 px-4 font-mono text-slate-400">${m.rule_baseline}</td>
          <td class="py-3 px-4 font-medium text-amber-300">${m.improvement}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Impact load error:', err);
  }
}

function updateThresholdLabel(val) {
  const lbl = document.getElementById('current-threshold-label');
  if (lbl) lbl.textContent = `Auto-Freeze Threshold: ${parseFloat(val).toFixed(2)}`;
}

async function submitThresholdChange() {
  const val = parseFloat(document.getElementById('threshold-slider').value);
  try {
    const res = await fetch('/api/v1/thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        threshold_key: 'hold_freeze_min',
        new_value: val,
        actor_id: 'compliance_officer_dan',
        justification: 'Audited threshold calibration via Analyst Dashboard slider'
      })
    });
    if (!res.ok) {
      const err = await res.json();
      alert(`Threshold adjustment failed: ${err.detail}`);
      return;
    }
    alert(`Threshold updated to ${val.toFixed(2)} and logged to audit ledger!`);
  } catch (err) {
    alert(err.message);
  }
}

async function resetDemoData() {
  if (confirm('Reset synthetic environment to pristine initial state?')) {
    try {
      await fetch('/api/v1/demo/reset', { method: 'POST' });
      alert('Synthetic environment reset successfully!');
      location.reload();
    } catch (err) {
      alert(err.message);
    }
  }
}
