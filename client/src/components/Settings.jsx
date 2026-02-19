import React, { useState, useEffect } from 'react';
import { Save, Bot, Loader2, Activity, AlertTriangle, Download, ChevronRight } from 'lucide-react';
import { getAvailableSkills, loadSkillSettings } from '../utils/skillRegistry';

const Settings = () => {
    const [settings, setSettings] = useState({});
    const [schema, setSchema] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [models, setModels] = useState([]);

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
                fetch('/api/settings'),
                fetch('/api/settings/schema'),
                fetch('/api/models')
            ]);
            const settingsData = await settingsRes.json();
            const schemaData = await schemaRes.json();
            const modelsData = await modelsRes.json();

            setSettings(settingsData || {});
            setSchema(Array.isArray(schemaData) ? schemaData : []);
            setModels(modelsData.models || []);
        } catch (err) {
            console.error("Failed to fetch settings data:", err);
            setMessage({ type: 'error', text: `Kunde inte ladda inställningar: ${err.message}` });
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
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value: settings[key] })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Uppdaterade ${key} framgångsrikt!` });
            } else {
                setMessage({ type: 'error', text: 'Kunde inte spara inställningen.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Fel vid sparning.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    const handleBackup = () => {
        window.open('/api/system/backup_db', '_blank');
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full text-mainframe-text">
            <Loader2 className="animate-spin mr-2" /> Laddar konfiguration...
        </div>
    );

    // Filter Sections - Only show Core System Settings (Identity & Intelligence) when no skill is selected
    const identityItems = schema.filter(i => i.section === 'Identity');
    const intelligenceItems = schema.filter(i => i.section === 'Intelligence');

    const renderField = (item) => (
        <div key={item.key} className="grid gap-2">
            <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight">
                    {item.label}
                </label>
            </div>
            <div className="flex gap-2">
                {item.type === 'select' ? (
                    <select
                        value={settings[item.key] || ''}
                        onChange={(e) => handleChange(item.key, e.target.value)}
                        className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                    >
                        <option value="" disabled>Välj modell...</option>
                        {(item.options || models).map((opt) => (
                            <option key={opt} value={opt}>{opt}</option>
                        ))}
                    </select>
                ) : (
                    <input
                        type={item.type}
                        value={settings[item.key] || ''}
                        onChange={(e) => handleChange(item.key, e.target.value)}
                        placeholder={item.description || `Ange ${item.label}`}
                        className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm"
                    />
                )}

                <button
                    onClick={() => handleSave(item.key)}
                    disabled={saving}
                    className="px-5 py-2.5 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/30 hover:border-mainframe-accent rounded transition-all flex items-center shadow-lg"
                >
                    {saving ? <Loader2 className="w-4 h-5 animate-spin" /> : <Save className="w-4 h-5" />}
                </button>
            </div>
            {item.description && <p className="text-xs text-zinc-500 italic mt-1">{item.description}</p>}
        </div>
    );

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto">
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
                        </div>
                    )}

                    <div className="p-5 bg-yellow-900/10 border border-yellow-700/30 rounded-lg text-yellow-500/80 text-sm flex items-start gap-4">
                        <AlertTriangle className="w-6 h-6 shrink-0" />
                        <div>
                            <strong className="block mb-1 text-yellow-500 uppercase tracking-tighter">Säkerhetsnotis</strong>
                            <p>Konfiguration och känsliga nycklar lagras i en lokal SQLite-databas. Se till att miljö och fysisk åtkomst är begränsad.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Settings;
