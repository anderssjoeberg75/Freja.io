import { Activity, Cpu, Wifi } from 'lucide-react';
import { useState, useEffect } from 'react';
import { API_URL } from '../config';

export default function Dashboard() {
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch(`${API_URL}/status`);
                if (res.ok) {
                    const data = await res.json();
                    setAgents(data.agents || []);
                }
            } catch (err) {
                console.error("Failed to fetch status:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchStatus();
    }, []);

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Mainframe Overview</h1>
                <p className="text-zinc-400">System Status: <span className="text-green-400">Operational</span></p>
            </header>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <StatCard icon={<Cpu />} label="CPU Load" value="12%" color="text-blue-400" />
                <StatCard icon={<Wifi />} label="Network" value="1.2 Gbps" color="text-purple-400" />
                <StatCard icon={<Activity />} label="AI Latency" value="450ms" color="text-mainframe-accent" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Recent Logs (Mock) */}
                <div className="bg-mainframe-card rounded-2xl p-6 border border-mainframe-border">
                    <h3 className="text-lg font-semibold mb-4 text-white">System Logs</h3>
                    <div className="space-y-3 font-mono text-sm text-zinc-400">
                        <LogEntry time="10:42:15" level="INFO">Mainframe Core initialized.</LogEntry>
                        <LogEntry time="10:42:16" level="INFO">Connected to Mem0 Database.</LogEntry>
                        <LogEntry time="10:42:18" level="WARNING">Garmin Integration: Token expired.</LogEntry>
                        <LogEntry time="10:45:01" level="INFO">Proactive Service: Scan complete.</LogEntry>
                    </div>
                </div>

                {/* Active Agents - Now Dynamic */}
                <div className="bg-mainframe-card rounded-2xl p-6 border border-mainframe-border">
                    <h3 className="text-lg font-semibold mb-4 text-white">Active Agents</h3>
                    <div className="space-y-4">
                        {loading ? (
                            <p className="text-zinc-500 text-sm">Loading...</p>
                        ) : agents.length > 0 ? (
                            agents.map((agent, idx) => (
                                <AgentStatus key={idx} name={agent.name} status={agent.status} />
                            ))
                        ) : (
                            <p className="text-zinc-500 text-sm">No active agents</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

const StatCard = ({ icon, label, value, color }) => (
    <div className="bg-mainframe-card p-6 rounded-2xl border border-mainframe-border flex items-center gap-4">
        <div className={`p-3 rounded-lg bg-zinc-800 ${color}`}>{icon}</div>
        <div>
            <div className="text-zinc-500 text-sm">{label}</div>
            <div className="text-2xl font-bold font-mono">{value}</div>
        </div>
    </div>
);

const LogEntry = ({ time, level, children }) => (
    <div className="flex gap-3">
        <span className="text-zinc-600">[{time}]</span>
        <span className={level === 'WARNING' ? 'text-yellow-500' : 'text-blue-500'}>{level}</span>
        <span>{children}</span>
    </div>
);

const AgentStatus = ({ name, status }) => (
    <div className="flex justify-between items-center p-3 bg-zinc-900/50 rounded-lg">
        <span className="font-medium">{name}</span>
        <span className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-400">{status}</span>
    </div>
);
