import React, { useState, useEffect } from 'react';
<<<<<<< HEAD
import { Save, Bot, Loader2, ActivityIcon, Info, AlertTriangle } from 'lucide-react';

const Settings = () => {
    const [settings, setSettings] = useState({});
=======
import { Save, Bot, Loader2, Activity, Info, AlertTriangle, ChevronRight } from 'lucide-react';
import HaAliasManager from './HaAliasManager';

const Settings = () => {
    const [settings, setSettings] = useState({});
    const [schema, setSchema] = useState([]);
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [showStravaHelp, setShowStravaHelp] = useState(false);
<<<<<<< HEAD
    const [models, setModels] = useState([]); // State for available models

    useEffect(() => {
        fetchSettings();
        fetchModels();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            setSettings(data);
        } catch (err) {
            console.error("Failed to fetch settings:", err);
            setMessage({ type: 'error', text: 'Failed to load settings.' });
        } finally {
            setLoading(false);
        }
    };

    const fetchModels = async () => {
        try {
            const res = await fetch('/api/models');
            if (res.ok) {
                const data = await res.json();
                setModels(data.models || []);
            }
        } catch (err) {
            console.error("Failed to fetch models:", err);
=======
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
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

<<<<<<< HEAD
    const handleSave = async (key) => {
        setSaving(true);
        setMessage(null);
=======
    const handleSave = async (key, directValue = null) => {
        setSaving(true);
        setMessage(null);
        const valueToSave = directValue !== null ? directValue : settings[key];
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
<<<<<<< HEAD
                body: JSON.stringify({ key, value: settings[key] })
=======
                body: JSON.stringify({ key, value: valueToSave })
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
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

<<<<<<< HEAD
    const handleGarminReconnect = async () => {
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch('/api/integrations/garmin/reconnect', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: data.message });
            } else {
                setMessage({ type: 'error', text: data.message });
            }
        } catch (err) {
            console.error("Reconnect error:", err);
            setMessage({ type: 'error', text: 'Network error during reconnect.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 5000);
        }
    };

    if (loading) return <div className="flex items-center justify-center h-full text-mainframe-text"><Loader2 className="animate-spin mr-2" /> Loading Configuration...</div>;

    const sections = [
        {
            title: "AI & Models",
            icon: <Bot className="w-5 h-5 mb-1" />,
            items: [
                {
                    key: "SELECTED_MODEL",
                    label: "Active Model",
                    type: "select",
                    options: models,
                    desc: "Select the AI model to use for Chat & Voice."
                },
                { key: "GOOGLE_API_KEY", label: "Google Gemini API Key", type: "password", desc: "Required for Chat & Voice" },
                { key: "MEM0_API_KEY", label: "Mem0 API Key", type: "password", desc: "Required for Long-Term Memory" },
                { key: "OPENAI_API_KEY", label: "OpenAI API Key", type: "password", desc: "Optional fallback" },
                { key: "OLLAMA_URL", label: "Ollama URL", type: "text", desc: "e.g. http://localhost:11434" }
            ]
        },
        {
            title: "Web Search",
            icon: <Bot className="w-5 h-5 mb-1 text-green-400" />,
            items: [
                {
                    key: "WEB_FALLBACK_PROVIDER",
                    label: "Search Provider",
                    type: "select",
                    options: ["serpapi"],
                    desc: "Using SerpAPI."
                },
                { key: "SERPAPI_API_KEY", label: "SerpAPI Key", type: "password", desc: "Get from serpapi.com" }
            ]
        },
        {
            title: "Weather & Location",
            icon: <Bot className="w-5 h-5 mb-1 text-yellow-400" />,
            items: [
                { key: "LATITUDE", label: "Latitude", type: "text", desc: "e.g. 59.3293 (Decimal)" },
                { key: "LONGITUDE", label: "Longitude", type: "text", desc: "e.g. 18.0686 (Decimal)" }
            ]
        },
        {
            title: "Integrations",
            icon: <ActivityIcon />,
            items: [
                { key: "HA_URL", label: "Home Assistant URL", type: "text", desc: "e.g. http://homeassistant.local:8123" },
                { key: "HA_TOKEN", label: "Home Assistant Token", type: "password", desc: "Long-lived access token from Home Assistant" },
                { key: "ROBOROCK_SECRET_KEY", label: "Roborock Secret Key", type: "password", desc: "Fernet key for encrypted Roborock credentials" },
                { key: "USER_ID", label: "Roborock User ID", type: "text", desc: "Credential partition key for Roborock data (optional override)" },
                { key: "GARMIN_EMAIL", label: "Garmin Email", type: "text" },
                { key: "GARMIN_PASSWORD", label: "Garmin Password", type: "password" },
                {
                    key: "GARMIN_RECONNECT",
                    label: "Garmin Connection",
                    type: "action",
                    actionLabel: "Test / Reconnect",
                    onAction: handleGarminReconnect,
                    desc: "Force reconnect if token is expired."
                },
                { key: "STRAVA_CLIENT_ID", label: "Strava Client ID", type: "text", desc: "From https://www.strava.com/settings/api (Create App)" },
                { key: "STRAVA_CLIENT_SECRET", label: "Strava Client Secret", type: "password", desc: "Client Secret from Strava API" },
                { key: "STRAVA_REFRESH_TOKEN", label: "Strava Refresh Token", type: "password", desc: "OAuth refresh token (see guide)" },
                { key: "TELEGRAM_BOT_TOKEN", label: "Telegram Bot Token", type: "password", desc: "From @BotFather on Telegram" },
                { key: "TELEGRAM_CHAT_ID", label: "Telegram Chat ID", type: "text", desc: "Your chat ID (send /start to bot)" }
            ]
        }
    ];
=======
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
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
            <h1 className="text-3xl font-orbitron mb-8 text-mainframe-accent border-b border-mainframe-border pb-4">
                System Configuration
            </h1>

            {message && (
<<<<<<< HEAD
                <div className={`mb - 6 p - 4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'} `}>
=======
                <div className={`mb-6 p-4 rounded border transition-all ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                    {message.text}
                </div>
            )}

<<<<<<< HEAD
            <div className="grid gap-8">
                {sections.map((section, idx) => (
                    <div key={idx} className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border">
                        <div className="flex items-center gap-3 mb-6 text-xl text-mainframe-text/90 pb-2 border-b border-mainframe-border/50">
                            {section.icon}
                            <h2>{section.title}</h2>
                        </div>

                        <div className="grid gap-6">
                            {section.items.map((item) => (
                                <div key={item.key} className="grid gap-2">
                                    <div className="flex items-center gap-2">
                                        <label className="text-sm font-medium text-mainframe-text/70">
                                            {item.label}
                                        </label>
                                        {item.key.startsWith('STRAVA') && (
                                            <button
                                                type="button"
                                                onClick={() => setShowStravaHelp(true)}
                                                className="text-mainframe-accent hover:text-white transition-colors"
                                                title="How to get Strava credentials"
=======
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
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
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
<<<<<<< HEAD
                                                className="flex-1 bg-black/30 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none focus:ring-1 focus:ring-mainframe-accent transition-all font-mono text-sm appearance-none"
                                            >
                                                <option value="" disabled>Select a model...</option>
                                                {item.options.map((opt) => (
                                                    <option key={opt} value={opt}>
                                                        {opt}
                                                    </option>
                                                ))}
                                            </select>
                                        ) : item.type === 'action' ? (
                                            <div className="flex-1 flex items-center gap-2">
                                                <span className="text-zinc-500 text-sm italic">Click to reconnect -&gt;</span>
                                                <button
                                                    onClick={item.onAction}
                                                    disabled={saving}
                                                    className="px-4 py-2 bg-yellow-600/20 border border-yellow-600/50 text-yellow-500 hover:bg-yellow-600/30 rounded transition-colors flex items-center font-bold text-sm"
                                                >
                                                    {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                                    {item.actionLabel}
                                                </button>
                                            </div>
=======
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
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                                        ) : (
                                            <input
                                                type={item.type}
                                                value={settings[item.key] || ''}
                                                onChange={(e) => handleChange(item.key, e.target.value)}
<<<<<<< HEAD
                                                placeholder={item.desc || `Enter ${item.label} `}
                                                className="flex-1 bg-black/30 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none focus:ring-1 focus:ring-mainframe-accent transition-all font-mono text-sm"
=======
                                                placeholder={item.description || `Enter ${item.label}`}
                                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                                            />
                                        )}

                                        {item.type !== 'action' && (
                                            <button
                                                onClick={() => handleSave(item.key)}
                                                disabled={saving}
<<<<<<< HEAD
                                                className="px-4 py-2 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/20 rounded transition-colors flex items-center"
                                            >
                                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                            </button>
                                        )}
                                    </div>
                                    {item.desc && <p className="text-xs text-zinc-500">{item.desc}</p>}
=======
                                                className="px-5 py-2.5 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/30 hover:border-mainframe-accent rounded transition-all flex items-center shadow-lg"
                                            >
                                                {saving ? <Loader2 className="w-4 h-5 animate-spin" /> : <Save className="w-4 h-5" />}
                                            </button>
                                        )}
                                    </div>
                                    {item.description && <p className="text-xs text-zinc-500 italic mt-1">{item.description}</p>}
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

<<<<<<< HEAD
            <div className="mt-8 p-4 bg-yellow-900/10 border border-yellow-700/30 rounded text-yellow-500/80 text-sm flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>Sensitive keys (Passwords, API Keys) are stored in the local SQLite database. Ensure this server is secured.</p>
=======
            <div className="mt-12 p-5 bg-yellow-900/10 border border-yellow-700/30 rounded-lg text-yellow-500/80 text-sm flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 shrink-0" />
                <div>
                    <strong className="block mb-1 text-yellow-500 uppercase tracking-tighter">Security Notice</strong>
                    <p>Configuration and sensitive keys are stored in a local SQLite database. Ensure environment and physical access is restricted.</p>
                </div>
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
            </div>

            {/* Strava Help Modal */}
            {showStravaHelp && (
<<<<<<< HEAD
                <div
                    className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
                    onClick={() => setShowStravaHelp(false)}
                >
                    <div
                        className="bg-mainframe-bg border-2 border-mainframe-accent rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto m-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h2 className="text-2xl font-orbitron mb-4 text-mainframe-accent">Strava API Setup Guide</h2>

                        <div className="space-y-4 text-mainframe-text">
                            <div>
                                <h3 className="font-bold text-lg mb-2">1. Create Strava API Application</h3>
                                <p className="mb-2">Visit: <a href="https://www.strava.com/settings/api" target="_blank" rel="noopener noreferrer" className="text-mainframe-accent underline hover:text-white">https://www.strava.com/settings/api</a></p>
                                <p className="text-sm text-gray-400">Log in to your Strava account if needed</p>
                            </div>

                            <div>
                                <h3 className="font-bold text-lg mb-2">2. Click "Create App"</h3>
                                <p className="mb-2">Fill in the application form:</p>
                                <ul className="list-disc ml-6 space-y-1 text-sm">
                                    <li><strong>Application Name:</strong> Freja.Io</li>
                                    <li><strong>Category:</strong> Other</li>
                                    <li><strong>Website:</strong> http://192.168.107.17:8000</li>
                                    <li><strong>Authorization Callback Domain:</strong> 192.168.107.17</li>
                                </ul>
                                <p className="mt-2 text-sm text-gray-400">Check "I have read and agree to the API Agreement"</p>
                            </div>

                            <div>
                                <h3 className="font-bold text-lg mb-2">3. Save Your Credentials</h3>
                                <p className="mb-2">After creating the app, you'll see:</p>
                                <ul className="list-disc ml-6 space-y-1 text-sm">
                                    <li><strong>Client ID:</strong> A number (e.g., 123456)</li>
                                    <li><strong>Client Secret:</strong> A long string (click "Show" to reveal)</li>
                                </ul>
                            </div>

                            <div>
                                <h3 className="font-bold text-lg mb-2">4. Enter in Settings</h3>
                                <p className="mb-2">Copy the Client ID and Client Secret to the fields in this Settings page.</p>
                                <p className="text-sm text-yellow-500">Note: Refresh Token requires OAuth flow setup (optional for now)</p>
                            </div>
                        </div>

                        <button
                            onClick={() => setShowStravaHelp(false)}
                            className="mt-6 px-6 py-2 bg-mainframe-accent text-black rounded hover:opacity-80 transition-opacity font-bold"
                        >
                            Close
                        </button>
=======
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
>>>>>>> 331190c (Update: 2026-02-16 17:26:31)
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
