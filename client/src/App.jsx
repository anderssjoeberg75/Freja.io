import { useState } from 'react';
import { Terminal, Settings as SettingsIcon, Activity, Mic, MessageSquare, Edit3, Hash } from 'lucide-react';
import Dashboard from './components/Dashboard';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';
import Prompts from './components/Prompts';
import LiveSession from './components/LiveSession';
import AliasView from './components/AliasView';

import { useSocket } from './hooks/useSocket';

function App() {
    const [activeView, setActiveView] = useState('dashboard');
    const { connected: socketConnected } = useSocket();

    return (
        <div className="flex h-screen bg-mainframe-bg text-mainframe-text overflow-hidden">
            {/* Sidebar */}
            <div className="w-16 flex flex-col items-center py-4 border-r border-mainframe-border bg-mainframe-card">
                <div className="mb-8 p-2 rounded-lg bg-mainframe-accent/10">
                    <Terminal className="w-6 h-6 text-mainframe-accent" />
                </div>

                <nav className="flex-1 flex flex-col gap-4">
                    <NavIcon icon={<Activity />} active={activeView === 'dashboard'} onClick={() => setActiveView('dashboard')} />
                    <NavIcon icon={<MessageSquare />} active={activeView === 'chat'} onClick={() => setActiveView('chat')} />
                    <NavIcon icon={<Edit3 />} active={activeView === 'prompts'} onClick={() => setActiveView('prompts')} />
                    <NavIcon icon={<Mic />} active={activeView === 'voice'} onClick={() => setActiveView('voice')} />
                    <NavIcon icon={<Hash />} active={activeView === 'aliases'} onClick={() => setActiveView('aliases')} />
                    <NavIcon icon={<SettingsIcon />} active={activeView === 'settings'} onClick={() => setActiveView('settings')} />
                </nav>

                <div className={`w-3 h-3 rounded-full mb-4 ${socketConnected ? 'bg-green-500' : 'bg-red-500'}`} title={socketConnected ? "Connected" : "Disconnected"} />
            </div>

            {/* Main Content */}
            <main className="flex-1 overflow-auto h-full">
                {activeView === 'dashboard' && <Dashboard />}
                {activeView === 'chat' && <ChatInterface />}
                {activeView === 'prompts' && <Prompts />}
                {activeView === 'voice' && <LiveSession />}
                {activeView === 'aliases' && <AliasView />}
                {activeView === 'settings' && <Settings />}
            </main>
        </div>
    );
}

const NavIcon = ({ icon, active, onClick }) => (
    <button
        onClick={onClick}
        className={`p-3 rounded-xl transition-all ${active ? 'bg-mainframe-accent text-black shadow-lg shadow-mainframe-accent/20' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
    >
        {icon}
    </button>
);

export default App;
