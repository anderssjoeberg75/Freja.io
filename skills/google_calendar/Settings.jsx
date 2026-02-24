import React, { useState, useEffect } from 'react';
import { Save, Loader2, Calendar, Info, Link, AlertTriangle } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';

const GoogleCalendarSettings = () => {
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
                    <Calendar className="w-8 h-8 text-blue-500" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Google Calendar
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

                {/* Credentials JSON */}
                <div className="grid gap-2">
                    <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">OAuth 2.0 Client credentials (JSON)</label>
                    <p className="text-xs text-mainframe-text/40 italic">Paste the entire content of the <code>credentials.json</code> file downloaded from Google Cloud here.</p>
                    <div className="flex flex-col gap-2">
                        <textarea
                            value={settings.GOOGLE_CALENDAR_CREDENTIALS || ''}
                            onChange={(e) => handleChange('GOOGLE_CALENDAR_CREDENTIALS', e.target.value)}
                            className="w-full bg-black/40 border border-mainframe-border rounded px-4 py-2 font-mono text-sm h-48"
                            placeholder='{"web":{"client_id":"...","project_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_secret":"..."}}'
                        />
                        <button onClick={() => handleSave('GOOGLE_CALENDAR_CREDENTIALS')} disabled={saving} className="self-end px-6 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 flex items-center gap-2">
                            {saving ? <Loader2 className="animate-spin w-4 h-4" /> : <Save className="w-4 h-4" />}
                            Save Credentials
                        </button>
                    </div>
                </div>

                {/* Setup Tool Alert */}
                <div className="mt-8 p-4 border border-blue-500/30 bg-blue-500/10 rounded-lg text-blue-200 text-sm">
                    <AlertTriangle className="w-5 h-5 inline mr-2" />
                    <strong>Important:</strong> After saving your credentials here, you must run <code>python3 skills/google_calendar/setup_auth.py</code> in the terminal on the server to complete the initial Google login flow.
                </div>

            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Google Calendar Setup</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>To let Freja manage your calendar, you need to create OAuth 2.0 Desktop credentials in Google Cloud.</p>
                            <ol className="list-decimal pl-5 space-y-2">
                                <li>Go to the <a href="https://console.cloud.google.com/" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">Google Cloud Console</a>.</li>
                                <li>Create a new Project (or select an existing one).</li>
                                <li>Enable the <b>Google Calendar API</b> for your project.</li>
                                <li>Configure the OAuth Consent Screen (External, add yourself as Test User if not verified).</li>
                                <li>Go to <b>Credentials</b> {'>'} Create Credentials {'>'} <b>OAuth client ID</b>.</li>
                                <li>Choose <b>Desktop app</b> as the Application Type.</li>
                                <li>Download the JSON file, open it in a text editor, copy everything, and paste it into the field behind this window.</li>
                            </ol>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GoogleCalendarSettings;
