import React, { useState, useEffect } from 'react';
import { Save, Loader2, Globe, AlertTriangle } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';
import { formatModelOption } from '../../client/src/utils/modelDescriptions';

const DeepResearchSettings = () => {
    const [settings, setSettings] = useState({});
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [settingsRes, modelsRes] = await Promise.all([
                adminFetch('/api/settings'),
                adminFetch('/api/models')
            ]);
            const settingsData = await settingsRes.json();
            const modelsData = await modelsRes.json();

            const availableModels = modelsData.models || [];
            setModels(availableModels);

            let loadedSettings = settingsData || {};

            // Auto-select the best web agent model if none is configured
            if (!loadedSettings.WEB_AGENT_MODEL) {
                const AGENT_MODEL_PRIORITY = [
                    "gemini-2.5-pro", "gemini-2.0-pro-exp", "o1", "o3-mini",
                    "gemini-2.5-flash", "deepseek-r1", "gpt-4o"
                ];
                let bestModel = "";
                for (const preferred of AGENT_MODEL_PRIORITY) {
                    const match = availableModels.find(m => m.toLowerCase().startsWith(preferred));
                    if (match) {
                        bestModel = match;
                        break;
                    }
                }
                // Fallback to first if no matches
                if (!bestModel && availableModels.length > 0) {
                    bestModel = availableModels[0];
                }
                loadedSettings.WEB_AGENT_MODEL = bestModel;
            }

            setSettings(loadedSettings);
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to load settings.' });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleModelChange = async (val) => {
        handleChange('WEB_AGENT_MODEL', val);
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'WEB_AGENT_MODEL', value: val })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Web Agent model updated to ${val || 'system default'}.` });
            } else {
                setMessage({ type: 'error', text: 'Could not save model.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleSave = async (key) => {
        setSaving(true);
        setMessage(null);
        try {
            const res = await adminFetch('/api/settings', {
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
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Globe className="w-8 h-8 text-blue-500" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Deep Research (Web Agent)
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <p className="text-sm text-mainframe-text/70 mb-4">
                    The Web Agent can navigate the web, research topics, and interact with websites to provide up-to-date information.
                </p>

                {/* SerpAPI Key */}
                <SettingsField
                    label="SerpAPI Key (Search)"
                    value={settings.SERPAPI_API_KEY}
                    onChange={(val) => handleChange('SERPAPI_API_KEY', val)}
                    onSave={() => handleSave('SERPAPI_API_KEY')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.SERPAPI_API_KEY}
                    placeholder="Enter SerpAPI key"
                    saving={saving}
                />

                <div className="py-2 border-t border-b border-mainframe-border/30">
                    <div className="grid gap-2 my-4">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            Web Agent Model
                            {saving && <Loader2 className="w-3 h-3 animate-spin text-mainframe-accent" />}
                        </label>
                        <select
                            value={settings.WEB_AGENT_MODEL || ''}
                            onChange={(e) => handleModelChange(e.target.value)}
                            disabled={saving}
                            className="w-full bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                        >
                            <option value="">Use system default model</option>
                            {models.map((opt) => (
                                <option key={opt} value={opt}>{formatModelOption(opt)}</option>
                            ))}
                        </select>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Recommended: Models with "computer-use" or "thinking" capabilities.
                        </p>
                    </div>
                </div>
            </div>

            <div className="mt-8 p-4 bg-yellow-900/10 border border-yellow-700/30 rounded text-yellow-500/80 text-sm flex gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>The Web Agent requires <code>playwright</code> to be installed on the system. It uses a headless browser to perform tasks.</p>
            </div>
        </div>
    );
};

export default DeepResearchSettings;
