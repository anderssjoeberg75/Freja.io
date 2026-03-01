import React, { useState, useEffect, useRef } from 'react';
import { Cpu, Trash2, Download, RefreshCw, X, CheckCircle, AlertCircle, Loader2, MemoryStick, Zap } from 'lucide-react';
import { adminFetch } from '../utils/adminFetch';

const RECOMMENDED_MODELS = [
    // --- Små & Snabba (Run on almost anything) ---
    { id: 'llama3.2:1b', name: 'Llama 3.2 (1B)', minRamGB: 2, desc: 'Extremt snabb, mobil-vänlig' },
    { id: 'llama3.2', name: 'Llama 3.2 (3B)', minRamGB: 4, desc: 'Snabb standardmodell' },
    { id: 'qwen2.5:0.5b', name: 'Qwen 2.5 (0.5B)', minRamGB: 2, desc: 'Liten men naggande god' },
    { id: 'gemma2:2b', name: 'Gemma 2 (2B)', minRamGB: 4, desc: 'Liten från Google' },

    // --- Standard (Bäst balans) ---
    { id: 'llama3.1:8b', name: 'Llama 3.1 (8B)', minRamGB: 8, desc: 'Bra på svenska, grym standard' },
    { id: 'qwen2.5', name: 'Qwen 2.5 (7B)', minRamGB: 8, desc: 'Stark all-around' },
    { id: 'mistral', name: 'Mistral (7B)', minRamGB: 8, desc: 'Klassisk & pålitlig' },
    { id: 'gemma-2', name: 'Gemma 2 (9B)', minRamGB: 8, desc: 'Googles open-weights' },

    // --- Kodning (Specialister) ---
    { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder (7B)', minRamGB: 8, desc: 'Mindre kod-modell' },
    { id: 'codellama', name: 'CodeLlama (7B)', minRamGB: 8, desc: 'Metas kod-AI' },
    { id: 'deepseek-coder-v2', name: 'DeepSeek Coder V2 (16B)', minRamGB: 16, desc: 'Fantastisk kodare MoE' },

    // --- Smarta & Logik (Reasoning) ---
    { id: 'deepseek-r1:1.5b', name: 'DeepSeek R1 (1.5B)', minRamGB: 4, desc: 'Mini-reasoning' },
    { id: 'deepseek-r1:8b', name: 'DeepSeek R1 (8B)', minRamGB: 8, desc: 'Snabb reasoning' },
    { id: 'deepseek-r1:14b', name: 'DeepSeek R1 (14B)', minRamGB: 16, desc: 'Tung reasoning (Qwen)' },
    { id: 'phi4', name: 'Phi-4 (14B)', minRamGB: 14, desc: 'Bra på logik & matte' },

    // --- Tungviktare (Kräver mycket resurser) ---
    { id: 'qwen2.5:32b', name: 'Qwen 2.5 (32B)', minRamGB: 24, desc: 'Tungviktsmodell' },
    { id: 'deepseek-r1:32b', name: 'DeepSeek R1 (32B)', minRamGB: 24, desc: 'Tungvikts reasoning' },
    { id: 'mixtral', name: 'Mixtral (8x7B)', minRamGB: 32, desc: 'Kraftfull MoE från Mistral' },
    { id: 'llama3.3', name: 'Llama 3.3 (70B)', minRamGB: 48, desc: 'Enorm & kraftfull standard' },
    { id: 'deepseek-r1:70b', name: 'DeepSeek R1 (70B)', minRamGB: 48, desc: 'Gigantisk reasoning' },
];

const formatSize = (bytes) => {
    if (!bytes) return '—';
    const gb = bytes / 1024 ** 3;
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = bytes / 1024 ** 2;
    return `${mb.toFixed(0)} MB`;
};

const formatMB = (mb) => {
    if (!mb && mb !== 0) return '—';
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
};

const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('sv-SE', { year: 'numeric', month: 'short', day: 'numeric' });
};

const ProgressBar = ({ value, max, color = 'bg-mainframe-accent' }) => {
    const pct = max ? Math.min(100, Math.round((value / max) * 100)) : 0;
    const barColor = pct > 85 ? 'bg-red-500' : pct > 60 ? 'bg-yellow-500' : color;
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-black/40 rounded-full overflow-hidden">
                <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs font-mono text-mainframe-dim w-8 text-right">{pct}%</span>
        </div>
    );
};

