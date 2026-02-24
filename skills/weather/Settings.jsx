import React, { useState, useEffect } from 'react';
import { Save, Loader2, Cloud } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';

const WeatherSettings = () => {
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
                <Cloud className="w-8 h-8 text-gray-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Weather & Location
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="grid grid-cols-2 gap-6">
                    {/* Latitude */}
                    <div className="grid gap-2">
                        <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Latitude</label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="59.3293"
                                value={settings.LATITUDE || ''}
                                onChange={(e) => handleChange('LATITUDE', e.target.value)}
                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                            />
                            <button onClick={() => handleSave('LATITUDE')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                                <Save className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Longitude */}
                    <div className="grid gap-2">
                        <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Longitude</label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="18.0686"
                                value={settings.LONGITUDE || ''}
                                onChange={(e) => handleChange('LONGITUDE', e.target.value)}
                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                            />
                            <button onClick={() => handleSave('LONGITUDE')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                                <Save className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Timezone */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Timezone</label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Europe/Stockholm"
                            value={settings.TIMEZONE || ''}
                            onChange={(e) => handleChange('TIMEZONE', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                        />
                        <button onClick={() => handleSave('TIMEZONE')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30">
                            <Save className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WeatherSettings;
