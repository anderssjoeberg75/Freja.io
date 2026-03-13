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

                {/* Refresh Token */}
                <SettingsField
                    label="Initial Refresh Token"
                    value={settings.FITBIT_REFRESH_TOKEN}
                    onChange={(val) => handleChange('FITBIT_REFRESH_TOKEN', val)}
                    onSave={() => handleSave('FITBIT_REFRESH_TOKEN')}
                    type="password"
                    secretConfigured={settings.__secrets && settings.__secrets.FITBIT_REFRESH_TOKEN}
                    placeholder="Lång kod-sträng"
                    description="Anges manuellt från OAuth 2.0-flödet för att aktivera uppkopplingen."
                    saving={saving}
                />
            </div>

            {/* Help Modal */}
            {showHelp && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowHelp(false)}>
                    <div className="bg-mainframe-card border-2 border-mainframe-accent rounded-xl p-8 max-w-2xl max-h-[85vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <h2 className="text-2xl font-orbitron mb-6 text-mainframe-accent tracking-widest border-b border-mainframe-border pb-4">Fitbit Setup Guide</h2>
                        <div className="space-y-6 text-mainframe-text/90">
                            <p>För att Freja ska kunna läsa din Fitbit-datakurva behöver du skapa en utvecklarapp kopplad till ditt konto. Då vi inte har en automatisk callback-lyssnare just nu görs setupen manuellt en gång.</p>
                            <ol className="list-decimal pl-5 space-y-3">
                                <li>Gå till <a href="https://dev.fitbit.com/apps/new" target="_blank" className="text-mainframe-accent underline" rel="noreferrer">dev.fitbit.com</a> och registrera en ny app. Typ: <b>Personal</b>.</li>
                                <li>Ange <code className="bg-black/40 text-teal-300 px-1 rounded">http://localhost:8000</code> (eller valfri URL du äger) som <b>Callback URL</b>.</li>
                                <li>När appen är skapad, kopiera in <b>Client ID</b> och <b>Client Secret</b> i inställningarna till vänster (spara).</li>
                                <li>Klicka sedan på <b>"OAuth 2.0 tutorial page"</b> längst ner på din Fitbit-appsida för att generera en token.</li>
                                <li>Scrolla ner till Step 2 (Authorization) och klicka på länken. Fyll i vad som helst som inte godkänns, och var väldigt vaksam på URL:en du skickas tillbaka till.</li>
                                <li>Du kommer skickas till `localhost:8000/?code=...`. Ta <b>koden</b> från adressfältet och stoppa in den i "Step 3".</li>
                                <li>Svaret du får ut från "Step 3" innehåller en <code className="bg-black/40 text-teal-300 px-1 rounded">refresh_token</code>.</li>
                                <li>Kopiera värdet för refresh_token och klistra in det i fältet <b>Initial Refresh Token</b> här på Freja.</li>
                            </ol>
                            <p className="text-xs text-mainframe-text/50 mt-4">När du lagt in refresh-tokenen kommer Freja själv att förnya den framöver när den går ut. Detta behöver bara göras en enda gång (eller ifall Freja har varit avstängd i flera månader).</p>
                        </div>
                        <button onClick={() => setShowHelp(false)} className="mt-10 w-full py-3 bg-mainframe-accent text-black rounded font-bold uppercase tracking-widest hover:brightness-110 active:scale-[0.98] transition-all">Got it</button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FitbitSettings;
