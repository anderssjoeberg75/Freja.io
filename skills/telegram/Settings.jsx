import React, { useState, useEffect } from 'react';
import { Save, Loader2, Send, MessageSquare, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const TelegramSettings = () => {
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
                    <Send className="w-8 h-8 text-blue-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Telegram Integration
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
                <p className="text-sm text-mainframe-text/70 mb-4">
                    Telegram integration allows the system to send you proactive notifications and morning briefings.
                </p>

                {/* Bot Token */}
                <SettingsField
                    label="Bot Token"
                    value={settings.TELEGRAM_BOT_TOKEN}
                    onChange={(val) => handleChange('TELEGRAM_BOT_TOKEN', val)}
                    onSave={() => handleSave('TELEGRAM_BOT_TOKEN')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.TELEGRAM_BOT_TOKEN}
                    placeholder="Enter Bot Token"
                    saving={saving}
                />

                {/* Chat ID */}
                <SettingsField
                    label="Chat ID"
                    value={settings.TELEGRAM_CHAT_ID}
                    onChange={(val) => handleChange('TELEGRAM_CHAT_ID', val)}
                    onSave={() => handleSave('TELEGRAM_CHAT_ID')}
                    placeholder="Enter Chat ID"
                    description="Use a bot like @userinfobot to find your Chat ID."
                    saving={saving}
                />
            </div>

            <div className="mt-8 p-4 bg-zinc-900/30 border border-mainframe-border/50 rounded-lg flex items-center gap-4">
                <MessageSquare className="w-5 h-5 text-mainframe-dim opacity-50" />
                <div className="text-xs text-mainframe-text/40">
                    Proactive messages are sent when certain triggers are met (e.g. morning reports, security alerts).
                </div>
            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Telegram Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To connect Telegram so Freja can send you messages, you need to create your own bot and find your Chat ID.</p>

                            <div>
                                <h3 className="text-lg font-bold text-blue-400 mb-2">Step 1: Get Bot Token</h3>
                                <ol className="list-decimal pl-5 space-y-2">
                                    <li>Open Telegram and search for <b>@BotFather</b> (the official bot with a blue verified tick).</li>
                                    <li>Send the command <code>/newbot</code> and follow the instructions to name your bot.</li>
                                    <li>When finished, BotFather will give you a <b>HTTP API Token</b>. Copy this and paste it into the <b>Bot Token</b> field.</li>
                                </ol>
                            </div>

                            <div className="mt-6">
                                <h3 className="text-lg font-bold text-blue-400 mb-2">Step 2: Get Chat ID</h3>
                                <ol className="list-decimal pl-5 space-y-2">
                                    <li>Search for your newly created bot in Telegram and send it a message (e.g. "Hello"). <i>This is required to initiate the chat.</i></li>
                                    <li>Search for <b>@userinfobot</b> in Telegram and start a chat with it.</li>
                                    <li>It will reply with your <b>Id</b> (a string of numbers). Copy this and paste it into the <b>Chat ID</b> field.</li>
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

export default TelegramSettings;
