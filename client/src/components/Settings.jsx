import React, { useState, useEffect } from 'react';
import { Save, Bot, Loader2, ActivityIcon, Info, AlertTriangle } from 'lucide-react';

const Settings = () => {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [showStravaHelp, setShowStravaHelp] = useState(false);
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
                { key: "OPENAI_API_KEY", label: "OpenAI API Key", type: "password", desc: "Optional fallback" },
                { key: "OLLAMA_URL", label: "Ollama URL", type: "text", desc: "e.g. http://localhost:11434" }
            ]
        },
        {
            title: "Integrations",
            icon: <ActivityIcon />,
            items: [
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

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
            <h1 className="text-3xl font-orbitron mb-8 text-mainframe-accent border-b border-mainframe-border pb-4">
                System Configuration
            </h1>

            {message && (
                <div className={`mb - 6 p - 4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'} `}>
                    {message.text}
                </div>
            )}

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
                                        ) : (
                                            <input
                                                type={item.type}
                                                value={settings[item.key] || ''}
                                                onChange={(e) => handleChange(item.key, e.target.value)}
                                                placeholder={item.desc || `Enter ${item.label} `}
                                                className="flex-1 bg-black/30 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none focus:ring-1 focus:ring-mainframe-accent transition-all font-mono text-sm"
                                            />
                                        )}

                                        {item.type !== 'action' && (
                                            <button
                                                onClick={() => handleSave(item.key)}
                                                disabled={saving}
                                                className="px-4 py-2 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/20 rounded transition-colors flex items-center"
                                            >
                                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                            </button>
                                        )}
                                    </div>
                                    {item.desc && <p className="text-xs text-zinc-500">{item.desc}</p>}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-8 p-4 bg-yellow-900/10 border border-yellow-700/30 rounded text-yellow-500/80 text-sm flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>Sensitive keys (Passwords, API Keys) are stored in the local SQLite database. Ensure this server is secured.</p>
            </div>

            {/* Strava Help Modal */}
            {showStravaHelp && (
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
                                    <li><strong>Application Name:</strong> DAA Mainframe</li>
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
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
