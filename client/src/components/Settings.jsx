import React, { useState, useEffect } from 'react';
import { Save, Bot, Loader2, Activity, Info, AlertTriangle, ChevronRight } from 'lucide-react';
import HaAliasManager from './HaAliasManager';

const Settings = () => {
    const [settings, setSettings] = useState({});
    const [schema, setSchema] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [showStravaHelp, setShowStravaHelp] = useState(false);
    const [models, setModels] = useState([]);

    useEffect(() => {
        fetchInitialData();
    }, []);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [settingsRes, schemaRes, modelsRes] = await Promise.all([
                fetch('/api/settings'),
                fetch('/api/settings/schema'),
                fetch('/api/models')
            ]);

            // Check responses before parsing
            if (!settingsRes.ok || !schemaRes.ok) {
                console.error("API Error statuses:", settingsRes.status, schemaRes.status);
            }

            const settingsData = await settingsRes.json();
            const schemaData = await schemaRes.json();
            const modelsData = await modelsRes.json();

            setSettings(settingsData || {});
            setSchema(Array.isArray(schemaData) ? schemaData : []);
            setModels(modelsData.models || []);

            if (!Array.isArray(schemaData)) {
                setMessage({ type: 'error', text: 'Läser in felaktigt format från servern. Starta om backend-tjänsten.' });
            }
        } catch (err) {
            console.error("Failed to fetch settings data:", err);
            setMessage({
                type: 'error',
                text: `Kunde inte ladda inställningar: ${err.message}. Kontrollera att backend körs.`
            });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleSave = async (key, directValue = null) => {
        setSaving(true);
        setMessage(null);
        const valueToSave = directValue !== null ? directValue : settings[key];
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value: valueToSave })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Saved ${key} successfully!` });
            } else {
                setMessage({ type: 'error', text: 'Failed to save setting.' });
            }
        } catch (err) {
            console.error("Save error:", err);
            setMessage({ type: 'error', text: 'Error saving setting.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleAction = async (item) => {
        if (item.key === 'GARMIN_RECONNECT') {
            setSaving(true);
            try {
                const res = await fetch('/api/integrations/garmin/reconnect', { method: 'POST' });
                const data = await res.json();
                setMessage({ type: data.success ? 'success' : 'error', text: data.message });
            } catch (err) {
                setMessage({ type: 'error', text: 'Network error during Garmin reconnect.' });
            } finally {
                setSaving(false);
                setTimeout(() => setMessage(null), 5000);
            }
        } else if (item.key === 'WITHINGS_CONNECT') {
            const clientId = settings.WITHINGS_CLIENT_ID;
            const redirectUri = settings.WITHINGS_REDIRECT_URI;
            if (!clientId || !redirectUri) {
                setMessage({ type: 'error', text: 'Please enter Client ID and Redirect URI first.' });
                return;
            }
            const url = `https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=${clientId}&state=freja&scope=user.metrics,user.activity&redirect_uri=${encodeURIComponent(redirectUri)}`;
            window.open(url, '_blank');
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full text-mainframe-text">
            <Loader2 className="animate-spin mr-2" /> Loading Configuration...
        </div>
    );

    // Group schema into sections
    const sections = schema.reduce((acc, item) => {
        if (!acc[item.section]) acc[item.section] = [];
        acc[item.section].push(item);
        return acc;
    }, {});

    const getSectionIcon = (name) => {
        switch (name) {
            case 'Identity': return <Bot className="w-5 h-5 text-purple-400" />;
            case 'Intelligence': return <Activity className="w-5 h-5 text-green-400" />;
            case 'Weather & Location': return <Bot className="w-5 h-5 text-yellow-400" />;
            default: return <Activity className="w-5 h-5 text-blue-400" />;
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
            <h1 className="text-3xl font-orbitron mb-8 text-mainframe-accent border-b border-mainframe-border pb-4">
                System Configuration
            </h1>

            {message && (
                <div className={`mb-6 p-4 rounded border transition-all ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid gap-10">
                {Object.entries(sections).map(([sectionName, items]) => (
                    <div key={sectionName} className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl">
                        <div className="flex items-center gap-3 mb-8 text-xl text-mainframe-text/90 pb-3 border-b border-mainframe-border/50">
                            {getSectionIcon(sectionName)}
                            <h2 className="font-orbitron tracking-wider">{sectionName.toUpperCase()}</h2>
                        </div>

                        <div className="grid gap-8">
                            {items.map((item) => (
                                <div key={item.key} className="grid gap-2">
                                    <div className="flex items-center gap-2">
                                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight">
                                            {item.label}
                                        </label>
                                        {(item.key.startsWith('STRAVA') || item.key.startsWith('WITHINGS')) && (
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    if (item.key.startsWith('STRAVA')) setShowStravaHelp(true);
                                                    else setMessage({ type: 'info', text: 'Se manualen för Withings under Strava-hjälpen.' });
                                                }}
                                                className="text-mainframe-accent hover:text-white transition-colors"
                                            >
                                                <Info className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                    <div className="flex gap-2">
                                        {item.type === 'select' ? (
                                            <select
                                                value={settings[item.key] || ''}
                                                onChange={(e) => handleChange(item.key, e.target.value)}
                                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                                            >
                                                <option value="" disabled>Select model...</option>
                                                {(item.options || models).map((opt) => (
                                                    <option key={opt} value={opt}>{opt}</option>
                                                ))}
                                            </select>
                                        ) : item.type === 'action' ? (
                                            <button
                                                onClick={() => handleAction(item)}
                                                disabled={saving}
                                                className="flex-1 px-4 py-2.5 bg-mainframe-accent/5 border border-mainframe-accent/40 text-mainframe-accent hover:bg-mainframe-accent/20 rounded transition-all flex items-center justify-center font-bold text-sm tracking-widest uppercase gap-2 group"
                                            >
                                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
                                                {item.actionLabel}
                                            </button>
                                        ) : (
                                            <input
                                                type={item.type}
                                                value={settings[item.key] || ''}
                                                onChange={(e) => handleChange(item.key, e.target.value)}
                                                placeholder={item.description || `Enter ${item.label}`}
                                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                                            />
                                        )}

                                        {item.type !== 'action' && (
                                            <button
                                                onClick={() => handleSave(item.key)}
                                                disabled={saving}
                                                className="px-5 py-2.5 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/30 hover:border-mainframe-accent rounded transition-all flex items-center shadow-lg"
                                            >
                                                {saving ? <Loader2 className="w-4 h-5 animate-spin" /> : <Save className="w-4 h-5" />}
                                            </button>
                                        )}
                                    </div>
                                    {item.description && <p className="text-xs text-zinc-500 italic mt-1">{item.description}</p>}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-12 p-5 bg-yellow-900/10 border border-yellow-700/30 rounded-lg text-yellow-500/80 text-sm flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 shrink-0" />
                <div>
                    <strong className="block mb-1 text-yellow-500 uppercase tracking-tighter">Security Notice</strong>
                    <p>Configuration and sensitive keys are stored in a local SQLite database. Ensure environment and physical access is restricted.</p>
                </div>
            </div>

            {/* Strava Help Modal */}
            {showStravaHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowStravaHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Integration Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <section>
                                <h3 className="font-bold text-lg text-mainframe-accent/80 mb-2">1. Strava API</h3>
                                <p className="text-sm">Create app at <a href="https://www.strava.com/settings/api" target="_blank" className="text-mainframe-accent underline">strava.com/settings/api</a>. Use <code>localhost</code> as authorization domain.</p>
                            </section>
                            <section>
                                <h3 className="font-bold text-lg text-mainframe-accent/80 mb-2">2. Withings API</h3>
                                <p className="text-sm">Create account at <a href="https://developer.withings.com/" target="_blank" className="text-mainframe-accent underline">developer.withings.com</a>. Set callback to <code>http://localhost:8000/api/integrations/withings/callback</code>.</p>
                            </section>
                        </div>
                        <button onClick={() => setShowStravaHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
