import React, { useState, useEffect } from 'react';
import { Save, Bot, Loader2, Activity, AlertTriangle, Download, ChevronRight } from 'lucide-react';
import { getAvailableSkills, loadSkillSettings } from '../utils/skillRegistry';
import { adminFetch, getAdminToken, setAdminToken } from '../utils/adminFetch';
import SettingsField from './SettingsField';
import { formatModelOption } from '../utils/modelDescriptions';

const Settings = () => {
    const [settings, setSettings] = useState({});
    const [schema, setSchema] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [models, setModels] = useState([]);
    const [adminToken, setAdminTokenState] = useState(getAdminToken());
    const [tokenMessage, setTokenMessage] = useState(null);

    // Dynamic Skill State
    const [availableSkills, setAvailableSkills] = useState([]);
    const [selectedSkillId, setSelectedSkillId] = useState("");
    const [SkillComponent, setSkillComponent] = useState(null);
    const [skillLoading, setSkillLoading] = useState(false);

    useEffect(() => {
        fetchInitialData();
        const skills = getAvailableSkills();
        setAvailableSkills(skills);
    }, []);

    // Load skill component when selection changes
    useEffect(() => {
        if (selectedSkillId) {
            loadSkill(selectedSkillId);
        } else {
            setSkillComponent(null);
        }
    }, [selectedSkillId]);

    const loadSkill = async (id) => {
        setSkillLoading(true);
        try {
            const Component = await loadSkillSettings(id);
            setSkillComponent(() => Component);
        } catch (err) {
            console.error("Failed to load skill component", err);
            setMessage({ type: 'error', text: `Failed to load skill settings for ${id}` });
        } finally {
            setSkillLoading(false);
        }
    }

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const [settingsRes, schemaRes, modelsRes] = await Promise.all([
                adminFetch('/api/settings'),
                adminFetch('/api/settings/schema'),
                adminFetch('/api/models')
            ]);
            if (!settingsRes.ok || !schemaRes.ok || !modelsRes.ok) {
                throw new Error("Admin token required or invalid.");
            }
            const settingsData = await settingsRes.json();
            const schemaData = await schemaRes.json();
            const modelsData = await modelsRes.json();

            setSettings(settingsData || {});
            setSchema(Array.isArray(schemaData) ? schemaData : []);
            setModels(modelsData.models || []);
        } catch (err) {
            console.error("Failed to fetch settings data:", err);
            setMessage({ type: 'error', text: `Could not load settings: ${err.message}` });
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
                setMessage({ type: 'success', text: data.message || `${key} updated successfully!` });
                const isSecret = schema.some((item) => item.key === key && item.type === 'password');
                if (isSecret) {
                    setSettings(prev => ({
                        ...prev,
                        [key]: '',
                        __secrets: { ...(prev.__secrets || {}), [key]: true }
                    }));
                }
            } else {
                setMessage({ type: 'error', text: 'Could not save setting.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleBackup = async () => {
        try {
            const res = await adminFetch('/api/system/backup_db');
            if (!res.ok) {
                throw new Error("Could not fetch backup.");
            }
            const blob = await res.blob();
            const disposition = res.headers.get("content-disposition") || "";
            const match = disposition.match(/filename="([^"]+)"/);
            const filename = match ? match[1] : "mainframe_backup.db";
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setMessage({ type: 'error', text: 'Backup failed.' });
        }
    };

    const handleTokenSave = () => {
        const cleaned = adminToken.trim();
        setAdminToken(cleaned);
        setTokenMessage(cleaned ? "Admin token saved." : "Admin token cleared.");
        fetchInitialData();
        setTimeout(() => setTokenMessage(null), 3000);
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full text-mainframe-text">
            <Loader2 className="animate-spin mr-2" /> Loading configuration...
        </div>
    );

    // Filter Sections - Only show Core System Settings (Identity & Intelligence) when no skill is selected
    const identityItems = schema.filter(i => i.section === 'Identity');
    const intelligenceItems = schema.filter(i => i.section === 'Intelligence');

    const renderField = (item) => {
        const secretConfigured = settings.__secrets && settings.__secrets[item.key];

        return (
            <SettingsField
                key={item.key}
                label={item.label}
                value={settings[item.key]}
                onChange={(val) => handleChange(item.key, val)}
                onSave={() => handleSave(item.key)}
                type={item.type}
                options={item.options || models}
                formatOption={(opt) => item.key.includes('MODEL') ? formatModelOption(opt) : opt}
                secretConfigured={secretConfigured}
                saving={saving}
                description={item.description}
            />
        );
    };

    const handleSaveSection = async (items, sectionName) => {
        setSaving(true);
        setMessage(null);
        let successCount = 0;
        let failCount = 0;

        try {
            for (const item of items) {
                // If value is undefined or empty and it's not a secret, skip or send default?
                // For now, we send whatever is in settings state.
                const res = await adminFetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: item.key, value: settings[item.key] })
                });
                const data = await res.json();
                if (data.success) {
                    successCount++;
                    if (item.type === 'password') {
                        setSettings(prev => ({
                            ...prev,
                            [item.key]: '',
                            __secrets: { ...(prev.__secrets || {}), [item.key]: true }
                        }));
                    }
                } else {
                    failCount++;
                }
            }

            if (failCount === 0) {
                setMessage({ type: 'success', text: `All ${sectionName} settings updated successfully!` });
            } else {
                setMessage({ type: 'error', text: `${successCount} saved, ${failCount} failed.` });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving section.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
            <div className="mb-6 p-4 border border-mainframe-border rounded-lg bg-mainframe-card/60">
                <div className="flex items-center gap-4 flex-wrap">
                    <label className="text-xs uppercase tracking-wider text-mainframe-text/60">Admin Token</label>
                    <input
                        type="password"
                        value={adminToken}
                        onChange={(e) => setAdminTokenState(e.target.value)}
                        placeholder="X-Admin-Token"
                        className="flex-1 min-w-[240px] bg-black/40 border border-mainframe-border rounded px-3 py-2 text-mainframe-text text-sm"
                    />
                    <button
                        onClick={handleTokenSave}
                        className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 text-sm"
                    >
                        Save token
                    </button>
                </div>
                {tokenMessage && <p className="text-xs text-mainframe-text/60 mt-2">{tokenMessage}</p>}
            </div>

            <div className="flex items-center justify-between mb-8 border-b border-mainframe-border pb-4 gap-4">
                <h1 className="text-3xl font-orbitron text-mainframe-accent whitespace-nowrap">
                    System Configuration
                </h1>

                <div className="flex items-center gap-4 flex-1 justify-end">
                    {/* Dynamic Skill Dropdown */}
                    <div className="relative max-w-xs w-full">
                        <select
                            value={selectedSkillId}
                            onChange={(e) => setSelectedSkillId(e.target.value)}
                            className="w-full bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                        >
                            <option value="">-- Core Settings --</option>
                            {availableSkills.map(skill => (
                                <option key={skill.id} value={skill.id}>{skill.name}</option>
                            ))}
                        </select>
                        <ChevronRight className="w-4 h-4 text-mainframe-text/50 absolute right-3 top-1/2 -translate-y-1/2 rotate-90 pointer-events-none" />
                    </div>

                    <button
                        onClick={handleBackup}
                        className="flex items-center gap-2 px-4 py-2 bg-mainframe-card border border-mainframe-border rounded hover:bg-mainframe-border/30 transition-colors text-mainframe-text/80 text-sm font-bold uppercase tracking-wider whitespace-nowrap"
                    >
                        <Download className="w-4 h-4" />
                        Backup DB
                    </button>
                </div>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border transition-all ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            {/* If a skill is selected, render it. Otherwise render core settings */}
            {selectedSkillId ? (
                <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                    {skillLoading ? (
                        <div className="flex justify-center p-10"><Loader2 className="animate-spin w-8 h-8 text-mainframe-dim" /></div>
                    ) : SkillComponent ? (
                        <SkillComponent />
                    ) : (
                        <div className="text-center p-10 text-mainframe-dim">Could not load skill component.</div>
                    )}
                </div>
            ) : (
                <div className="grid gap-10 animate-in fade-in slide-in-from-left-2 duration-300">
                    {/* Identity Section */}
                    {identityItems.length > 0 && (
                        <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl">
                            <div className="flex items-center gap-3 mb-8 text-xl text-mainframe-text/90 pb-3 border-b border-mainframe-border/50">
                                <Bot className="w-5 h-5 text-purple-400" />
                                <h2 className="font-orbitron tracking-wider">IDENTITY</h2>
                            </div>
                            <div className="grid gap-8">
                                {identityItems.map(renderField)}
                            </div>
                            <div className="mt-8 pt-6 border-t border-mainframe-border/30 flex justify-end">
                                <button
                                    onClick={() => handleSaveSection(identityItems, 'Identity')}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-mainframe-accent text-black font-bold uppercase tracking-widest rounded hover:bg-mainframe-accent/80 transition-all disabled:opacity-50 text-sm"
                                >
                                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Save Identity
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Intelligence Section */}
                    {intelligenceItems.length > 0 && (
                        <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl">
                            <div className="flex items-center gap-3 mb-8 text-xl text-mainframe-text/90 pb-3 border-b border-mainframe-border/50">
                                <Activity className="w-5 h-5 text-green-400" />
                                <h2 className="font-orbitron tracking-wider">INTELLIGENCE</h2>
                            </div>
                            <div className="grid gap-8">
                                {intelligenceItems.map(renderField)}
                            </div>
                            <div className="mt-8 pt-6 border-t border-mainframe-border/30 flex justify-end">
                                <button
                                    onClick={() => handleSaveSection(intelligenceItems, 'Intelligence')}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-mainframe-accent text-black font-bold uppercase tracking-widest rounded hover:bg-mainframe-accent/80 transition-all disabled:opacity-50 text-sm"
                                >
                                    {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                                    Save Intelligence
                                </button>
                            </div>
                        </div>
                    )}


                    <div className="p-5 bg-yellow-900/10 border border-yellow-700/30 rounded-lg text-yellow-500/80 text-sm flex items-start gap-4">
                        <AlertTriangle className="w-6 h-6 shrink-0" />
                        <div>
                            <strong className="block mb-1 text-yellow-500 uppercase tracking-tighter">Security Notice</strong>
                            <p>Sensitive keys are stored in the Vault and are never returned to the browser. The Admin API now requires an admin token.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
