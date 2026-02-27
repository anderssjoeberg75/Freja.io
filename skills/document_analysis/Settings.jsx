import React from 'react';
import { Database, Search, Upload, Info } from 'lucide-react';

const DocumentAnalysisSettings = () => {
    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Database className="w-8 h-8 text-purple-400" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Document Analysis (RAG)
                </h1>
            </div>

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="flex items-start gap-4 p-4 bg-purple-900/10 border border-purple-900/30 rounded-lg">
                    <Search className="w-6 h-6 text-purple-400 shrink-0 mt-1" />
                    <div>
                        <h2 className="text-xl font-bold text-purple-400 mb-2 font-orbitron">KNOWLEDGE BASE ACTIVE</h2>
                        <p className="text-sm text-mainframe-text/80 leading-relaxed">
                            This skill manages your private document library. It uses ChromaDB for vector retrieval
                            and Ollama for local embeddings.
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-mainframe-accent border-b border-mainframe-border/30 pb-2">Technical Specs</h3>
                    <ul className="list-disc list-inside space-y-2 text-sm text-mainframe-text/70">
                        <li><strong>Database:</strong> ChromaDB (Local Persistence)</li>
                        <li><strong>Embedding Model:</strong> <code>nomic-embed-text</code> (via Ollama)</li>
                        <li><strong>Chunking:</strong> Semantic paragraph-aware (approx 600 chars)</li>
                        <li><strong>Deduplication:</strong> SHA-256 content hashing</li>
                    </ul>
                </div>

                <div className="pt-4 border-t border-mainframe-border/50">
                    <div className="flex items-center gap-2 p-3 bg-zinc-900/50 rounded text-xs text-mainframe-text/50">
                        <Upload className="w-4 h-4" />
                        <span>Use the Document Manager in the sidebar to upload and manage your files.</span>
                    </div>
                </div>
            </div>

            <div className="mt-8 p-4 bg-zinc-900/30 border border-mainframe-border/50 rounded-lg flex items-center gap-4">
                <Info className="w-5 h-5 text-mainframe-dim opacity-50" />
                <div className="text-xs text-mainframe-text/40">
                    Settings for this skill are currently managed via the <code>Intelligence</code> global configuration (Ollama URL).
                </div>
            </div>
        </div>
    );
};

export default DocumentAnalysisSettings;
