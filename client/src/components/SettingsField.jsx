import React, { useId } from 'react';
import { Save, Loader2, ChevronRight } from 'lucide-react';

const SettingsField = ({
    label,
    value,
    onChange,
    onSave,
    type = 'text',
    placeholder,
    secretConfigured,
    saving,
    description,
    options = [],
    formatOption = (opt) => opt
}) => {
    const isSecret = type === 'password';
    const id = useId();

    // Logic for secret fields:
    // If it's a secret and we know it's configured, but the current value in state is empty,
    // we show the dots placeholder.
    const effectivePlaceholder = (isSecret && secretConfigured && !value)
        ? "••••••••••••••••"
        : (placeholder || `Enter ${label}`);

    // We display an empty string if it's a stored secret that hasn't been re-typed
    const displayValue = (isSecret && secretConfigured && !value) ? '' : value;

    return (
        <div className="grid gap-2">
            <div className="flex items-center gap-2">
                <label htmlFor={id} className="text-sm font-bold uppercase tracking-wider text-mainframe-text/60">
                    {label}
                </label>
                {(isSecret && secretConfigured) || (!isSecret && value) ? (
                    <span className="text-[10px] uppercase tracking-wider text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded">● Set</span>
                ) : null}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); onSave(); }} className="flex gap-2">
                {type === 'select' ? (
                    <div className="relative flex-1 min-w-0">
                        <select
                            id={id}
                            value={value || ''}
                            onChange={(e) => onChange(e.target.value)}
                            className="w-full bg-black/40 border border-mainframe-border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm appearance-none cursor-pointer truncate pr-8"
                        >
                            <option value="" disabled>Choose {label.toLowerCase()}...</option>
                            {options.map((opt) => (
                                <option key={opt} value={opt}>
                                    {formatOption(opt)}
                                </option>
                            ))}
                        </select>
                        <ChevronRight className="w-4 h-4 text-mainframe-text/50 absolute right-3 top-1/2 -translate-y-1/2 rotate-90 pointer-events-none" />
                    </div>
                ) : (
                    <input
                        id={id}
                        type={type}
                        value={displayValue || ''}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={effectivePlaceholder}
                        className={`flex-1 min-w-0 bg-black/40 border rounded px-4 py-2.5 text-mainframe-text focus:border-mainframe-accent focus:outline-none transition-all font-mono text-sm truncate ${isSecret && secretConfigured && !value
                            ? 'border-green-500/30 placeholder-green-400/60'
                            : 'border-mainframe-border'
                            }`}
                    />
                )}
                <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 bg-mainframe-accent/20 border border-mainframe-accent/50 text-mainframe-accent rounded hover:bg-mainframe-accent/30 disabled:opacity-50 transition-all flex items-center gap-2 justify-center min-w-[90px]"
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    <span className="text-sm font-bold tracking-widest uppercase">Save</span>
                </button>
            </form>
            {description && <p className="text-xs text-zinc-500 italic mt-1">{description}</p>}
        </div>
    );
};

export default SettingsField;

