import React, { useState, useEffect } from 'react';
import { Save, Loader2, Activity, Info, Link, AlertTriangle } from 'lucide-react';

const StravaSettings = () => {
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

    if (loading) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center justify-between mb-8 border-b border-mainframe-border pb-4">
                <div className="flex items-center gap-4">
                    <Activity className="w-8 h-8 text-orange-500" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Strava Integration
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
                            value={settings.STRAVA_CLIENT_ID || ''}
                            onChange={(e) => handleChange('STRAVA_CLIENT_ID', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('STRAVA_CLIENT_ID')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
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
                            value={settings.STRAVA_CLIENT_SECRET || ''}
                            onChange={(e) => handleChange('STRAVA_CLIENT_SECRET', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('STRAVA_CLIENT_SECRET')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
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
                            value={settings.STRAVA_REDIRECT_URI || ''}
                            onChange={(e) => handleChange('STRAVA_REDIRECT_URI', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('STRAVA_REDIRECT_URI')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                            <Save className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Authorization Helper */}
                {settings.STRAVA_CLIENT_ID ? (
                    <div className="mt-8 p-4 border border-green-500/30 bg-green-500/10 rounded-lg">
                        <h3 className="text-lg font-bold text-green-400 mb-2">Step 2: Initialize Authorization</h3>
                        <p className="text-sm mb-4">Click the button below to authorize this app to read your workouts (requires activity:read_all scope).</p>
                        <a
                            href={`https://www.strava.com/oauth/authorize?client_id=${settings.STRAVA_CLIENT_ID}&response_type=code&redirect_uri=${encodeURIComponent(window.location.origin + '/api/integrations/strava/callback')}&approval_prompt=force&scope=activity:read_all,profile:read_all&state=Anders`}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 text-white font-bold rounded hover:bg-orange-600 transition-colors"
                        >
                            <Link className="w-5 h-5" />
                            Authorize with Strava
                        </a>
                    </div>
                ) : (
                    <div className="mt-8 p-4 border border-orange-500/30 bg-orange-500/10 rounded-lg text-orange-200 text-sm">
                        <AlertTriangle className="w-5 h-5 inline mr-2" />
                        Save your Client ID first to generate the mandatory Authorization Link.
                    </div>
                )}
            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Strava Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To connect Strava, you need to create an API Application and authorize it.</p>
                            <ol className="list-decimal pl-5 space-y-2">
                                <li>Go to <a href="https://www.strava.com/settings/api" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">strava.com/settings/api</a></li>
                                <li>Create an app. Category: "Performance Analysis" is fine.</li>
                                <li>Set <b>Authorization Callback Domain</b> to <code>localhost</code> (or your server domain).</li>
                                <li>Copy the <b>Client ID</b> and <b>Client Secret</b> into the settings behind this window and save them.</li>
                                <li>Set Redirect URI to match your domain (e.g. <code>http://localhost</code>).</li>
                            </ol>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StravaSettings;
