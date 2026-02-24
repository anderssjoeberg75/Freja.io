import React, { useState, useEffect } from 'react';
import { Info, Loader2 } from 'lucide-react';
import HaAliasManager from './HaAliasManager';
import { adminFetch } from '../utils/adminFetch';

const AliasView = () => {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await adminFetch('/api/settings');
            if (!res.ok) {
                throw new Error("Admin token required.");
            }
            const data = await res.json();
            setSettings(data);
        } catch (err) {
            console.error("Failed to fetch settings:", err);
            setMessage({ type: 'error', text: 'Failed to load aliases.' });
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
            const res = await adminFetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value: valueToSave })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Aliases updated successfully!` });
                setTimeout(() => setMessage(null), 3000);
            } else {
                setMessage({ type: 'error', text: 'Failed to save aliases.' });
            }
        } catch (err) {
            console.error("Save error:", err);
            setMessage({ type: 'error', text: 'Error saving aliases.' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full text-mainframe-text">
            <Loader2 className="animate-spin mr-2" /> Loading Aliases...
        </div>
    );

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
            <h1 className="text-3xl font-orbitron mb-8 text-mainframe-accent border-b border-mainframe-border pb-4">
                Home Assistant Aliases
            </h1>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border">
                <div className="flex items-center gap-3 mb-6 text-xl text-mainframe-text/90 pb-2 border-b border-mainframe-border/50">
                    <Info className="text-blue-400" />
                    <h2>Manage Mappings</h2>
                </div>

                <HaAliasManager
                    settings={settings}
                    handleChange={handleChange}
                    handleSave={handleSave}
                    saving={saving}
                />
            </div>
        </div>
    );
};

export default AliasView;
