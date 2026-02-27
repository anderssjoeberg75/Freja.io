import React from 'react';
import { Clock, Calendar, Zap, Info } from 'lucide-react';

const SchedulerSettings = () => {
    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-auto text-mainframe-text">
            <div className="flex items-center gap-4 mb-8 border-b border-mainframe-border pb-4">
                <Clock className="w-8 h-8 text-mainframe-accent" />
                <h1 className="text-3xl font-orbitron text-mainframe-accent">
                    Task Scheduler
                </h1>
            </div>

            <div className="bg-mainframe-card p-6 rounded-lg border border-mainframe-border shadow-xl space-y-6">
                <div className="flex items-start gap-4 p-4 bg-mainframe-accent/10 border border-mainframe-accent/30 rounded-lg">
                    <Calendar className="w-6 h-6 text-mainframe-accent shrink-0 mt-1" />
                    <div>
                        <h2 className="text-xl font-bold text-mainframe-accent mb-2 font-orbitron">SCHEDULER SERVICE</h2>
                        <p className="text-sm text-mainframe-text/80 leading-relaxed">
                            The scheduler handles background tasks, proactive reminders, and
                            time-based execution of various skills.
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-mainframe-accent border-b border-mainframe-border/30 pb-2">Active Jobs</h3>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-black/40 border border-mainframe-border/30 rounded">
                            <div className="flex items-center gap-3">
                                <Zap className="w-4 h-4 text-yellow-400" />
                                <span className="text-sm font-mono">Morning Briefing</span>
                            </div>
                            <span className="text-[10px] uppercase tracking-widest bg-green-500/20 text-green-400 px-2 py-1 rounded">Daily / 07:00</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-black/40 border border-mainframe-border/30 rounded opacity-60">
                            <div className="flex items-center gap-3">
                                <Zap className="w-4 h-4 text-blue-400" />
                                <span className="text-sm font-mono">Health Sync</span>
                            </div>
                            <span className="text-[10px] uppercase tracking-widest bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Hourly</span>
                        </div>
                    </div>
                </div>

                <div className="pt-4 border-t border-mainframe-border/50">
                    <p className="text-xs text-center text-mainframe-text/40">
                        Detailed job configuration is currently handled via <code>proactive_service.py</code>.
                    </p>
                </div>
            </div>

            <div className="mt-8 p-4 bg-zinc-900/30 border border-mainframe-border/50 rounded-lg flex items-center gap-4">
                <Info className="w-5 h-5 text-mainframe-dim opacity-50" />
                <div className="text-xs text-mainframe-text/40 italic">
                    "Time is the fire in which we burn."
                </div>
            </div>
        </div>
    );
};

export default SchedulerSettings;
