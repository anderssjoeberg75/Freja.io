import React, { useState, useEffect } from 'react';
import { Save, Loader2, Home } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const HASettings = () => {
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
                <Home className="w-8 h-8 text-cyan-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Home Assistant
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">

                {/* HA URL */}
                <SettingsField
                    label="Server URL"
                    value={settings.HA_URL}
                    onChange={(val) => handleChange('HA_URL', val)}
                    onSave={() => handleSave('HA_URL')}
                    placeholder="http://homeassistant.local:8123"
                    saving={saving}
                />

                {/* HA Token */}
                <SettingsField
                    label="Long-Lived Access Token"
                    value={settings.HA_TOKEN}
                    onChange={(val) => handleChange('HA_TOKEN', val)}
                    onSave={() => handleSave('HA_TOKEN')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.HA_TOKEN}
                    placeholder="Long token from HA Profile..."
                    saving={saving}
                />
            </div>
        </div>
    );
};

export default HASettings;
