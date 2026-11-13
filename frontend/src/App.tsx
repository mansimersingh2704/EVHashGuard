import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopNav } from './components/TopNav';
import { OverviewPage } from './pages/OverviewPage';
import { HashLabPage } from './pages/HashLabPage';
import { CollisionPage } from './pages/CollisionPage';
import { EVSimulatorPage } from './pages/EVSimulatorPage';
import { LegacyMD5Page } from './pages/LegacyMD5Page';
import { MigrationPage } from './pages/MigrationPage';
import { AttackSimPage } from './pages/AttackSimPage';
import { RiskPage } from './pages/RiskPage';
import { AuditPage } from './pages/AuditPage';
import { DocumentationPage } from './pages/DocumentationPage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<string>('overview');

  const pageTitles: Record<string, string> = {
    overview: 'System Overview & Threat Telemetry',
    hash_lab: 'Cryptographic Hash Laboratory',
    collision: 'MD5 Collision Risk Demonstration',
    ev_simulator: 'EV Firmware & OCPP 1.6 Message Simulator',
    legacy_md5: 'Legacy MD5 Integrity Verification Engine',
    migration: 'SHA-3 Backward-Compatible Cryptographic Wrapper',
    attacks: 'Attack Simulation & Defense Verification Lab',
    risk: 'Cryptographic Risk Analysis Matrix',
    audit: 'Security Audit Logs & Journal',
    docs: 'Engineering Specifications & Documentation',
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <OverviewPage />;
      case 'hash_lab':
        return <HashLabPage />;
      case 'collision':
        return <CollisionPage />;
      case 'ev_simulator':
        return <EVSimulatorPage />;
      case 'legacy_md5':
        return <LegacyMD5Page />;
      case 'migration':
        return <MigrationPage />;
      case 'attacks':
        return <AttackSimPage />;
      case 'risk':
        return <RiskPage />;
      case 'audit':
        return <AuditPage />;
      case 'docs':
        return <DocumentationPage />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1e] text-slate-100 flex">
      {/* Sidebar */}
      <Sidebar currentPage={currentPage} onSelectPage={setCurrentPage} />

      {/* Main Content Area */}
      <div className="flex-1 ml-64 flex flex-col min-h-screen bg-[#0a0f1e]">
        <TopNav currentPageTitle={pageTitles[currentPage] || 'Dashboard'} />
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {renderPage()}
        </main>
      </div>
    </div>
  );
};

export default App;
