import React, { useState, useEffect } from 'react';
import { Save, Loader2, Send, MessageSquare } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const TelegramSettings = () => {
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
                <Send className="w-8 h-8 text-blue-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Telegram Integration
                </h1>
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
        </div>
    );
};

export default TelegramSettings;
