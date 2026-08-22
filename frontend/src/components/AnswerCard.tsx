import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, ShieldAlert, Globe, Activity, FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface AnswerCardProps {
    response: any; // UnifiedRAGResponse
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ response }) => {
    const [isSourcesOpen, setIsSourcesOpen] = useState(false);
    const [isDebugOpen, setIsDebugOpen] = useState(false);

    if (!response) return null;

    const confScore = (response.confidence * 100).toFixed(0);
    const isAbstained = response.status === 'abstained';
    const isSafe = response.guardrails?.input_safe ?? true;

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl mx-auto space-y-6"
        >
            {/* Main Answer Area */}
            <div className={`p-8 rounded-3xl border shadow-2xl relative overflow-hidden backdrop-blur-xl ${isAbstained ? 'bg-amber-950/40 border-amber-800/50' : 'bg-slate-900/60 border-slate-700/50'}`}>
                
                {/* Background glow */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120%] h-32 bg-indigo-500/10 blur-[100px] pointer-events-none" />

                {/* Header Metrics */}
                <div className="flex flex-wrap items-center gap-3 mb-8 relative z-10">
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-semibold text-slate-300">
                        <Activity size={14} className={response.confidence > 0.8 ? 'text-green-400' : 'text-amber-400'} />
                        Confidence {confScore}%
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-semibold text-slate-300">
                        <Globe size={14} className="text-cyan-400" />
                        Language: {response.language?.toUpperCase() || 'EN'}
                    </div>
                    {response.guardrails?.grounded ? (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-900/30 border border-emerald-800/50 text-xs font-semibold text-emerald-400">
                            <CheckCircle2 size={14} />
                            Fully Grounded
                        </div>
                    ) : (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-900/30 border border-amber-800/50 text-xs font-semibold text-amber-400">
                            <ShieldAlert size={14} />
                            {isAbstained ? 'Abstained' : 'Ungrounded'}
                        </div>
                    )}
                    {!isSafe && (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-900/30 border border-rose-800/50 text-xs font-semibold text-rose-400">
                            <ShieldAlert size={14} />
                            Blocked Request
                        </div>
                    )}
                </div>

                {/* Answer Content */}
                <div className="relative z-10">
                    {isAbstained ? (
                        <div className="text-xl md:text-2xl text-amber-200/80 font-light leading-relaxed italic border-l-4 border-amber-500/50 pl-6">
                            "{response.answer}"
                        </div>
                    ) : (
                        <div className="prose prose-invert prose-lg max-w-none prose-p:leading-relaxed prose-p:text-slate-200 font-light">
                            {response.answer.split('\n').map((line: string, i: number) => (
                                <p key={i}>{line}</p>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Citations / Sources Accordion */}
            {response.sources && response.sources.length > 0 && (
                <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-md">
                    <button 
                        onClick={() => setIsSourcesOpen(!isSourcesOpen)}
                        className="w-full flex items-center justify-between p-5 hover:bg-slate-800/50 transition-colors"
                    >
                        <div className="flex items-center gap-2">
                            <FileText size={18} className="text-indigo-400" />
                            <span className="font-semibold text-slate-300 tracking-wide">Retrieved Evidence ({response.sources.length} sources)</span>
                        </div>
                        {isSourcesOpen ? <ChevronUp size={20} className="text-slate-500" /> : <ChevronDown size={20} className="text-slate-500" />}
                    </button>
                    
                    <AnimatePresence>
                        {isSourcesOpen && (
                            <motion.div 
                                initial={{ height: 0 }}
                                animate={{ height: 'auto' }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                            >
                                <div className="p-5 pt-0 space-y-3">
                                    {response.sources.map((src: any, i: number) => (
                                        <div key={i} className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/50 flex flex-col gap-2">
                                            <div className="flex justify-between items-center">
                                                <span className="text-xs font-mono font-bold px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded">Source {i+1}: {src.chunk_id}</span>
                                                <span className="text-xs font-mono text-cyan-500 bg-cyan-950 px-2 py-1 rounded">Score: {src.score.toFixed(3)}</span>
                                            </div>
                                            <p className="text-sm text-slate-400 leading-relaxed font-light mt-1">"{src.text}"</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}

            {/* Technical Debug Accordion */}
            <div className="bg-slate-900/20 border border-slate-800/50 rounded-2xl overflow-hidden">
                <button 
                    onClick={() => setIsDebugOpen(!isDebugOpen)}
                    className="w-full flex items-center justify-between p-4 hover:bg-slate-800/30 transition-colors"
                >
                    <span className="text-xs font-mono text-slate-500 uppercase tracking-widest">Retrieval Debug & Guardrails</span>
                    {isDebugOpen ? <ChevronUp size={16} className="text-slate-600" /> : <ChevronDown size={16} className="text-slate-600" />}
                </button>
                
                <AnimatePresence>
                    {isDebugOpen && (
                        <motion.div 
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="p-4 pt-0 font-mono text-xs text-slate-500 space-y-1">
                                <div><span className="text-slate-400">Request ID:</span> {response.request_id}</div>
                                <div><span className="text-slate-400">Status:</span> {response.status}</div>
                                <div><span className="text-slate-400">Guardrails Decision:</span> {response.guardrails?.decision}</div>
                                <div><span className="text-slate-400">Guardrails Reason:</span> {response.guardrails?.reason || 'None'}</div>
                                <div><span className="text-slate-400">Context Sufficient:</span> {response.guardrails?.context_sufficient ? 'True' : 'False'}</div>
                                <div className="pt-2">Raw Guardrails JSON:</div>
                                <pre className="bg-black/50 p-3 rounded-lg overflow-x-auto text-[10px] text-cyan-600/70">
                                    {JSON.stringify(response.guardrails, null, 2)}
                                </pre>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

        </motion.div>
    );
};
