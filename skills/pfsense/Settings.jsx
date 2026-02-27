import React, { useState, useEffect } from 'react';
import { Save, Loader2, Wifi, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const PfSenseSettings = () => {
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
            <div className="flex items-center justify-between mb-8 border-b border-mainframe-border pb-4">
                <div className="flex items-center gap-4">
                    <Wifi className="w-8 h-8 text-blue-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        pfSense Firewall
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

                {/* API URL */}
                <SettingsField
                    label="pfSense API URL"
                    value={settings.PFSENSE_API_URL}
                    onChange={(val) => handleChange('PFSENSE_API_URL', val)}
                    onSave={() => handleSave('PFSENSE_API_URL')}
                    placeholder="e.g. https://192.168.1.1"
                    saving={saving}
                />

                {/* API Key */}
                <SettingsField
                    label="pfSense API Key"
                    value={settings.PFSENSE_API_KEY}
                    onChange={(val) => handleChange('PFSENSE_API_KEY', val)}
                    onSave={() => handleSave('PFSENSE_API_KEY')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.PFSENSE_API_KEY}
                    placeholder="username:password or API Token"
                    saving={saving}
                />

                {/* Verify TLS */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Verify TLS Certificate</label>
                    <div className="flex gap-2">
                        <select
                            value={settings.PFSENSE_VERIFY_TLS || 'true'}
                            onChange={(e) => {
                                handleChange('PFSENSE_VERIFY_TLS', e.target.value);
                            }}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text"
                        >
                            <option value="true">Yes (Strict SSL)</option>
                            <option value="false">No (Allow self-signed)</option>
                        </select>
                        <button onClick={() => handleSave('PFSENSE_VERIFY_TLS')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 flex items-center justify-center min-w-[50px]">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        </button>
                    </div>
                    <p className="text-xs text-mainframe-text/40 italic mt-1">Set to "No" if your router uses a self-signed HTTPS certificate.</p>
                </div>

            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">pfSense Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To connect pfSense, Freja requires the `pfrest` API package to be installed on your router.</p>
                            <ol className="list-decimal pl-5 space-y-2">
                                <li>Ensure `pfrest` is running on your pfSense firewall.</li>
                                <li>Enter the router's base URL (e.g., <code>https://192.168.1.1</code>).</li>
                                <li>Generate an API client/token in the pfSense `System → API` settings.</li>
                                <li>Enter the API credentials (often in <code>client_id:client_secret</code> format).</li>
                                <li>If you haven't assigned a valid SSL certificate to pfSense, change <b>Verify TLS Certificate</b> to <b>No</b>.</li>
                            </ol>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PfSenseSettings;
