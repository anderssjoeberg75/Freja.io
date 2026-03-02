import React, { useState, useEffect } from 'react';
import { User, Save, Loader2, Database, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const UserProfileSettings = () => {
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
                    <User className="w-8 h-8 text-pink-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        User Persona & Identity
                    </h1>
                </div>
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
                        label={
                            <span className="flex items-center gap-2">
                                Mem0 API Key
                                <button
                                    type="button"
                                    onClick={(e) => { e.preventDefault(); setShowHelp(true); }}
                                    className="text-mainframe-text/60 hover:text-mainframe-accent transition-colors"
                                    title="Show Mem0 Setup Instructions"
                                >
                                    <Info className="w-4 h-4 cursor-pointer" />
                                </button>
                            </span>
                        }
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

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Mem0 API Setup</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To enable long-term personalized memory for Freja, you need a Mem0 API key.</p>

                            <div>
                                <h3 className="text-lg font-bold text-pink-400 mb-2">Step-by-step:</h3>
                                <ol className="list-decimal pl-5 space-y-2">
                                    <li>Navigate to <a href="https://app.mem0.ai/dashboard/api-keys" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">app.mem0.ai/dashboard</a> and create an account if you don't have one.</li>
                                    <li>Go to the <b>API Keys</b> section.</li>
                                    <li>Click <b>Create API Key</b> and give it a name like "Freja".</li>
                                    <li>Copy the generated key (it usually starts with <code>m0-</code>).</li>
                                    <li>Paste the key into the <b>Mem0 API Key</b> field behind this window and click Save.</li>
                                </ol>
                            </div>

                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserProfileSettings;
