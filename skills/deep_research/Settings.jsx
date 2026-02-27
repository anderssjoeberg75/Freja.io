import React, { useState, useEffect } from 'react';
import { Save, Loader2, Globe, AlertTriangle } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const DeepResearchSettings = () => {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const res = await adminFetch('/api/settings');
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

                {/* Web Agent Model */}
                <SettingsField
                    label="Web Agent Model"
                    value={settings.WEB_AGENT_MODEL}
                    onChange={(val) => handleChange('WEB_AGENT_MODEL', val)}
                    onSave={() => handleSave('WEB_AGENT_MODEL')}
                    placeholder="gemini-2.0-flash-exp"
                    description='Recommended: Models with "computer-use" or "thinking" capabilities.'
                    saving={saving}
                />
            </div>

            <div className="mt-8 p-4 bg-yellow-900/10 border border-yellow-700/30 rounded text-yellow-500/80 text-sm flex gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>The Web Agent requires <code>playwright</code> to be installed on the system. It uses a headless browser to perform tasks.</p>
            </div>
        </div>
    );
};

export default DeepResearchSettings;
