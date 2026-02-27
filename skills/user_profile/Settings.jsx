import React, { useState, useEffect } from 'react';
import { User, Save, Loader2, Database, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const UserProfileSettings = () => {
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
                <User className="w-8 h-8 text-pink-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    User Persona & Identity
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <SettingsField
                        label="Preferred Name"
                        value={settings.USER_NAME}
                        onChange={(val) => handleChange('USER_NAME', val)}
                        onSave={() => handleSave('USER_NAME')}
                        description="How the system should address you."
                        saving={saving}
                    />
                    <SettingsField
                        label="Instance Personality"
                        value={settings.APP_NAME}
                        onChange={(val) => handleChange('APP_NAME', val)}
                        onSave={() => handleSave('APP_NAME')}
                        description="The name of your personal AI assistant."
                        saving={saving}
                    />
                </div>

                <div className="pt-6 border-t border-mainframe-border/30">
                    <div className="flex items-center gap-3 mb-4 text-mainframe-text/80">
                        <Database className="w-5 h-5 text-pink-400" />
                        <h3 className="font-bold uppercase tracking-widest text-sm">Conversational Memory (Mem0)</h3>
                    </div>

                    <SettingsField
                        label="Mem0 API Key"
                        value={settings.MEM0_API_KEY}
                        onChange={(val) => handleChange('MEM0_API_KEY', val)}
                        onSave={() => handleSave('MEM0_API_KEY')}
                        type="password"
                        secretConfigured={settings.__secrets && settings.__secrets.MEM0_API_KEY}
                        placeholder="Enter Mem0 key"
                        saving={saving}
                    />
                </div>
            </div>

            <div className="mt-8 p-4 bg-zinc-900/30 border border-mainframe-border/50 rounded-lg flex items-center gap-4">
                <Info className="w-5 h-5 text-mainframe-dim opacity-50" />
                <div className="text-xs text-mainframe-text/40">
                    Personalization data helps the AI understand your preferences and daily routine over time.
                </div>
            </div>
        </div>
    );
};

export default UserProfileSettings;
