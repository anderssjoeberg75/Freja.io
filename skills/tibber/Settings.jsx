import React, { useState, useEffect } from 'react';
import { Save, Loader2, Zap, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';

const TibberSettings = () => {
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
                    <Zap className="w-8 h-8 text-yellow-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Tibber Energy
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

                {/* API Token */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">Tibber API Token</label>
                    <div className="flex gap-2">
                        <input
                            type="password"
                            value={settings.TIBBER_API_TOKEN || ''}
                            onChange={(e) => handleChange('TIBBER_API_TOKEN', e.target.value)}
                            className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2"
                            placeholder="Enter your Personal Access Token"
                        />
                        <button onClick={() => handleSave('TIBBER_API_TOKEN')} disabled={saving} className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 flex items-center gap-2">
                            {saving ? <Loader2 className="animate-spin w-4 h-4" /> : <Save className="w-4 h-4" />}
                            Save
                        </button>
                    </div>
                    <p className="text-xs text-mainframe-text/40 italic mt-1">This token allows Freja to read your hourly electricity consumption and prices.</p>
                </div>

            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Tibber Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To connect your Tibber account, you need to generate a Personal Access Token.</p>
                            <ol className="list-decimal pl-5 space-y-2">
                                <li>Got to the <a href="https://developer.tibber.com/" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">Tibber Developer Portal</a>.</li>
                                <li>Sign in with your Tibber app account.</li>
                                <li>Once logged in, click on your profile/account name in the top right and navigate to <b>Personal Access Token</b>.</li>
                                <li>Copy the token provided on the screen.</li>
                                <li>Paste the token into the <b>Tibber API Token</b> field behind this window and click Save.</li>
                            </ol>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TibberSettings;
