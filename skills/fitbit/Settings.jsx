import React, { useState, useEffect } from 'react';
import { Save, Loader2, Activity, Info } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import SettingsField from '../../client/src/components/SettingsField';

const FitbitSettings = () => {
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
                if (key !== 'FITBIT_CLIENT_ID') {
                    setSettings(prev => ({
                        ...prev,
                        [key]: '',
                        __secrets: { ...(prev.__secrets || {}), [key]: true }
                    }));
                }
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

    const handleConnect = () => {
        const clientId = settings.FITBIT_CLIENT_ID;
        const redirectUri = settings.FITBIT_REDIRECT_URI;
        if (!clientId || !redirectUri) {
            setMessage({ type: 'error', text: 'Please enter Client ID and Redirect URI first.' });
            return;
        }

        // Sometimes Fitbit's auth endpoint has issues if the redirect_uri is strictly URL encoded depending on the dev portal config.
        // If encodeURIComponent fails, we try sending it directly or ensuring there is no trailing slash mismatch.
        const cleanUri = redirectUri.trim();
        const url = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${clientId}&scope=activity%20heartrate%20sleep%20profile%20weight&redirect_uri=${cleanUri}`;
        window.open(url, '_blank');
    };

    if (loading) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center justify-between mb-8 border-b border-mainframe-border pb-4">
                <div className="flex items-center gap-4">
                    <Activity className="w-8 h-8 text-teal-400" />
                    <h1 className="text-3xl font-orbitron text-mainframe-accent">
                        Fitbit
                    </h1>
                </div>
                <button onClick={() => setShowHelp(true)} className="text-mainframe-text/60 hover:text-mainframe-accent transition-colors">
                    <Info className="w-6 h-6" />
                </button>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border transition-all ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">

                {/* Client ID */}
                <SettingsField
                    label="Client ID"
                    value={settings.FITBIT_CLIENT_ID}
                    onChange={(val) => handleChange('FITBIT_CLIENT_ID', val)}
                    onSave={() => handleSave('FITBIT_CLIENT_ID')}
                    placeholder="e.g. 23B4P5"
                    description="Kopiera 'OAuth 2.0 Client ID' från dev.fitbit.com"
                    saving={saving}
                />

                {/* Client Secret */}
                <SettingsField
                    label="Client Secret"
                    value={settings.FITBIT_CLIENT_SECRET}
                    onChange={(val) => handleChange('FITBIT_CLIENT_SECRET', val)}
                    onSave={() => handleSave('FITBIT_CLIENT_SECRET')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.FITBIT_CLIENT_SECRET}
                    placeholder="Din Client Secret"
                    description="Kopiera 'Client Secret' från dev.fitbit.com"
                    saving={saving}
                />

                {/* Redirect URI */}
                <SettingsField
                    label="Redirect URI (Callback URL)"
                    value={settings.FITBIT_REDIRECT_URI}
                    onChange={(val) => handleChange('FITBIT_REDIRECT_URI', val)}
                    onSave={() => handleSave('FITBIT_REDIRECT_URI')}
                    placeholder="http://DIN_IP:8000/api/integrations/fitbit/callback"
                    description="MÅSTE matcha 'Callback URL' exakt i din Fitbit Developer App."
                    saving={saving}
                />

                <div className="pt-4 border-t border-mainframe-border/50">
                    <button
                        onClick={handleConnect}
                        className="w-full py-3 bg-teal-500/10 border border-teal-500/50 text-teal-400 rounded hover:bg-teal-500/20 flex items-center justify-center gap-2 font-bold uppercase tracking-widest"
                    >
                        <Activity className="w-4 h-4" />
                        Connect Fitbit
                    </button>
                    <p className="text-xs text-center mt-2 text-mainframe-text/40">
                        Redirects to Fitbit login to authorize Freja.
                    </p>
                </div>
            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Fitbit Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>För att Freja ska kunna läsa din hälso- och aktivitetsdata från Fitbit måste du skapa en utvecklarapp kopplad till ditt konto.</p>
                            <ol className="list-decimal pl-5 space-y-3">
                                <li>Gå till <a href="https://dev.fitbit.com/apps/new" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">dev.fitbit.com</a> och registrera en ny app.</li>
                                <li>Sätt OAuth 2.0 Application Type till <b>Web</b> eller <b>Server</b> (inte Personal).</li>
                                <li>När Fitbit frågar efter <b>Callback URL</b>, skriv in Frejas fullständiga callback-adress, till exempel: <br /><code className="bg-black/40 text-teal-300 px-2 py-1 rounded">http://192.168.1.50:8000/api/integrations/fitbit/callback</code> <br /><small className="text-mainframe-text/50">(Ersätt IP:t med Freja-serverns IP).</small></li>
                                <li>När appen skapats, kopiera <b>OAuth 2.0 Client ID</b> och lägg in det i fältet här.</li>
                                <li>Kopiera <b>Client Secret</b> och lägg in det i fältet.</li>
                                <li>Kopiera samma <b>Callback URL</b> du angav på Fitbit och lägg i <b>Redirect URI</b>-fältet här.</li>
                                <li>Spara samtliga tre fält och klicka sedan på den stora <b>Connect Fitbit</b>-knappen för att logga in och godkänna behörigheter!</li>
                            </ol>
                            <p className="text-xs text-mainframe-text/50 mt-4">När du godkänt skickas en kod till Freja som automatiskt byts in mot en åtkomstnyckel som sparas tryggt i systemet.</p>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FitbitSettings;
