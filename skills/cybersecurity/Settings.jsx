import React from 'react';
import { Shield, Info, ExternalLink } from 'lucide-react';

const CybersecuritySettings = () => {
    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Shield className="w-8 h-8 text-red-500" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Cybersecurity Skill
                </h1>
            </div>

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="flex items-start gap-4 p-4 bg-red-900/10 border border-red-900/30 rounded-lg">
                    <Info className="w-6 h-6 text-red-400 shrink-0 mt-1" />
                    <div>
                        <h2 className="text-xl font-bold text-red-400 mb-2 font-orbitron">SYSTEM ACTIVE</h2>
                        <p className="text-sm text-mainframe-text/80 leading-relaxed">
                            Cybersecurity module is enabled. This skill provides tools for security auditing,
                            passive reconnaissance, and vulnerability analysis.
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-mainframe-accent border-b border-mainframe-border/30 pb-2">Functional Overview</h3>
                    <ul className="list-disc list-inside space-y-2 text-sm text-mainframe-text/70">
                        <li><strong>Passive Recon:</strong> Uses search tools to gather public information about targets.</li>
                        <li><strong>Audit Tools:</strong> Can run automated code audits and CVE lookups.</li>
                        <li><strong>Workflow:</strong> Use <code>/hacka [domän]</code> in chat to start a security test.</li>
                    </ul>
                </div>

                <div className="pt-4 border-t border-mainframe-border/50">
                    <p className="text-xs text-center text-mainframe-text/40">
                        No specific configuration settings required at this time. All tools leverage core intelligence settings.
                    </p>
                </div>
            </div>

            <div className="mt-8 flex justify-center">
                <a
                    href="/docs/cybersecurity_guide.md"
                    className="flex items-center gap-2 px-6 py-2 bg-mainframe-accent/10 border border-mainframe-accent/30 text-mainframe-accent rounded hover:bg-mainframe-accent/20 transition-all uppercase tracking-widest text-sm font-bold"
                >
                    <ExternalLink className="w-4 h-4" />
                    Read Security Guide
                </a>
            </div>
        </div>
    );
};

export default CybersecuritySettings;
