import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { API_URL } from '../config';

export default function ChatInterface() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedModel, setSelectedModel] = useState("gemini-2.0-flash");
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Fetch settings to get selected model
    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await fetch(`${API_URL}/api/settings`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.SELECTED_MODEL) {
                        setSelectedModel(data.SELECTED_MODEL);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch settings:", err);
            }
        };
        fetchSettings();
    }, []);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const history = messages.map(m => ({
                role: m.role,
                content: m.content
            }));
            history.push(userMsg);

            const res = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: selectedModel,
                    messages: history,
                    session_id: "default"
                })
            });

            if (!res.ok) throw new Error('Network response was not ok');

            const data = await res.json();
            const botMsg = { role: 'assistant', content: data.response || data.error || 'No response' };
            setMessages(prev => [...prev, botMsg]);

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-mainframe-bg text-mainframe-text">
            {/* Header */}
            <div className="p-4 border-b border-mainframe-border bg-mainframe-card/50 backdrop-blur flex justify-between items-center">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Bot className="w-6 h-6 text-mainframe-accent" />
                    Neural Interface
                </h2>
                <div className="text-xs text-zinc-500 font-mono">
                    Model: {selectedModel}
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-zinc-500 mt-20">
                        <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>Mainframe Online. Waiting for input.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`
                            max-w-[80%] rounded-2xl p-4 flex gap-3
                            ${msg.role === 'user'
                                ? 'bg-mainframe-accent text-black rounded-tr-sm'
                                : 'bg-mainframe-card border border-mainframe-border rounded-tl-sm'}
                        `}>
                            <div className="mt-1 shrink-0">
                                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                            </div>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-mainframe-card border border-mainframe-border rounded-2xl p-4 rounded-tl-sm flex items-center gap-2 text-zinc-400">
                            <Bot size={18} />
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Processing...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-mainframe-border bg-mainframe-card">
                <form onSubmit={sendMessage} className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a command or query..."
                        className="flex-1 bg-zinc-900 border border-mainframe-border rounded-xl px-4 py-3 focus:outline-none focus:border-mainframe-accent transition-colors"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="bg-mainframe-accent text-black p-3 rounded-xl hover:bg-mainframe-accent/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
}
