import { useState } from 'react';
import { Terminal, Settings as SettingsIcon, Activity, Mic, MessageSquare, Edit3, Hash, Cpu, Shield } from 'lucide-react';
import Dashboard from './components/Dashboard';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';
import Prompts from './components/Prompts';
import LiveSession from './components/LiveSession';
import AliasView from './components/AliasView';
import OllamaManager from './components/OllamaManager';
import IPAllowlist from './components/IPAllowlist';

import { useSocket } from './hooks/useSocket';

function App() {
    const [activeView, setActiveView] = useState('dashboard');
    const { connected: socketConnected } = useSocket();

    return (
        <div className="flex h-screen bg-mainframe-bg text-mainframe-text overflow-hidden">
            {/* Sidebar */}
            <div className="w-16 flex flex-col items-center py-4 border-r border-mainframe-border bg-mainframe-card overflow-y-auto scrollbar-hide">
                <div className="mb-8 p-2 rounded-lg bg-mainframe-accent/10">
                    <Terminal className="w-6 h-6 text-mainframe-accent" />
                </div>

                <nav className="flex-1 flex flex-col gap-4 w-full items-center">
                    <NavIcon icon={<Activity />} active={activeView === 'dashboard'} onClick={() => setActiveView('dashboard')} title="Dashboard" />
                    <NavIcon icon={<MessageSquare />} active={activeView === 'chat'} onClick={() => setActiveView('chat')} title="Chat" />
                    <NavIcon icon={<Edit3 />} active={activeView === 'prompts'} onClick={() => setActiveView('prompts')} title="Prompts" />
                    <NavIcon icon={<Mic />} active={activeView === 'voice'} onClick={() => setActiveView('voice')} title="Voice Mode" />
                    <NavIcon icon={<Hash />} active={activeView === 'aliases'} onClick={() => setActiveView('aliases')} title="Aliases" />
                    <NavIcon icon={<Cpu />} active={activeView === 'ollama'} onClick={() => setActiveView('ollama')} title="Ollama Models" />

                    <div className="w-8 h-px bg-mainframe-border/50 my-2" />

                    <div className="flex-1" /> {/* Spacer */}

                    <NavIcon icon={<Shield />} active={activeView === 'access_control'} onClick={() => setActiveView('access_control')} title="Access Control" />
                    <NavIcon icon={<SettingsIcon />} active={activeView === 'settings'} onClick={() => setActiveView('settings')} title="System Settings" />
                </nav>

                <div className={`w-3 h-3 rounded-full mt-4 ${socketConnected ? 'bg-green-500' : 'bg-red-500'}`} title={socketConnected ? "Connected" : "Disconnected"} />
            </div>

            {/* Main Content */}
            <main className="flex-1 overflow-auto h-full">
                {activeView === 'dashboard' && <Dashboard />}
                {activeView === 'chat' && <ChatInterface />}
                {activeView === 'prompts' && <Prompts />}
                {activeView === 'voice' && <LiveSession />}
                {activeView === 'aliases' && <AliasView />}
                {activeView === 'settings' && <Settings />}
                {activeView === 'access_control' && <IPAllowlist />}
                {activeView === 'ollama' && (
                    <div className="p-8 max-w-3xl mx-auto h-full overflow-auto">
                        <h1 className="text-3xl font-orbitron text-mainframe-accent mb-8 border-b border-mainframe-border pb-4">Ollama Models</h1>
                        <OllamaManager standalone />
                    </div>
                )}
            </main>
        </div>
    );
}

const NavIcon = ({ icon, active, onClick, title }) => (
    <button
        onClick={onClick}
        title={title}
        className={`p-3 rounded-xl transition-all ${active ? 'bg-mainframe-accent text-black shadow-lg shadow-mainframe-accent/20' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
    >
        {icon}
    </button>
);

export default App;
