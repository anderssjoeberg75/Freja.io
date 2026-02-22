import { Activity, Cpu, Wifi } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { API_URL } from '../config';

export default function Dashboard() {
    const [agents, setAgents] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const logsEndRef = useRef(null);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_URL}/status`);
            if (res.ok) {
                const data = await res.json();
                setAgents(data.agents || []);
            }

            const logsRes = await fetch(`${API_URL}/api/logs`);
            if (logsRes.ok) {
                const logData = await logsRes.json();
                setLogs(logData.logs || []);
            }
        } catch (err) {
            console.error("Failed to fetch dashboard data:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    // parse log line: "2026-02-22 06:33:55 | INFO | app.services.tool_registry..."
    const parseLogLine = (line, idx) => {
        const parts = line.split('|');
        if (parts.length >= 3) {
            const time = parts[0].trim().split(' ')[1] || parts[0].trim();
            const level = parts[1].trim();
            const message = parts.slice(2).join('|').trim();
            return <LogEntry key={idx} time={time} level={level}>{message}</LogEntry>;
        }
        return <LogEntry key={idx} time="" level="INFO">{line.trim()}</LogEntry>;
    };

    return (
        <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
            <header className="mb-8 shrink-0">
                <h1 className="text-3xl font-bold text-white mb-2">Mainframe Overview</h1>
                <p className="text-zinc-400">System Status: <span className="text-green-400">Operational</span></p>
            </header>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8 shrink-0">
                <StatCard icon={<Cpu />} label="CPU Load" value="12%" color="text-blue-400" />
                <StatCard icon={<Wifi />} label="Network" value="1.2 Gbps" color="text-purple-400" />
                <StatCard icon={<Activity />} label="AI Latency" value="450ms" color="text-mainframe-accent" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0 pb-8">
                {/* System Logs */}
                <div className="bg-mainframe-card rounded-2xl p-6 border border-mainframe-border flex flex-col h-[500px]">
                    <h3 className="text-lg font-semibold mb-4 text-white shrink-0">System Logs</h3>
                    <div className="space-y-2 font-mono text-[13px] text-zinc-400 overflow-y-auto flex-1 pr-2 custom-scrollbar">
                        {loading && logs.length === 0 ? (
                            <p className="text-zinc-500 text-sm">Loading logs...</p>
                        ) : logs.length > 0 ? (
                            <>
                                {logs.map((line, idx) => parseLogLine(line, idx))}
                                <div ref={logsEndRef} />
                            </>
                        ) : (
                            <p className="text-zinc-500 text-sm">No system logs available</p>
                        )}
                    </div>
                </div>

                {/* Active Agents */}
                <div className="bg-mainframe-card rounded-2xl p-6 border border-mainframe-border flex flex-col h-[500px]">
                    <h3 className="text-lg font-semibold mb-4 text-white shrink-0">Active Agents</h3>
                    <div className="space-y-3 overflow-y-auto flex-1 pr-2 custom-scrollbar">
                        {loading && agents.length === 0 ? (
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

const LogEntry = ({ time, level, children }) => {
    let levelClass = 'text-blue-500';
    if (level.includes('WARN')) levelClass = 'text-yellow-500';
    if (level.includes('ERR')) levelClass = 'text-red-500';
    if (level.includes('DEBUG')) levelClass = 'text-zinc-500';

    return (
        <div className="flex gap-3 leading-tight">
            {time && <span className="text-zinc-600 shrink-0">[{time}]</span>}
            <span className={`${levelClass} shrink-0 w-16`}>{level}</span>
            <span className="break-all">{children}</span>
        </div>
    );
};

const AgentStatus = ({ name, status }) => (
    <div className="flex justify-between items-center p-3 bg-zinc-900/50 rounded-lg">
        <span className="font-medium text-sm">{name}</span>
        <span className="text-[11px] px-2 py-1 rounded bg-zinc-800 text-zinc-400 uppercase tracking-wider">{status}</span>
    </div>
);
