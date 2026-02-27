import React, { useState, useEffect } from 'react';
import { Shield, Save, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { adminFetch } from '../utils/adminFetch';

const IPAllowlist = () => {
    const [allowedIps, setAllowedIps] = useState('');
    const [loading, setLoading] = useState(true);
    const [status, setStatus] = useState({ type: '', message: '' });

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const resp = await adminFetch('/api/settings');
            const data = await resp.json();
            if (data.ALLOWED_IPS !== undefined) {
                setAllowedIps(data.ALLOWED_IPS || '');
            }
        } catch (err) {
            console.error('Failed to fetch settings:', err);
            setStatus({ type: 'error', message: 'Kunde inte hämta inställningar.' });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setStatus({ type: 'info', message: 'Sparar...' });
        try {
            const resp = await adminFetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    key: 'ALLOWED_IPS',
                    value: allowedIps
                })
            });
            const data = await resp.json();
            if (data.success) {
                setStatus({ type: 'success', message: 'IP-lista sparad!' });
                setTimeout(() => setStatus({ type: '', message: '' }), 3000);
            } else {
                setStatus({ type: 'error', message: data.message || 'Ett fel uppstod.' });
            }
        } catch (err) {
            console.error('Failed to save settings:', err);
            setStatus({ type: 'error', message: 'Kunde inte ansluta till servern.' });
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-64 text-mainframe-accent animate-pulse">
            <Shield className="w-8 h-8 mr-2" />
            <span>Laddar säkerhetsinställningar...</span>
        </div>
    );

    return (
        <div className="space-y-6 max-w-2xl mx-auto p-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <header className="flex items-center gap-3 border-b border-mainframe-border pb-4 mb-6">
                <Shield className="w-8 h-8 text-mainframe-accent" />
                <div>
                    <h1 className="text-2xl font-orbitron text-mainframe-accent">Access Control</h1>
                    <p className="text-zinc-500 text-sm">Hantering av tillåtna IP-adresser</p>
                </div>
            </header>

            <div className="bg-mainframe-card border border-mainframe-border rounded-xl p-6 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                    <Shield className="w-24 h-24" />
                </div>

                <div className="space-y-4 relative z-10">
                    <label className="block text-sm font-medium text-zinc-300">
                        Tillåtna IP-adresser (komma-separerade)
                    </label>
                    <textarea
                        value={allowedIps}
                        onChange={(e) => setAllowedIps(e.target.value)}
                        placeholder="t.ex. 192.168.1.10, 85.226.12.3"
                        className="w-full h-32 bg-mainframe-bg border border-mainframe-border rounded-lg p-3 text-mainframe-text font-mono focus:outline-none focus:border-mainframe-accent transition-colors resize-none"
                    />

                    <div className="bg-blue-900/20 border border-blue-800/50 rounded-lg p-4 flex gap-3">
                        <Info className="w-5 h-5 text-blue-400 shrink-0" />
                        <div className="text-sm text-blue-200/80 leading-relaxed">
                            <p className="font-semibold mb-1">Viktig information:</p>
                            <ul className="list-disc list-inside space-y-1">
                                <li>Lämna tomt för att tillåta åtkomst från alla nätverksadresser.</li>
                                <li><strong>Localhost (127.0.0.1)</strong> är alltid tillåten automatiskt.</li>
                                <li>Använd komma (,) för att separera flera adresser.</li>
                            </ul>
                        </div>
                    </div>

                    <div className="bg-amber-900/20 border border-amber-800/50 rounded-lg p-4 flex gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                        <p className="text-sm text-amber-200/80">
                            <strong>Varning:</strong> Om du anger felaktiga IP-adresser kan du låsa ut dig själv från webbgränssnittet. Se till att din nuvarande IP ingår i listan.
                        </p>
                    </div>

                    <button
                        onClick={handleSave}
                        className="w-full flex items-center justify-center gap-2 bg-mainframe-accent hover:bg-mainframe-accent/80 text-black font-bold py-3 rounded-lg transition-all active:scale-95 group"
                    >
                        <Save className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                        Spara inställningar
                    </button>

                    {status.message && (
                        <div className={`flex items-center gap-2 p-3 rounded-lg animate-in fade-in duration-300 ${status.type === 'success' ? 'bg-green-900/30 text-green-400 border border-green-800/50' :
                            status.type === 'error' ? 'bg-red-900/30 text-red-400 border border-red-800/50' :
                                'bg-zinc-800 text-zinc-300'
                            }`}>
                            {status.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <Info className="w-4 h-4" />}
                            <span className="text-sm">{status.message}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default IPAllowlist;
