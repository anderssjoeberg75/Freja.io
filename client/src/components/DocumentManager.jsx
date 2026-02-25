import React, { useState, useEffect, useRef } from 'react';
import { FileText, Trash2, Download, Upload, RefreshCw, X, CheckCircle, AlertCircle, Loader2, Database } from 'lucide-react';
import { adminFetch } from '../utils/adminFetch';

const DocumentManager = ({ standalone = false }) => {
    const [documents, setDocuments] = useState([]);
    const [totalChunks, setTotalChunks] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Upload state
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const fileInputRef = useRef(null);

    // Delete state
    const [confirmDelete, setConfirmDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    const fetchDocuments = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminFetch('/api/documents');
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Kunde inte hämta dokument');
            setDocuments(data.documents || []);
            setTotalChunks(data.total_chunks || 0);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchDocuments(); }, []);

    const handleFileSelect = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setUploadStatus({ text: `Laddar upp ${file.name}...`, error: false, done: false });

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Need a new endpoint in backend to handle file upload and pass to tool
            const res = await adminFetch('/api/documents/upload', {
                method: 'POST',
                body: formData, // Don't set Content-Type, browser will set it with boundary
            });
            
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Uppladdning misslyckades');
            
            setUploadStatus({ text: 'Klar! 🎉', error: false, done: true });
            fetchDocuments();
        } catch (e) {
            setUploadStatus({ text: e.message, error: true, done: false });
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            const res = await adminFetch(`/api/documents/${encodeURIComponent(confirmDelete)}`, { method: 'DELETE' });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Radering misslyckades');
            fetchDocuments();
        } catch (e) {
            setError(e.message);
        } finally {
            setDeleting(false);
            setConfirmDelete(null);
        }
    };

    return (
        <div className="space-y-6">
            {/* Stats Panel */}
            <div className="bg-mainframe-card p-5 rounded-lg border border-mainframe-border shadow-xl">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-mainframe-border/50">
                    <Database className="w-4 h-4 text-cyan-400" />
                    <h3 className="font-orbitron text-sm tracking-wider text-mainframe-text/80">KUNSKAPSDATABAS</h3>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <span className="text-xs text-mainframe-dim">Indexerade Filer</span>
                        <div className="text-2xl font-mono text-mainframe-text">{documents.length}</div>
                    </div>
                    <div className="space-y-1">
                        <span className="text-xs text-mainframe-dim">Totalt antal semantiska chunks</span>
                        <div className="text-2xl font-mono text-mainframe-text">{totalChunks}</div>
                    </div>
                </div>
            </div>

            {/* Document List */}
            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl">
                <div className="flex items-center justify-between mb-6 pb-3 border-b border-mainframe-border/50">
                    <div className="flex items-center gap-3 text-xl text-mainframe-text/90">
                        <FileText className="w-5 h-5 text-cyan-400" />
                        <h2 className="font-orbitron tracking-wider">INDEXERADE DOKUMENT</h2>
                    </div>
                    <button onClick={fetchDocuments} disabled={loading}
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
                    ) : documents.length === 0 ? (
                        <p className="text-center text-mainframe-dim py-6 text-sm">Inga dokument indexerade ännu.</p>
                    ) : (
                        documents.map((doc) => (
                            <div key={doc.name}
                                className="flex items-center justify-between p-3 rounded-lg border transition-all group bg-black/30 border-mainframe-border/40 hover:border-mainframe-border"
                            >
                                <div className="flex flex-col min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="font-mono text-sm text-mainframe-text truncate">{doc.name}</span>
                                    </div>
                                    <span className="text-xs text-mainframe-dim mt-1">
                                        {doc.chunks} semantiska chunks
                                    </span>
                                </div>
                                <button onClick={() => setConfirmDelete(doc.name)}
                                    className="ml-4 p-2 rounded text-mainframe-dim hover:text-red-400 hover:bg-red-900/20 transition-all opacity-0 group-hover:opacity-100" title="Radera dokument">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))
                    )}
                </div>

                {/* Upload Section */}
                <div className="space-y-3">
                    <p className="text-xs uppercase tracking-wider text-mainframe-text/50">Ladda upp nytt dokument (PDF, TXT, MD)</p>
                    
                    <input 
                        type="file" 
                        ref={fileInputRef}
                        accept=".pdf,.txt,.md"
                        onChange={handleFileSelect}
                        className="hidden" 
                    />
                    
                    <button 
                        onClick={() => fileInputRef.current?.click()} 
                        disabled={uploading}
                        className="w-full px-4 py-3 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent hover:bg-mainframe-accent/30 hover:border-mainframe-accent rounded transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed border-dashed"
                    >
                        {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                        {uploading ? 'Bearbetar dokument...' : 'Klicka för att välja fil'}
                    </button>

                    {uploadStatus && (
                        <div className={`p-3 rounded border text-sm ${uploadStatus.error ? 'bg-red-900/20 border-red-500/40 text-red-300' : uploadStatus.done ? 'bg-green-900/20 border-green-500/40 text-green-300' : 'bg-mainframe-card border-mainframe-border text-mainframe-text/70'}`}>
                            <div className="flex items-center gap-2">
                                {uploadStatus.done ? <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                                    : uploadStatus.error ? <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                                        : <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
                                <span className="truncate">{uploadStatus.text}</span>
                            </div>
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
                            <h3 className="font-orbitron text-mainframe-text">Radera dokument</h3>
                        </div>
                        <p className="text-sm text-mainframe-dim mb-6">
                            Är du säker på att du vill ta bort <span className="font-mono text-mainframe-text">{confirmDelete}</span> från kunskapsbasen?
                            Det kan inte ångras.
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

export default DocumentManager;
