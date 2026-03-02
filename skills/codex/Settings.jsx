import React, { useState, useEffect } from 'react';
import { Terminal, Code, Cpu, Save, Loader2 } from 'lucide-react';
import { adminFetch } from '../../client/src/utils/adminFetch';
import { formatModelOption } from '../../client/src/utils/modelDescriptions';

const CodexSettings = () => {
    const [settings, setSettings] = useState({});
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
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

            let loadedSettings = settingsData || {};

            // Auto-select the best coding model if none is configured
            if (!loadedSettings.CODEX_MODEL) {
                const CODING_MODEL_PRIORITY = [
                    "o1", "o3-mini", "gemini-2.5-flash", "gemini-2.0-flash",
                    "deepseek-coder-v2", "qwen2.5-coder:32b", "qwen2.5-coder",
                    "gpt-4o", "codellama"
                ];
                let bestModel = "";
                for (const preferred of CODING_MODEL_PRIORITY) {
                    const match = availableModels.find(m => m.toLowerCase().startsWith(preferred));
                    if (match) {
                        bestModel = match;
                        break;
                    }
                }
                // Fallback to first if no matches
                if (!bestModel && availableModels.length > 0) {
                    bestModel = availableModels[0];
                }
                loadedSettings.CODEX_MODEL = bestModel;
            }

            setSettings(loadedSettings);
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to load data.' });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleModelChange = async (val) => {
        handleChange('CODEX_MODEL', val);
        setSaving(true);
        setMessage(null);
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: 'CODEX_MODEL', value: val })
            });
            const data = await res.json();
            if (data.success) {
                setMessage({ type: 'success', text: `Codex model updated to ${val || 'system default'}.` });
            } else {
                setMessage({ type: 'error', text: 'Could not save model.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Error saving.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
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
                setMessage({ type: 'success', text: 'Saved!' });
            } else {
                setMessage({ type: 'error', text: 'Could not save setting.' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'An error occurred.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    if (loading) return <div className="p-8"><Loader2 className="animate-spin text-mainframe-text/50" /></div>;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Terminal className="w-8 h-8 text-green-500" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Codex (Code Intelligence)
                </h1>
            </div>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="flex items-start gap-4 p-4 bg-green-900/10 border border-green-900/30 rounded-lg">
                    <Code className="w-6 h-6 text-green-400 shrink-0 mt-1" />
                    <div>
                        <h2 className="text-xl font-bold text-green-400 mb-2 font-orbitron">CODE ENGINE READY</h2>
                        <p className="text-sm text-mainframe-text/80 leading-relaxed">
                            Codex provides advanced code analysis, refactoring, and generation tools.
                            It is integrated directly into the system's core loop.
                        </p>
                    </div>
                </div>

                <div className="py-2 border-t border-b border-mainframe-border/30">
                    <div className="grid gap-2 my-4">
                        <label className="text-sm font-medium text-mainframe-text/70 uppercase tracking-tight flex items-center gap-2">
                            Codex Model Override
                        </label>
                        <div className="flex gap-2 w-96">
                            <select
                                value={settings.CODEX_MODEL || ''}
                                onChange={(e) => handleChange('CODEX_MODEL', e.target.value)}
                                className="flex-1 min-w-0 truncate bg-black/40 border border-mainframe-border rounded px-4 py-2 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer"
                            >
                                <option value="">Use system default model</option>
                                {models.map((opt) => (
                                    <option key={opt} value={opt}>{formatModelOption(opt)}</option>
                                ))}
                            </select>
                            <button
                                onClick={() => handleSave('CODEX_MODEL')}
                                disabled={saving}
                                className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                            >
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-xs text-zinc-500 italic mt-1">
                            Select a specific model for code analysis. Otherwise uses `SELECTED_MODEL` from main settings. Models are fetched from Ollama, Gemini, and OpenAI.
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-mainframe-accent border-b border-mainframe-border/30 pb-2">Features</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-3 bg-black/30 border border-mainframe-border/30 rounded">
                            <h4 className="font-bold text-sm mb-1 uppercase tracking-tighter">Analysis</h4>
                            <p className="text-xs text-mainframe-text/50 text-wrap">Deep structural analysis of Python and Javascript projects.</p>
                        </div>
                        <div className="p-3 bg-black/30 border border-mainframe-border/30 rounded">
                            <h4 className="font-bold text-sm mb-1 uppercase tracking-tighter">Refactoring</h4>
                            <p className="text-xs text-mainframe-text/50 text-wrap">Automated skill migration and codebase cleanup.</p>
                        </div>
                        <div className="p-3 bg-black/30 border border-mainframe-border/30 rounded">
                            <h4 className="font-bold text-sm mb-1 uppercase tracking-tighter">Auditing</h4>
                            <p className="text-xs text-mainframe-text/50 text-wrap">Integrated security and performance auditing via Docker containers.</p>
                        </div>
                        <div className="p-3 bg-black/30 border border-mainframe-border/30 rounded">
                            <h4 className="font-bold text-sm mb-1 uppercase tracking-tighter">Persistence</h4>
                            <p className="text-xs text-mainframe-text/50 text-wrap">Long-term memory of project structure and logic.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-8 p-4 bg-zinc-900/30 border border-mainframe-border/50 rounded-lg flex items-center gap-4">
                <Cpu className="w-10 h-10 text-mainframe-dim opacity-30" />
                <div className="text-xs text-mainframe-text/50 italic">
                    "The architect's hammer is logic; the foundations are code."
                </div>
            </div>
        </div>
    );
};

export default CodexSettings;
