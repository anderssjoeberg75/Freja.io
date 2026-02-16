import React, { useState } from 'react';
import { Info, AlertTriangle, Loader2 } from 'lucide-react';

const HaAliasManager = ({ settings, handleChange, handleSave, saving }) => {
    const aliases = JSON.parse(settings.HA_ALIASES || "{}");
    const [newKey, setNewKey] = useState("");
    const [newValue, setNewValue] = useState("");

    const addAlias = () => {
        if (!newKey || !newValue) return;
        const updated = { ...aliases, [newKey.toLowerCase().trim()]: newValue.trim() };
        handleChange("HA_ALIASES", JSON.stringify(updated));
        handleSave("HA_ALIASES", JSON.stringify(updated));
        setNewKey("");
        setNewValue("");
    };

    const deleteAlias = (key) => {
        const updated = { ...aliases };
        delete updated[key];
        handleChange("HA_ALIASES", JSON.stringify(updated));
        handleSave("HA_ALIASES", JSON.stringify(updated));
    };

    return (
        <div className="grid gap-4">
            <p className="text-xs text-zinc-500 mb-2">
                Map short names (e.g. <span className="text-mainframe-accent">"kontor"</span>) to full entity IDs.
                Separate multiple IDs with commas to create a group (e.g. <span className="text-mainframe-accent">"light.1, light.2"</span>).
            </p>

            {Object.keys(aliases).length > 0 && (
                <div className="grid gap-2 mb-4">
                    {Object.entries(aliases).map(([k, v]) => (
                        <div key={k} className="flex items-center justify-between bg-black/20 p-2 rounded border border-mainframe-border/30">
                            <div className="flex gap-4 items-center">
                                <span className="text-mainframe-accent font-mono text-sm">{k}</span>
                                <span className="text-zinc-500 text-xs">→</span>
                                <span className="text-mainframe-text/80 font-mono text-sm">{v}</span>
                            </div>
                            <button
                                onClick={() => deleteAlias(k)}
                                disabled={saving}
                                className="text-red-400 hover:text-red-300 p-1 disabled:opacity-50"
                                title="Delete Alias"
                            >
                                <AlertTriangle className="w-4 h-4" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex gap-2 items-center bg-black/10 p-3 rounded border border-dashed border-mainframe-border/50">
                <input
                    placeholder="Alias (e.g. kontor)"
                    value={newKey}
                    onChange={(e) => setNewKey(e.target.value)}
                    className="flex-1 bg-black/30 border border-mainframe-border rounded px-3 py-1 text-sm text-mainframe-text focus:outline-none focus:border-mainframe-accent"
                />
                <span className="text-zinc-500">→</span>
                <input
                    placeholder="Entity ID (e.g. light.kontor_2)"
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    className="flex-1 bg-black/30 border border-mainframe-border rounded px-3 py-1 text-sm text-mainframe-text focus:outline-none focus:border-mainframe-accent"
                />
                <button
                    onClick={addAlias}
                    disabled={saving}
                    className="bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent px-3 py-1 rounded hover:bg-mainframe-accent/30 text-sm font-bold disabled:opacity-50"
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Add"}
                </button>
            </div>
        </div>
    );
};

export default HaAliasManager;
