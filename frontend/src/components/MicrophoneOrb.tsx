import React from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export type AppState = 'IDLE' | 'LISTENING' | 'TRANSCRIBING' | 'REVIEWING' | 'SEARCHING' | 'GENERATING' | 'COMPLETED' | 'ABSTAINED' | 'ERROR';

interface MicrophoneOrbProps {
    appState: AppState;
    onStartRecording: () => void;
    onStopRecording: () => void;
    recordingTime: number;
}

export const MicrophoneOrb: React.FC<MicrophoneOrbProps> = ({ appState, onStartRecording, onStopRecording, recordingTime }) => {
    
    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <div className="flex flex-col items-center justify-center relative my-12">
            <div className="relative flex items-center justify-center w-40 h-40">
                {/* Pulsing Rings when listening */}
                <AnimatePresence>
                    {appState === 'LISTENING' && (
                        <>
                            <motion.div 
                                initial={{ scale: 0.8, opacity: 0.5 }}
                                animate={{ scale: 1.5, opacity: 0 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                                className="absolute w-full h-full rounded-full bg-cyan-500/30"
                            />
                            <motion.div 
                                initial={{ scale: 0.8, opacity: 0.5 }}
                                animate={{ scale: 2, opacity: 0 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 1.5, delay: 0.5, repeat: Infinity, ease: "easeOut" }}
                                className="absolute w-full h-full rounded-full bg-indigo-500/20"
                            />
                        </>
                    )}
                </AnimatePresence>

                {/* Main Button */}
                <motion.button
                    onClick={appState === 'LISTENING' ? onStopRecording : onStartRecording}
                    disabled={appState !== 'IDLE' && appState !== 'LISTENING'}
                    whileHover={appState === 'IDLE' ? { scale: 1.05 } : {}}
                    whileTap={appState === 'IDLE' || appState === 'LISTENING' ? { scale: 0.95 } : {}}
                    className={`relative z-10 flex items-center justify-center w-28 h-28 rounded-full shadow-2xl transition-all duration-300
                        ${appState === 'IDLE' ? 'bg-gradient-to-br from-indigo-500 to-cyan-500 hover:shadow-cyan-500/50' : ''}
                        ${appState === 'LISTENING' ? 'bg-gradient-to-br from-red-500 to-rose-600 shadow-red-500/50' : ''}
                        ${['TRANSCRIBING', 'SEARCHING', 'GENERATING'].includes(appState) ? 'bg-slate-800 border border-slate-700 cursor-not-allowed' : ''}
                        ${['COMPLETED', 'ABSTAINED', 'REVIEWING', 'ERROR'].includes(appState) ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-50' : ''}
                    `}
                >
                    {appState === 'IDLE' && <Mic size={40} className="text-white" />}
                    {appState === 'LISTENING' && <Square size={32} className="text-white fill-current" />}
                    {['TRANSCRIBING', 'SEARCHING', 'GENERATING'].includes(appState) && <Loader2 size={40} className="text-cyan-400 animate-spin" />}
                    {['COMPLETED', 'ABSTAINED', 'REVIEWING', 'ERROR'].includes(appState) && <Mic size={40} className="text-slate-600" />}
                </motion.button>
            </div>

            {/* Status Text */}
            <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 text-center h-8"
            >
                {appState === 'LISTENING' && (
                    <span className="text-red-400 font-mono text-xl tracking-widest font-semibold drop-shadow-md">
                        {formatTime(recordingTime)}
                    </span>
                )}
                {appState === 'TRANSCRIBING' && (
                    <span className="text-cyan-400 font-medium tracking-wide animate-pulse">Transcribing Audio...</span>
                )}
                {appState === 'SEARCHING' && (
                    <span className="text-indigo-400 font-medium tracking-wide animate-pulse">Searching MSMARCO-XI...</span>
                )}
                {appState === 'GENERATING' && (
                    <span className="text-fuchsia-400 font-medium tracking-wide animate-pulse">Generating Response...</span>
                )}
                {appState === 'IDLE' && (
                    <span className="text-slate-400 font-medium tracking-wide">Tap to speak</span>
                )}
            </motion.div>
        </div>
    );
};
