import React, { useState, useEffect } from 'react';
import { FileText, Save, Loader2, Globe } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import { formatModelOption } from '../../client/src/utils/modelDescriptions';

const WordPressSettings = () => {
    const [settings, setSettings] = useState({});
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState({});
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [settingsRes, modelsRes] = await Promise.all([
                adminFetch('/api/settings'),
                adminFetch('/api/models')
            ]);
            const settingsData = await settingsRes.json();
            const modelsData = await modelsRes.json();

            const availableModels = modelsData.models || [];
            setModels(availableModels);
            setSettings(settingsData || {});
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to load settings.' });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleModelChange = async (val) => {
        handleChange('WORDPRESS_LLM_MODEL', val);
        setSaving(prev => ({ ...prev, ['WORDPRESS_LLM_MODEL']: true }));
        setMessage(null);
        try {
            const res = await adminFetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'WORDPRESS_LLM_MODEL', value: val })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Model updated to ${val || 'system default'}.` });
            } else {
                setMessage({ type: 'error', text: 'Could not save model.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving.' });
        } finally {
            setSaving(prev => ({ ...prev, ['WORDPRESS_LLM_MODEL']: false }));
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleSave = async (key) => {
        setSaving(prev => ({ ...prev, [key]: true }));
        setMessage(null);
        try {
            const res = await adminFetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value: settings[key] })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Saved ${key.replace('WORDPRESS_', '')} successfully!` });
            } else {
                setMessage({ type: 'error', text: 'Could not save setting.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'An error occurred during save.' });
        } finally {
            setSaving(prev => ({ ...prev, [key]: false }));
            setTimeout(() => setMessage(null), 3000);
        }
    };

    if (loading) return <div className="p-8"><Loader2 className="animate-spin text-mainframe-text/50" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Globe className="w-8 h-8 text-blue-500" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    WordPress
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="flex items-start gap-4 p-4 bg-blue-900/10 border border-blue-900/30 rounded-lg mb-6">
                    <FileText className="w-6 h-6 text-blue-400 shrink-0 mt-1" />
                    <div>
                        <h2 className="text-xl font-bold text-blue-400 mb-2 font-orbitron">BLOG PUBLISHING</h2>
                        <p className="text-sm text-mainframe-text/80 leading-relaxed">
                            Configure your WordPress site credentials below. These are stored securely in your system vault and are used to completely automate draft and post publishing from Freja.
                        </p>
                    </div>
                </div>

                <div className="py-2 border-t border-b border-mainframe-border/30 space-y-6">
                    <div className="grid gap-2 my-4">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            WordPress Base URL
                        </label>
                        <div className="flex gap-2 w-full max-w-2xl">
                            <input
                                type="text"
                                placeholder="https://din-domän.se"
                                value={settings.WORDPRESS_BASE_URL || ''}
                                onChange={(e) => handleChange('WORDPRESS_BASE_URL', e.target.value)}
                                className="flex-1 min-w-0 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                            />
                            <button
                                onClick={() => handleSave('WORDPRESS_BASE_URL')}
                                disabled={saving['WORDPRESS_BASE_URL']}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving['WORDPRESS_BASE_URL'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            The full URL to your WordPress installation, without the trailing slash (e.g. `https://myblog.com`). This is used for REST API calls.
                        </p>
                    </div>

                    <div className="grid gap-2 my-4 pt-4 border-t border-mainframe-border/20">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            WordPress Username
                        </label>
                        <div className="flex gap-2 w-full max-w-2xl">
                            <input
                                type="text"
                                placeholder="e.g. admin"
                                value={settings.WORDPRESS_USERNAME || ''}
                                onChange={(e) => handleChange('WORDPRESS_USERNAME', e.target.value)}
                                className="flex-1 min-w-0 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                            />
                            <button
                                onClick={() => handleSave('WORDPRESS_USERNAME')}
                                disabled={saving['WORDPRESS_USERNAME']}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving['WORDPRESS_USERNAME'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Your login username for WordPress.
                        </p>
                    </div>
                        
                    <div className="grid gap-2 my-4 pt-4 border-t border-mainframe-border/20">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            WordPress App Password
                        </label>
                        <div className="flex gap-2 w-full max-w-2xl">
                            <input
                                type="password"
                                placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                                value={settings.WORDPRESS_APP_PASSWORD || ''}
                                onChange={(e) => handleChange('WORDPRESS_APP_PASSWORD', e.target.value)}
                                className="flex-1 min-w-0 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                            />
                            <button
                                onClick={() => handleSave('WORDPRESS_APP_PASSWORD')}
                                disabled={saving['WORDPRESS_APP_PASSWORD']}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving['WORDPRESS_APP_PASSWORD'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Generate this in your WordPress profile under "Application Passwords". It's required for REST API authentication and is stored securely in the local Vault.
                        </p>
                    </div>
                </div>

                <div className="py-2 border-t border-b border-mainframe-border/30 space-y-6">
                    <div className="grid gap-2 my-4">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            WordPress SSH Target (Automation)
                        </label>
                        <div className="flex gap-2 w-full max-w-2xl">
                            <input
                                type="text"
                                placeholder="root@192.168.101.104"
                                value={settings.WORDPRESS_SSH_TARGET || ''}
                                onChange={(e) => handleChange('WORDPRESS_SSH_TARGET', e.target.value)}
                                className="flex-1 min-w-0 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                            />
                            <button
                                onClick={() => handleSave('WORDPRESS_SSH_TARGET')}
                                disabled={saving['WORDPRESS_SSH_TARGET']}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving['WORDPRESS_SSH_TARGET'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Optional: The SSH user and host used for automated site management (WP-CLI).
                        </p>
                    </div>

                    <div className="grid gap-2 my-4 pt-4 border-t border-mainframe-border/20">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            WordPress Document Root
                        </label>
                        <div className="flex gap-2 w-full max-w-2xl">
                            <input
                                type="text"
                                placeholder="/var/www/html/wordpress"
                                value={settings.WORDPRESS_DOC_ROOT || ''}
                                onChange={(e) => handleChange('WORDPRESS_DOC_ROOT', e.target.value)}
                                className="flex-1 min-w-0 bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                            />
                            <button
                                onClick={() => handleSave('WORDPRESS_DOC_ROOT')}
                                disabled={saving['WORDPRESS_DOC_ROOT']}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving['WORDPRESS_DOC_ROOT'] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Optional: The absolute server path of the WordPress installation for WP-CLI.
                        </p>
                    </div>
                    <div className="grid gap-2 my-4 pt-4 border-t border-mainframe-border/20">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            Dedicated AI Model (Optional)
                            {saving['WORDPRESS_LLM_MODEL'] && <Loader2 className="w-3 h-3 animate-spin text-mainframe-accent" />}
                        </label>
                        <select
                            value={settings.WORDPRESS_LLM_MODEL || ''}
                            onChange={(e) => handleModelChange(e.target.value)}
                            disabled={saving['WORDPRESS_LLM_MODEL']}
                            className="w-full bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                        >
                            <option value="">Use system default model</option>
                            {models.map((opt) => (
                                <option key={opt} value={opt}>{formatModelOption(opt)}</option>
                            ))}
                        </select>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            If specified, all WordPress-related chats will automatically route to this model (e.g. gemini-2.5-flash) instead of the global default, ensuring highest reliability for WP-CLI actions.
                        </p>
                    </div>

                </div>

            </div>
        </div>
    );
};

export default WordPressSettings;
