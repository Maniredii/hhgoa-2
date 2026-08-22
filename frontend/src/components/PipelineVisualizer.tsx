import React from 'react';
import { motion } from 'framer-motion';
import type { AppState } from './MicrophoneOrb';

interface PipelineVisualizerProps {
    appState: AppState;
    responseStatus?: string; // COMPLETED, ABSTAINED, FAILED
}

const STAGES = [
    { id: 'voice', label: 'Voice' },
    { id: 'stt', label: 'Sarvam STT' },
    { id: 'query_processing', label: 'Query Processing' },
    { id: 'hybrid_retrieval', label: 'Hybrid Retrieval' },
    { id: 'reranking', label: 'Reranking' },
    { id: 'generation', label: 'Generation' },
    { id: 'guardrails', label: 'Guardrails' },
    { id: 'answer', label: 'Answer' },
];

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ appState }) => {
    
    const getActiveStageIndex = () => {
        if (appState === 'IDLE' || appState === 'LISTENING') return 0;
        if (appState === 'TRANSCRIBING') return 1;
        if (appState === 'REVIEWING') return 1;
        if (appState === 'SEARCHING') return 3; // Hybrid Retrieval
        if (appState === 'GENERATING') return 5; // Generation
        if (appState === 'COMPLETED' || appState === 'ABSTAINED') return 7;
        return -1;
    };

    const activeIndex = getActiveStageIndex();

    return (
        <div className="w-full bg-slate-900/50 backdrop-blur-md rounded-2xl p-6 border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase tracking-wider">Pipeline Activity</h3>
            <div className="flex items-center justify-between relative">
                {/* Background line */}
                <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-800 -translate-y-1/2 z-0 rounded-full" />
                
                {/* Active line */}
                <motion.div 
                    className="absolute top-1/2 left-0 h-1 bg-cyan-500 -translate-y-1/2 z-0 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                    initial={{ width: 0 }}
                    animate={{ width: activeIndex >= 0 ? `${(activeIndex / (STAGES.length - 1)) * 100}%` : '0%' }}
                    transition={{ duration: 0.5 }}
                />

                {STAGES.map((stage, index) => {
                    const isPast = activeIndex > index;
                    const isActive = activeIndex === index;
                    
                    let nodeColor = "bg-slate-800 border-slate-700";
                    let textColor = "text-slate-500";
                    
                    if (isPast) {
                        nodeColor = "bg-cyan-500 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.6)]";
                        textColor = "text-slate-300";
                    } else if (isActive) {
                        nodeColor = "bg-indigo-500 border-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.8)]";
                        textColor = "text-white font-bold";
                    }

                    return (
                        <div key={stage.id} className="relative z-10 flex flex-col items-center">
                            <motion.div 
                                className={`w-4 h-4 rounded-full border-2 transition-colors duration-300 ${nodeColor}`}
                                animate={isActive ? { scale: [1, 1.3, 1] } : { scale: 1 }}
                                transition={{ repeat: isActive ? Infinity : 0, duration: 1.5 }}
                            />
                            <div className={`absolute top-6 text-[10px] sm:text-xs whitespace-nowrap transition-colors duration-300 ${textColor}`}>
                                {stage.label}
                            </div>
                        </div>
                    );
                })}
            </div>
            
            {/* Height spacer for absolute text */}
            <div className="h-6"></div>
        </div>
    );
};
