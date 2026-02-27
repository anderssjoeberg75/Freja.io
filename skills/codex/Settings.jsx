import React from 'react';
import { Terminal, Code, Cpu, Info } from 'lucide-react';

const CodexSettings = () => {
    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Terminal className="w-8 h-8 text-green-500" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Codex (Code Intelligence)
                </h1>
            </div>

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

                <div className="pt-4 border-t border-mainframe-border/50 text-center">
                    <p className="text-xs text-mainframe-text/40">
                        Codex relies on the <strong>Intelligence</strong> settings (selected model) for its operations.
                    </p>
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
