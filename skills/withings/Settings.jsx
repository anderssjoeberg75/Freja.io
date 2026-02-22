import React, { useState, useEffect } from 'react';
import { Save, Loader2, Activity, Info, Link } from 'lucide-react';

const WithingsSettings = () => {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [showHelp, setShowHelp] = useState(false);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            setSettings(data || {});
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to load settings.' });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleSave = async (key) => {
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value: settings[key] })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: 'Saved successfully!' });
            } else {
                setMessage({ type: 'error', text: 'Failed to save.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving setting.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleConnect = () => {
        const clientId = settings.WITHINGS_CLIENT_ID;
        const redirectUri = settings.WITHINGS_REDIRECT_URI;
        if (!clientId || !redirectUri) {
            setMessage({ type: 'error', text: 'Please enter Client ID and Redirect URI first.' });
            return;
        }
        const url = `https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=${clientId}&state=freja&scope=user.metrics,user.activity&redirect_uri=${encodeURIComponent(redirectUri)}`;
        window.open(url, '_blank');
    };

    if (loading) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center justify-between mb-8 border-b border-mainframe-border pb-4">
                <div className="flex items-center gap-4">
                    <Activity className="w-8 h-8 text-pink-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Withings Health Mate
                    </h1>
                </div>
                <button onClick={() => setShowHelp(true)} className="text-mainframe-text/60 hover:text-mainframe-accent transition-colors">
                    <Info className="w-6 h-6" />
                </button>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">

                {/* Client ID */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Client ID</label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={settings.WITHINGS_CLIENT_ID || ''}
                            onChange={(e) => handleChange('WITHINGS_CLIENT_ID', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('WITHINGS_CLIENT_ID')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                            <Save className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Client Secret */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Client Secret</label>
                    <div className="flex gap-2">
                        <input
                            type="password"
                            value={settings.WITHINGS_CLIENT_SECRET || ''}
                            onChange={(e) => handleChange('WITHINGS_CLIENT_SECRET', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('WITHINGS_CLIENT_SECRET')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                            <Save className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Redirect URI */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Redirect URI</label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={settings.WITHINGS_REDIRECT_URI || ''}
                            onChange={(e) => handleChange('WITHINGS_REDIRECT_URI', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('WITHINGS_REDIRECT_URI')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                            <Save className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                <div className="pt-4 border-t border-mainframe-border/50">
                    <button
                        onClick={handleConnect}
                        className="w-full py-3 bg-pink-500/10 border border-pink-500/50 text-pink-400 rounded hover:bg-pink-500/20 flex items-center justify-center gap-2 font-bold uppercase tracking-widest"
                    >
                        <Link className="w-4 h-4" />
                        Connect Withings
                    </button>
                    <p className="text-xs text-center mt-2 text-mainframe-text/40">
                        Redirects to Withings login.
                    </p>
                </div>
            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Withings Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To connect Withings, you need to create a developer application.</p>
                            <ol className="list-decimal pl-5 space-y-2">
                                <li>Go to <a href="https://developer.withings.com/developer-dashboard/" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">Developer Dashboard</a> to register an app.</li>
                                <li>Set <b>Callback URL</b> to your server's domain/IP or localhost.</li>
                                <li>Copy the <b>Client ID</b> and <b>Consumer Secret (Client Secret)</b> into the fields behind this window.</li>
                                <li>Click <b>Connect Withings</b> to authorize.</li>
                            </ol>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WithingsSettings;