const OllamaManager = ({ standalone = false }) => {
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeModel, setActiveModel] = useState('');

    // Resources
    const [resources, setResources] = useState(null);
    const [runningModels, setRunningModels] = useState([]);

    // Pull state
    const [pullDropdown, setPullDropdown] = useState('');
    const [customPullModel, setCustomPullModel] = useState('');
    const [pulling, setPulling] = useState(false);
    const [pullStatus, setPullStatus] = useState(null);
    const pullReaderRef = useRef(null);

    // Delete state
    const [confirmDelete, setConfirmDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    const fetchAll = async () => {
        setLoading(true);
        setError(null);
        try {
            const [modelsRes, settingsRes, resourcesRes, psRes] = await Promise.all([
                adminFetch('/api/ollama/models'),
                adminFetch('/api/settings'),
                adminFetch('/api/ollama/resources'),
                adminFetch('/api/ollama/ps'),
            ]);
            if (!modelsRes.ok) throw new Error('Kunde inte hämta modeller');
            const modelsData = await modelsRes.json();
            setModels(modelsData.models || []);
            if (settingsRes.ok) {
                const s = await settingsRes.json();
                setActiveModel(s.SELECTED_MODEL || '');
            }
            if (resourcesRes.ok) setResources(await resourcesRes.json());
            if (psRes.ok) {
                const ps = await psRes.json();
                setRunningModels(ps.models || []);
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAll(); }, []);

    const handlePull = async () => {
        const modelToPull = pullDropdown === 'custom' ? customPullModel : pullDropdown;
        if (!modelToPull.trim() || pulling) return;
        setPulling(true);
        setPullStatus({ text: 'Ansluter...', percent: 0, done: false, error: null });
        try {
            const res = await adminFetch('/api/ollama/pull', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelToPull.trim() }),
            });
            const reader = res.body.getReader();
            pullReaderRef.current = reader;
            const decoder = new TextDecoder();
            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const evt = JSON.parse(line);
                        if (evt.error) { setPullStatus({ text: evt.error, percent: 0, done: false, error: true }); setPulling(false); return; }
                        const pct = evt.total ? Math.round((evt.completed / evt.total) * 100) : null;
                        setPullStatus({ text: evt.status || '', percent: pct, done: false, error: null });
                    } catch { }
                }
            }
            setPullStatus({ text: 'Klar! 🎉', percent: 100, done: true, error: null });
            if (pullDropdown === 'custom') setCustomPullModel('');
            fetchAll();
        } catch (e) {
            setPullStatus({ text: e.message, percent: 0, done: false, error: true });
        } finally {
            setPulling(false);
            pullReaderRef.current = null;
        }
    };

    const cancelPull = () => {
        pullReaderRef.current?.cancel();
        pullReaderRef.current = null;
        setPulling(false);
        setPullStatus(null);
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            const res = await adminFetch(`/api/ollama/models/${encodeURIComponent(confirmDelete)}`, { method: 'DELETE' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Radering misslyckades');
            fetchAll();
        } catch (e) {
            setError(e.message);
        } finally {
            setDeleting(false);
            setConfirmDelete(null);
        }
    };

    return (
        <div className="space-y-6">

            {/* ── Resource Panel ───────────────────────────────────────── */}
            {resources && (
                <div className="bg-mainframe-card p-5 rounded-lg border border-mainframe-border shadow-xl">
                    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-mainframe-border/50">
                        <MemoryStick className="w-4 h-4 text-cyan-400" />
                        <h3 className="font-orbitron text-sm tracking-wider text-mainframe-text/80">SYSTEMRESURSER</h3>
                    </div>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        {/* RAM */}
                        {resources.ram && !resources.ram.error && (
                            <div className="space-y-1.5">
                                <div className="flex justify-between text-xs text-mainframe-dim">
                                    <span>RAM</span>
                                    <span className="font-mono">{resources.ram.used_gb} / {resources.ram.total_gb} GB</span>
                                </div>
                                <ProgressBar value={resources.ram.used_gb} max={resources.ram.total_gb} color="bg-cyan-500" />
                                <p className="text-[10px] text-mainframe-dim/60">{resources.ram.available_gb} GB tillgängligt</p>
                            </div>
                        )}

                        {/* GPU(s) */}
                        {resources.gpu && resources.gpu.map((g, i) => (
                            <div key={i} className="space-y-1.5">
                                <div className="flex justify-between text-xs text-mainframe-dim">
                                    <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-yellow-400" />{g.name}</span>
                                    <span className="font-mono">{formatMB(g.vram_used_mb)} / {formatMB(g.vram_total_mb)}</span>
                                </div>
                                <ProgressBar value={g.vram_used_mb} max={g.vram_total_mb} color="bg-yellow-500" />
                                <p className="text-[10px] text-mainframe-dim/60">GPU {g.utilization_pct}% · {formatMB(g.vram_free_mb)} VRAM fritt</p>
                            </div>
                        ))}

                        {/* No GPU */}
                        {resources.gpu && resources.gpu.length === 0 && (
                            <div className="flex items-center gap-2 text-xs text-mainframe-dim/60 italic">
                                <Zap className="w-3 h-3" /> Ingen NVIDIA GPU hittades – Ollama körs på CPU
                            </div>
                        )}
                    </div>

                    {/* Currently loaded models */}
                    {runningModels.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-mainframe-border/30">
                            <p className="text-[10px] uppercase tracking-wider text-mainframe-dim/60 mb-2">Laddade i minnet</p>
                            <div className="space-y-1">
                                {runningModels.map((m) => (
                                    <div key={m.name} className="flex items-center justify-between text-xs">
                                        <span className="font-mono text-mainframe-text/80 truncate">{m.name}</span>
                                        <span className="font-mono text-mainframe-dim ml-2 shrink-0">
                                            {formatSize(m.size_vram || m.size)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Model List ───────────────────────────────────────────── */}
            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl">
                <div className="flex items-center justify-between mb-6 pb-3 border-b border-mainframe-border/50">
                    <div className="flex items-center gap-3 text-xl text-mainframe-text/90">
                        <Cpu className="w-5 h-5 text-cyan-400" />
                        <h2 className="font-orbitron tracking-wider">INSTALLERADE MODELLER</h2>
                    </div>
                    <button onClick={fetchAll} disabled={loading}
                        className="p-2 rounded hover:bg-mainframe-border/30 text-mainframe-text/50 hover:text-mainframe-text transition-colors" title="Uppdatera">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-900/20 border border-red-500/40 rounded text-red-300 text-sm flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />{error}
                    </div>
                )}

                <div className="mb-6 space-y-2">
                    {loading ? (
                        <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-mainframe-dim" /></div>
                    ) : models.length === 0 ? (
                        <p className="text-center text-mainframe-dim py-6 text-sm">Inga modeller installerade.</p>
                    ) : (
                        models.map((m) => {
                            const isActive = activeModel && (
                                m.name === activeModel ||
                                m.name.startsWith(activeModel.split(':')[0] + ':')
                            );
                            const isRunning = runningModels.some(r => r.name === m.name);
                            return (
                                <div key={m.name}
                                    className={`flex items-center justify-between p-3 rounded-lg border transition-all group ${isActive
                                        ? 'bg-mainframe-accent/5 border-mainframe-accent/40'
                                        : 'bg-black/30 border-mainframe-border/40 hover:border-mainframe-border'}`}
                                >
                                    <div className="flex flex-col min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-mono text-sm text-mainframe-text truncate">{m.name}</span>
                                            {isActive && (
                                                <span className="shrink-0 text-[10px] uppercase tracking-wider text-mainframe-accent bg-mainframe-accent/10 border border-mainframe-accent/30 px-1.5 py-0.5 rounded">● Aktiv</span>
                                            )}
                                            {isRunning && (
                                                <span className="shrink-0 text-[10px] uppercase tracking-wider text-green-400 bg-green-400/10 border border-green-400/30 px-1.5 py-0.5 rounded">▶ Laddad</span>
                                            )}
                                        </div>
                                        <span className="text-xs text-mainframe-dim">
                                            {formatSize(m.size)} · {formatDate(m.modified_at)}
                                        </span>
                                    </div>
                                    <button onClick={() => setConfirmDelete(m.name)}
                                        className="ml-4 p-2 rounded text-mainframe-dim hover:text-red-400 hover:bg-red-900/20 transition-all opacity-0 group-hover:opacity-100" title="Radera modell">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Pull / Install */}
                <div className="space-y-3">
                    <p className="text-xs uppercase tracking-wider text-mainframe-text/50">Installera ny modell</p>
                    <div className="flex gap-2">
                        {(() => {
                            // Calculate total VRAM if GPUs exist, otherwise fallback to system RAM
                            let totalAvailableHardwareGB = 0;
                            if (resources?.gpu && resources.gpu.length > 0) {
                                const totalVramMB = resources.gpu.reduce((acc, curr) => acc + curr.vram_total_mb, 0);
                                totalAvailableHardwareGB = totalVramMB / 1024;
                            } else if (resources?.ram?.total_gb) {
                                totalAvailableHardwareGB = resources.ram.total_gb;
                            }

                            return (
                                <select
                                    value={pullDropdown}
                                    onChange={(e) => setPullDropdown(e.target.value)}
                                    disabled={pulling}
                                    className={`bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text font-mono text-sm focus:border-mainframe-accent focus:outline-none transition-all appearance-none cursor-pointer ${pullDropdown === 'custom' ? 'w-1/3' : 'flex-1'}`}
                                >
                                    <option value="" disabled>Välj rekommenderad modell...</option>
                                    {RECOMMENDED_MODELS.filter(m => !totalAvailableHardwareGB || totalAvailableHardwareGB >= m.minRamGB).map(m => (
                                        <option key={m.id} value={m.id}>
                                            {m.name} – {m.desc} (Kräver {m.minRamGB}GB)
                                        </option>
                                    ))}
                                    <option value="custom">Anpassad modell (skriv in namn...)</option>
                                </select>
                            );
                        })()}

                        {pullDropdown === 'custom' && (
                            <input
                                type="text"
                                value={customPullModel}
                                onChange={(e) => setCustomPullModel(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handlePull()}
                                placeholder="t.ex. llama3.2, phi4, gemma3:4b"
                                disabled={pulling}
                                className="flex-1 bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text font-mono text-sm focus:border-mainframe-accent focus:outline-none transition-all placeholder-mainframe-dim/50"
                            />
                        )}

                        {pulling ? (
                            <button onClick={cancelPull} className="px-4 py-2.5 bg-red-900/20 border border-red-500/40 text-red-400 hover:bg-red-900/40 rounded transition-all flex items-center gap-2 text-sm">
                                <X className="w-4 h-4" /> Avbryt
                            </button>
                        ) : (
                            <button onClick={handlePull} disabled={(!pullDropdown || (pullDropdown === 'custom' && !customPullModel.trim()))}
                                className="px-4 py-2.5 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/30 hover:border-mainframe-accent rounded transition-all flex items-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed">
                                <Download className="w-4 h-4" /> Installera
                            </button>
                        )}
                    </div>

                    {pullStatus && (
                        <div className={`p-3 rounded border text-sm ${pullStatus.error ? 'bg-red-900/20 border-red-500/40 text-red-300' : pullStatus.done ? 'bg-green-900/20 border-green-500/40 text-green-300' : 'bg-mainframe-card border-mainframe-border text-mainframe-text/70'}`}>
                            <div className="flex items-center gap-2">
                                {pullStatus.done ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                                    : pullStatus.error ? <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                                        : <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
                                <span className="truncate">{pullStatus.text}</span>
                                {pullStatus.percent !== null && !pullStatus.done && (
                                    <span className="ml-auto shrink-0 font-mono text-xs">{pullStatus.percent}%</span>
                                )}
                            </div>
                            {pulling && pullStatus.percent !== null && (
                                <div className="mt-2 h-1.5 bg-black/40 rounded-full overflow-hidden">
                                    <div className="h-full bg-mainframe-accent rounded-full transition-all duration-300" style={{ width: `${pullStatus.percent}%` }} />
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Delete Confirm Dialog */}
            {confirmDelete && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-mainframe-card border border-red-500/40 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <Trash2 className="w-5 h-5 text-red-400" />
                            <h3 className="font-orbitron text-mainframe-text">Radera modell</h3>
                        </div>
                        <p className="text-sm text-mainframe-dim mb-6">
                            Är du säker på att du vill radera <span className="font-mono text-mainframe-text">{confirmDelete}</span>?
                            Modellen måste laddas ner igen om du vill använda den.
                        </p>
                        <div className="flex gap-3 justify-end">
                            <button onClick={() => setConfirmDelete(null)}
                                className="px-4 py-2 border border-mainframe-border rounded text-mainframe-dim hover:text-mainframe-text hover:border-mainframe-text/40 text-sm transition-all">
                                Avbryt
                            </button>
                            <button onClick={handleDelete} disabled={deleting}
                                className="px-4 py-2 bg-red-900/30 border border-red-500/50 text-red-300 hover:bg-red-900/50 rounded text-sm transition-all flex items-center gap-2 disabled:opacity-50">
                                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                                Radera
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OllamaManager;
