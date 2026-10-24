import React, { useState, useEffect } from 'react';
import {
  Shield, Sparkles, Share2, GitBranch, Clock, Building2,
  BarChart3, RefreshCw, AlertTriangle, ArrowRight, CheckCircle2,
  Sliders, ShieldCheck, Terminal
} from 'lucide-react';
import { TopBar } from './components/TopBar';
import { Footer } from './components/Footer';
import { WarningModal } from './components/WarningModal';
import { LandingPage } from './pages/LandingPage';
import { ScanPage } from './pages/ScanPage';
import { AnalystConsolePage } from './pages/AnalystConsolePage';
import { CaseQueuePage } from './pages/CaseQueuePage';
import { BusinessShieldPage } from './pages/BusinessShieldPage';
import { ImpactDashboardPage } from './pages/ImpactDashboardPage';
import { fetchStats, resetDemo, submitDecision, fetchDemoStory } from './api';
import { LiveStats, ScanResponse } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'landing' | 'scan' | 'console' | 'cases' | 'vendor' | 'impact'>('landing');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [stats, setStats] = useState<LiveStats | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Warning Modal State
  const [warningModal, setWarningModal] = useState<{
    isOpen: boolean;
    scanData: ScanResponse | null;
  }>({
    isOpen: false,
    scanData: null
  });

  // Prefill state for Scan Page
  const [scanPrefill, setScanPrefill] = useState<{
    accountId?: string;
    amount?: number;
  }>({
    accountId: 'ACC02228',
    amount: 95000.0
  });

  const loadStats = async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (e) {
      console.error('Failed to load stats', e);
    }
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleResetDemo = async () => {
    setIsResetting(true);
    try {
      await resetDemo();
      await loadStats();
      setNotification('Demo state successfully reset to initial baseline.');
      setTimeout(() => setNotification(null), 4000);
    } catch (e) {
      console.error(e);
      setNotification('Failed to reset demo.');
      setTimeout(() => setNotification(null), 4000);
    } finally {
      setIsResetting(false);
    }
  };

  const handleLaunchDemoStory = async () => {
    try {
      const story = await fetchDemoStory();
      const muleL1 = story.anchors?.planted_mule_l1 || 'ACC-MULE-C1-L1-1';
      setScanPrefill({
        accountId: muleL1,
        amount: 95000.0
      });
      setActiveTab('scan');
      setNotification('Planted Story Loaded: ₹95,000 transfer to Mule Hub L1 (ACC-MULE-C1-L1-1). Click "Run Real-Time Scan" to intercept.');
      setTimeout(() => setNotification(null), 6000);
    } catch (e) {
      setActiveTab('scan');
    }
  };

  const handleTriggerWarning = (scanData: ScanResponse) => {
    setWarningModal({
      isOpen: true,
      scanData
    });
  };

  const handleCancelPayment = async () => {
    if (!warningModal.scanData) return;
    try {
      await submitDecision(
        warningModal.scanData.account_id,
        'CANCELLED',
        undefined,
        'Customer aborted transfer during 60s scam cooldown popup'
      );
      await loadStats();
      setNotification('Transaction CANCELLED by customer. ₹ prevented updated in top bar.');
      setTimeout(() => setNotification(null), 4500);
    } catch (e) {
      console.error(e);
    } finally {
      setWarningModal({ isOpen: false, scanData: null });
    }
  };

  const handleProceedAnyway = async () => {
    if (!warningModal.scanData) return;
    try {
      await submitDecision(
        warningModal.scanData.account_id,
        'PROCEEDED',
        undefined,
        'Customer acknowledged high-risk warning and forced transfer after countdown'
      );
      await loadStats();
      setNotification('Transaction PROCEEDED despite warning. Ledger marked for monitoring.');
      setTimeout(() => setNotification(null), 4500);
    } catch (e) {
      console.error(e);
    } finally {
      setWarningModal({ isOpen: false, scanData: null });
    }
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-200 ${
      theme === 'dark' ? 'bg-[#0B1220] text-slate-100' : 'bg-slate-50 text-slate-900'
    }`}>
      {/* Top Bar with Live Impact Counters & Simulated Badge */}
      <TopBar
        stats={stats}
        onReset={handleResetDemo}
        isResetting={isResetting}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Toast Notification Banner */}
      {notification && (
        <div className="bg-gradient-to-r from-rose-900/90 to-amber-900/90 border-b border-rose-500/50 text-white px-6 py-2.5 text-xs font-medium flex items-center justify-between shadow-lg animate-in slide-in-from-top duration-300">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-amber-300 shrink-0" />
            <span>{notification}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-300 hover:text-white text-xs underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Navigation Sub-Bar */}
      <nav className={`border-b px-4 lg:px-6 flex items-center space-x-1 lg:space-x-2 overflow-x-auto shrink-0 scrollbar-none ${
        theme === 'dark' ? 'bg-[#0F172A]/90 border-slate-800' : 'bg-white border-slate-200'
      }`}>
        <button
          onClick={() => setActiveTab('landing')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'landing'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('scan')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'scan'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Pre-Payment Scan</span>
        </button>

        <button
          onClick={() => setActiveTab('console')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'console'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Analyst Console & Money DNA</span>
        </button>

        <button
          onClick={() => setActiveTab('cases')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'cases'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Case Queue (RBI Clock)</span>
        </button>

        <button
          onClick={() => setActiveTab('vendor')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'vendor'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Business Shield (Invoices)</span>
        </button>

        <button
          onClick={() => setActiveTab('impact')}
          className={`px-3.5 py-3 text-xs font-semibold flex items-center space-x-2 border-b-2 transition whitespace-nowrap ${
            activeTab === 'impact'
              ? 'text-[#E5334F] border-[#E5334F]'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Impact & ML Evaluation</span>
        </button>

        <div className="flex-1" />

        <div className="hidden md:flex items-center space-x-2 py-1">
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1 px-2.5 py-1 rounded text-[11px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            <Terminal className="w-3 h-3 text-cyan-400" />
            <span>FastAPI /docs</span>
          </a>
        </div>
      </nav>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8">
        {activeTab === 'landing' && (
          <LandingPage
            stats={stats}
            onNavigate={setActiveTab}
            onLaunchDemoStory={handleLaunchDemoStory}
          />
        )}

        {activeTab === 'scan' && (
          <ScanPage
            onTriggerWarning={handleTriggerWarning}
            initialAccount={scanPrefill.accountId}
            initialAmount={scanPrefill.amount}
          />
        )}

        {activeTab === 'console' && (
          <AnalystConsolePage onRefreshStats={loadStats} />
        )}

        {activeTab === 'cases' && (
          <CaseQueuePage onRefreshStats={loadStats} />
        )}

        {activeTab === 'vendor' && (
          <BusinessShieldPage />
        )}

        {activeTab === 'impact' && (
          <ImpactDashboardPage />
        )}
      </main>

      {/* Regulatory Footer */}
      <Footer />

      {/* Scam Defense Warning Modal */}
      <WarningModal
        isOpen={warningModal.isOpen}
        scanData={warningModal.scanData}
        onCancelPayment={handleCancelPayment}
        onProceedAnyway={handleProceedAnyway}
      />
    </div>
  );
}
