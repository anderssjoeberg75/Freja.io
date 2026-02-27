import React from 'react';
import { Save, Loader2 } from 'lucide-react';

const SettingsField = ({
    label,
    value,
    onChange,
    onSave,
    type = 'text',
    placeholder,
    secretConfigured,
    saving,
    description
}) => {
    const isSecret = type === 'password';

    // Logic for secret fields:
    // If it's a secret and we know it's configured, but the current value in state is empty,
    // we show the dots placeholder.
    const effectivePlaceholder = (isSecret && secretConfigured && !value)
        ? "••••••••••••••••"
        : (placeholder || `Ange ${label}`);

    // We display an empty string if it's a stored secret that hasn't been re-typed
    const displayValue = (isSecret && secretConfigured && !value) ? '' : value;

    return (
        <div className="grid gap-2">
            <div className="flex items-center gap-2">
                <label className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">
                    {label}
                </label>
                {isSecret && secretConfigured && (
                    <span className="text-[10px] uppercase tracking-wider text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded">● Satt</span>
                )}
            </div>
            <div className="flex gap-2">
                <input
                    type={type}
                    value={displayValue || ''}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={effectivePlaceholder}
                    className={`flex-1 bg-black/40 border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm ${isSecret && secretConfigured && !value
                        ? 'border-green-500/30 placeholder-green-400/60'
                        : 'border-mainframe-border'
                        }`}
                />
                <button
                    onClick={onSave}
                    disabled={saving}
                    className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center justify-center min-w-[50px]"
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                </button>
            </div>
            {description && <p className="text-xs text-zinc-500 italic mt-1">{description}</p>}
        </div>
    );
};

export default SettingsField;
