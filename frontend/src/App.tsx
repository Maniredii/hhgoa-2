import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, Edit3, CheckCircle2, RotateCcw } from 'lucide-react';
import { sendTextQuery } from './services/api';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { MicrophoneOrb } from './components/MicrophoneOrb';
import type { AppState } from './components/MicrophoneOrb';
import { PipelineVisualizer } from './components/PipelineVisualizer';
import { LatencyPanel } from './components/LatencyPanel';
import { AnswerCard } from './components/AnswerCard';

function App() {
  const [appState, setAppState] = useState<AppState>('IDLE');
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [transcript, setTranscript] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const handleTranscriptResult = (t: string) => {
    setTranscript(t);
  };

  const handleMicError = (e: string) => {
    setError(e);
  };

  const { startRecording, stopRecording, recordingTime } = useAudioRecorder(
    handleTranscriptResult,
    handleMicError,
    setAppState
  );

  const processTextQuery = async (query: string) => {
    if (!query.trim()) return;
    setAppState('SEARCHING');
    setError(null);
    setResponse(null);
    setIsEditing(false);
    
    try {
      // Small simulated delay for UI feedback on SEARCHING state
      await new Promise(r => setTimeout(r, 800)); 
      
      setAppState('GENERATING');
      const data = await sendTextQuery(query);
      
      setResponse(data);
      if (data.status === 'abstained') setAppState('ABSTAINED');
      else setAppState('COMPLETED');
      
    } catch (err) {
      setError("Failed to process query. Backend might be down.");
      setAppState('ERROR');
      console.error(err);
    }
  };

  const resetState = () => {
    setAppState('IDLE');
    setTranscript('');
    setResponse(null);
    setError(null);
    setIsEditing(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200 font-sans overflow-x-hidden relative">
      
      {/* Dynamic Background Glow based on State */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] blur-[120px] transition-colors duration-[2s] rounded-full opacity-30
            ${appState === 'IDLE' ? 'bg-indigo-900/40' : ''}
            ${appState === 'LISTENING' ? 'bg-rose-900/60' : ''}
            ${appState === 'TRANSCRIBING' ? 'bg-cyan-900/50' : ''}
            ${['SEARCHING', 'GENERATING'].includes(appState) ? 'bg-fuchsia-900/50' : ''}
            ${appState === 'COMPLETED' ? 'bg-emerald-900/30' : ''}
            ${appState === 'ABSTAINED' ? 'bg-amber-900/30' : ''}
            ${appState === 'ERROR' ? 'bg-red-900/50' : ''}
        `} />
      </div>

      {/* Header */}
      <header className="relative z-10 w-full pt-10 pb-4 flex flex-col items-center justify-center">
        <motion.div 
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex items-center gap-3"
        >
          <BrainCircuit className="w-8 h-8 text-cyan-400" />
          <h1 className="text-3xl font-extrabold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">
            VAANIRAG
          </h1>
        </motion.div>
        <motion.p 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
            className="text-slate-400 mt-2 font-light tracking-wide text-sm"
        >
          Voice-enabled multilingual retrieval intelligence
        </motion.p>
      </header>

      <main className="relative z-10 max-w-4xl mx-auto px-4 py-8 flex flex-col items-center min-h-[calc(100vh-160px)]">
        
        {/* Main Mic Interaction */}
        <div className={`transition-all duration-700 ease-in-out ${appState !== 'IDLE' && appState !== 'LISTENING' ? 'scale-75 opacity-70 mb-0' : 'scale-100 opacity-100 mb-12'}`}>
            <MicrophoneOrb 
                appState={appState} 
                onStartRecording={startRecording} 
                onStopRecording={stopRecording} 
                recordingTime={recordingTime} 
            />
        </div>

        <div className="w-full space-y-8 flex-1 flex flex-col">
            
            {/* Transcript Review Panel */}
            <AnimatePresence mode="wait">
                {['REVIEWING', 'SEARCHING', 'GENERATING', 'COMPLETED', 'ABSTAINED', 'ERROR'].includes(appState) && transcript && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="w-full max-w-2xl mx-auto bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl p-6 shadow-2xl"
                    >
                        <h3 className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-3">You said:</h3>
                        
                        {isEditing ? (
                            <textarea 
                                value={transcript}
                                onChange={e => setTranscript(e.target.value)}
                                className="w-full bg-slate-950 text-slate-200 border border-slate-700 rounded-xl p-4 min-h-[100px] focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 resize-none transition-all"
                                autoFocus
                            />
                        ) : (
                            <p className="text-xl md:text-2xl font-light text-slate-200 leading-relaxed">
                                "{transcript}"
                            </p>
                        )}

                        <div className="flex items-center justify-end gap-3 mt-6">
                            {appState === 'REVIEWING' && (
                                <>
                                    <button onClick={resetState} className="flex items-center gap-2 px-4 py-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors text-sm font-medium">
                                        <RotateCcw size={16} /> Discard
                                    </button>
                                    <button onClick={() => setIsEditing(!isEditing)} className="flex items-center gap-2 px-4 py-2 rounded-full text-indigo-400 hover:bg-indigo-950/50 hover:text-indigo-300 transition-colors text-sm font-medium border border-indigo-900/50">
                                        <Edit3 size={16} /> {isEditing ? 'Done' : 'Edit'}
                                    </button>
                                    <button onClick={() => processTextQuery(transcript)} className="flex items-center gap-2 px-6 py-2 rounded-full bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-[0_0_15px_rgba(6,182,212,0.4)] text-sm font-bold tracking-wide">
                                        <CheckCircle2 size={16} /> Ask
                                    </button>
                                </>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Pipeline Visualizer */}
            <AnimatePresence>
                {['TRANSCRIBING', 'REVIEWING', 'SEARCHING', 'GENERATING', 'COMPLETED', 'ABSTAINED'].includes(appState) && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="w-full">
                        <PipelineVisualizer appState={appState} />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Error Message */}
            <AnimatePresence>
                {appState === 'ERROR' && error && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-red-950/50 border border-red-900/50 rounded-2xl text-red-400 text-center max-w-xl mx-auto w-full">
                        <p>{error}</p>
                        <button onClick={resetState} className="mt-4 px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-full text-sm">Try Again</button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Final Answer Card & Latency */}
            <AnimatePresence>
                {(appState === 'COMPLETED' || appState === 'ABSTAINED') && response && (
                    <motion.div 
                        initial={{ opacity: 0, y: 30 }} 
                        animate={{ opacity: 1, y: 0 }} 
                        transition={{ delay: 0.1 }}
                        className="w-full space-y-6 pb-20"
                    >
                        <AnswerCard response={response} />
                        <LatencyPanel metrics={response.latency} />
                        
                        <div className="flex justify-center pt-8">
                            <button onClick={resetState} className="flex items-center gap-2 px-8 py-3 rounded-full bg-slate-800 hover:bg-slate-700 text-white transition-all shadow-lg text-sm font-bold tracking-widest border border-slate-700">
                                <RotateCcw size={18} /> ASK ANOTHER QUESTION
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

        </div>
      </main>
    </div>
  );
}

export default App;
