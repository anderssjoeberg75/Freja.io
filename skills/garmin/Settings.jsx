import React, { useState, useEffect } from 'react';
import { Save, Loader2, Activity, AlertTriangle, RefreshCw } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const GarminSettings = () => {
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

    const handleReconnect = async () => {
        setSaving(true);
        try {
            const res = await adminFetch('/api/integrations/garmin/reconnect', { method: 'POST' });
            const data = await res.json();
            setMessage({ type: data.success ? 'success' : 'error', text: data.message });
        } catch (err) {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 5000);
        }
    };

    if (loading) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Activity className="w-8 h-8 text-blue-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Garmin Connect
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <p className="text-sm text-mainframe-text/70 mb-4">
                    Configure your Garmin Connect credentials to sync health data (Steps, Sleep, Body Battery).
                </p>

                {/* Email */}
                <SettingsField
                    label="Email"
                    value={settings.GARMIN_EMAIL}
                    onChange={(val) => handleChange('GARMIN_EMAIL', val)}
                    onSave={() => handleSave('GARMIN_EMAIL')}
                    saving={saving}
                />

                {/* Password */}
                <SettingsField
                    label="Password"
                    value={settings.GARMIN_PASSWORD}
                    onChange={(val) => handleChange('GARMIN_PASSWORD', val)}
                    onSave={() => handleSave('GARMIN_PASSWORD')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.GARMIN_PASSWORD}
                    saving={saving}
                />

                {/* Actions */}
                <div className="pt-4 border-t border-mainframe-border/50">
                    <button
                        onClick={handleReconnect}
                        disabled={saving}
                        className="w-full py-3 bg-blue-500/10 border border-blue-500/50 text-blue-400 rounded hover:bg-blue-500/20 flex items-center justify-center gap-2 font-bold uppercase tracking-widest"
                    >
                        {saving ? <Loader2 className="animate-spin w-4 h-4" /> : <RefreshCw className="w-4 h-4" />}
                        Test Connection / Reconnect
                    </button>
                    <p className="text-xs text-center mt-2 text-mainframe-text/40">
                        Uses cached tokens if available. Forces a new login if tokens are expired.
                    </p>
                </div>
            </div>

            <div className="mt-8 p-4 bg-yellow-900/10 border border-yellow-700/30 rounded text-yellow-500/80 text-sm flex gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>If you have 2FA enabled, you might need to run the `scripts/garmin_login.py` script manually on the server once to generate tokens.</p>
            </div>
        </div>
    );
};

export default GarminSettings;
