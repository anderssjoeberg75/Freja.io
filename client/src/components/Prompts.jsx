import { useState, useEffect } from 'react';
import { Save, Loader2, Edit3, Terminal } from 'lucide-react';

const Prompts = () => {
    const [prompts, setPrompts] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const [selectedKey, setSelectedKey] = useState(null);
    const [editValue, setEditValue] = useState("");

    useEffect(() => {
        fetchPrompts();
    }, []);

    const fetchPrompts = async () => {
        try {
            const res = await fetch('/api/prompts');
            const data = await res.json();
            setPrompts(data);
            if (Object.keys(data).length > 0 && !selectedKey) {
                // Select first prompt by default if none selected
                const firstKey = Object.keys(data)[0];
                setSelectedKey(firstKey);
                setEditValue(data[firstKey]);
            }
        } catch (err) {
            console.error("Failed to fetch prompts:", err);
            setMessage({ type: 'error', text: 'Failed to load prompts.' });
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (key) => {
        setSelectedKey(key);
        setEditValue(prompts[key]);
        setMessage(null);
    };

    const handleSave = async () => {
        if (!selectedKey) return;
        setSaving(true);
        setMessage(null);

        try {
            const res = await fetch('/api/prompts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: selectedKey, value: editValue })
            });
            const data = await res.json();

            if (data.success) {
                setMessage({ type: 'success', text: `Saved ${selectedKey} successfully!` });
                setPrompts(prev => ({ ...prev, [selectedKey]: editValue }));
            } else {
                setMessage({ type: 'error', text: 'Failed to save prompt.' });
            }
        } catch (err) {
            console.error("Save error:", err);
            setMessage({ type: 'error', text: 'Error saving prompt.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 3000);
        }
    };

    if (loading) return <div className="flex items-center justify-center h-full text-mainframe-text"><Loader2 className="animate-spin mr-2" /> Loading Prompts...</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto h-full overflow-hidden flex flex-col">
            <h1 className="text-3xl font-orbitron mb-6 text-mainframe-accent border-b border-mainframe-border pb-4 flex items-center gap-3">
                <Terminal className="w-8 h-8" />
                Prompt Engineering
            </h1>

            {message && (
                <div className={`mb-6 p-4 rounded border ${message.type === 'error' ? 'bg-red-900/20 border-red-500 text-red-200' : 'bg-green-900/20 border-green-500 text-green-200'}`}>
                    {message.text}
                </div>
            )}

            <div className="flex gap-6 flex-1 overflow-hidden">
                {/* Sidebar List */}
                <div className="w-1/3 bg-mainframe-card border border-mainframe-border rounded-lg overflow-y-auto">
                    <div className="p-4 bg-black/20 font-bold border-b border-mainframe-border text-mainframe-text/80">
                        Available Prompts
                    </div>
                    <div>
                        {Object.keys(prompts).map(key => (
                            <button
                                key={key}
                                onClick={() => handleSelect(key)}
                                className={`w-full text-left p-4 border-b border-mainframe-border/50 hover:bg-mainframe-accent/5 transition-colors flex items-center justify-between
                                    ${selectedKey === key ? 'bg-mainframe-accent/10 text-mainframe-accent border-l-4 border-l-mainframe-accent' : 'text-mainframe-text/70'}
                                `}
                            >
                                <span className="font-mono text-sm truncate">{key}</span>
                                {selectedKey === key && <Edit3 className="w-4 h-4" />}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Editor Area */}
                <div className="flex-1 bg-mainframe-card border border-mainframe-border rounded-lg flex flex-col">
                    <div className="p-4 bg-black/20 flex justify-between items-center border-b border-mainframe-border">
                        <span className="font-mono text-sm text-mainframe-accent font-bold">
                            {selectedKey || "Select a prompt"}
                        </span>
                        <button
                            onClick={handleSave}
                            disabled={saving || !selectedKey}
                            className="px-4 py-2 bg-mainframe-accent text-black rounded hover:bg-mainframe-accent/80 transition-colors flex items-center gap-2 font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Save Changes
                        </button>
                    </div>

                    <div className="flex-1 p-0 relative">
                        <textarea
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            disabled={!selectedKey}
                            className="w-full h-full bg-zinc-900/50 text-mainframe-text font-mono text-sm p-4 resize-none focus:outline-none focus:bg-black/40 transition-colors"
                            spellCheck="false"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Prompts;
