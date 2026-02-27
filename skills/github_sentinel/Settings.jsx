import React, { useState, useEffect } from 'react';
import { Save, Loader2, Github, AlertTriangle } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const GitHubSettings = () => {
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
                <Github className="w-8 h-8 text-github-text" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    GitHub Sentinel
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <p className="text-sm text-mainframe-text/70 mb-4">
                    GitHub Sentinel monitors your notifications and allows you to interact with issues and repositories.
                </p>

                {/* GitHub Token */}
                <SettingsField
                    label="GitHub Personal Access Token"
                    value={settings.GITHUB_TOKEN}
                    onChange={(val) => handleChange('GITHUB_TOKEN', val)}
                    onSave={() => handleSave('GITHUB_TOKEN')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.GITHUB_TOKEN}
                    placeholder="Enter token"
                    description="Create a classic PAT with repo and notifications scopes."
                    saving={saving}
                />
            </div>

            <div className="mt-8 p-4 bg-blue-900/10 border border-blue-700/30 rounded text-blue-400/80 text-sm flex gap-3">
                <AlertTriangle className="w-5 h-5 shrink-0 text-blue-500" />
                <div>
                    <h3 className="font-bold text-blue-400">Available Tools:</h3>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                        <li><code>github_list_issues</code>: List issues assigned to you.</li>
                        <li><code>github_create_issue</code>: Create a new issue in a repo.</li>
                        <li><code>github_check_notifications</code>: Check unread notifications.</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default GitHubSettings;
