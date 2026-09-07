import React from 'react';
import {
  Shield,
  Activity,
  Cpu,
  Lock,
  Network,
  Radio,
  Terminal,
} from '../icons';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealth?: {
    status: string;
    version: string;
    vision_loaded: boolean;
    blockchain_connected: boolean;
    contract_deployed: boolean;
  } | null;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'biometric', label: 'Biometric HUD', icon: <Activity className="w-4 h-4" /> },
    { id: 'osint', label: 'OSINT Radar', icon: <Radio className="w-4 h-4" /> },
    { id: 'dag', label: 'Origin DAG', icon: <Network className="w-4 h-4" /> },
    { id: 'merkle', label: 'Merkle Inspector', icon: <Lock className="w-4 h-4" /> },
    { id: 'takedown', label: 'Web3 Takedown', icon: <Shield className="w-4 h-4" /> },
    { id: 'zk', label: 'ZK Privacy Vault', icon: <Cpu className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 cyber-glass border-b border-cyber-border/40 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Tagline */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyber-cyan to-cyber-emerald flex items-center justify-center p-0.5 shadow-cyber-cyan">
              <div className="w-full h-full bg-cyber-bg rounded-md flex items-center justify-center">
                <Shield className="w-5 h-5 text-cyber-cyan" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-wider text-white font-mono">
                  TRACE<span className="text-cyber-cyan">FACE</span>
                </h1>
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/30 rounded">
                  v1.0.0-FORENSIC
                </span>
              </div>
              <p className="text-[10px] text-gray-400 font-mono hidden sm:block">
                Biometric OSINT & Blockchain Provenance Pipeline
              </p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden md:flex space-x-1 bg-cyber-surface/70 p-1 rounded-xl border border-cyber-border/30">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 shadow-cyber-cyan'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Status Badges */}
          <div className="flex items-center space-x-3 text-xs font-mono">
            {/* FastAPI Backend Status */}
            <div className="hidden sm:flex items-center gap-2 bg-cyber-surface/80 border border-cyber-border/40 px-2.5 py-1 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-cyber-emerald animate-ping" />
              <span className="text-[11px] text-gray-300">FastAPI API</span>
            </div>

            {/* Smart Contract Badge */}
            <div className="hidden lg:flex items-center gap-2 bg-cyber-surface/80 border border-cyber-border/40 px-2.5 py-1 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-cyber-cyan" />
              <span className="text-[11px] text-gray-300">Polygon / Hardhat</span>
            </div>

            {/* Docs link */}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded-lg bg-cyber-surface hover:bg-cyber-cyan/10 border border-cyber-border/40 text-gray-300 hover:text-cyber-cyan transition-all"
              title="FastAPI Swagger OpenAPI Docs"
            >
              <Terminal className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>

      {/* Mobile Nav Scroller */}
      <div className="md:hidden flex overflow-x-auto space-x-1 p-2 bg-cyber-surface/90 border-t border-cyber-border/30">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono whitespace-nowrap flex items-center gap-1.5 ${
                isActive
                  ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
