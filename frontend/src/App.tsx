import React, { useState } from 'react';
import { VoiceRecorder } from './components/VoiceRecorder';
import { sendVoiceQuery, sendTextQuery } from './services/api';
import { BrainCircuit, Activity, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

function App() {
  const [response, setResponse] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [textInput, setTextInput] = useState('');

  const handleVoiceRecording = async (blob: Blob) => {
    setIsProcessing(true);
    setError(null);
    setResponse(null);
    try {
      const data = await sendVoiceQuery(blob);
      setResponse(data);
    } catch (err) {
      setError("Failed to process voice query. Backend might be down.");
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    
    setIsProcessing(true);
    setError(null);
    setResponse(null);
    try {
      const data = await sendTextQuery(textInput);
      setResponse(data);
    } catch (err) {
      setError("Failed to process text query. Backend might be down.");
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen font-sans bg-slate-50 dark:bg-dark-bg text-slate-900 dark:text-slate-100 selection:bg-primary-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-dark-border bg-white dark:bg-dark-card sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-8 h-8 text-primary-500" />
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-400">
              VaaniRAG
            </h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 font-medium bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-full">
            <Activity className="w-4 h-4 text-green-500" />
            System Online
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 grid grid-cols-1 md:grid-cols-12 gap-8">
        
        {/* Input Column */}
        <div className="md:col-span-5 space-y-6">
          <div className="bg-white dark:bg-dark-card p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-dark-border">
            <h2 className="text-lg font-semibold mb-4">Voice Input</h2>
            <VoiceRecorder onRecordingComplete={handleVoiceRecording} isProcessing={isProcessing} />
          </div>

          <div className="flex items-center gap-4 py-2">
            <div className="flex-1 h-px bg-slate-200 dark:bg-dark-border"></div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">OR</span>
            <div className="flex-1 h-px bg-slate-200 dark:bg-dark-border"></div>
          </div>

          <form onSubmit={handleTextSubmit} className="bg-white dark:bg-dark-card p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-dark-border">
            <h2 className="text-lg font-semibold mb-4">Text Input</h2>
            <textarea
              className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all resize-none h-24 text-sm"
              placeholder="Ask anything..."
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              disabled={isProcessing}
            />
            <button
              type="submit"
              disabled={isProcessing || !textInput.trim()}
              className="mt-3 w-full bg-primary-600 hover:bg-primary-500 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white font-medium py-2.5 rounded-xl transition-colors"
            >
              Send Query
            </button>
          </form>
        </div>

        {/* Output Column */}
        <div className="md:col-span-7 space-y-6">
          {error && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex gap-3 border border-red-100 dark:border-red-900/50">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <p className="text-sm">{error}</p>
            </motion.div>
          )}

          {isProcessing && !response && !error && (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400">
              <Activity className="w-8 h-8 animate-pulse mb-3" />
              <p>Analyzing audio & searching knowledge base...</p>
            </div>
          )}

          {response && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              
              <div className="bg-white dark:bg-dark-card p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-dark-border relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-primary-500" />
                <h3 className="text-sm font-semibold text-primary-600 dark:text-primary-400 mb-2 uppercase tracking-wider">Final Answer</h3>
                
                {response.is_abstained ? (
                  <p className="text-lg text-slate-600 dark:text-slate-300 italic">
                    {response.answer}
                  </p>
                ) : (
                  <div className="prose dark:prose-invert max-w-none text-lg">
                    {response.answer}
                  </div>
                )}
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "STT", value: response.latency.stt_ms },
                  { label: "Retrieval", value: response.latency.retrieval_ms },
                  { label: "Reranking", value: response.latency.reranking_ms },
                  { label: "Generation", value: response.latency.generation_ms },
                ].map(m => (
                  <div key={m.label} className="bg-white dark:bg-dark-card p-4 rounded-xl border border-slate-200 dark:border-dark-border flex flex-col items-center justify-center text-center">
                    <span className="text-xs text-slate-500 uppercase font-semibold">{m.label}</span>
                    <span className="text-lg font-bold text-slate-800 dark:text-slate-100">{m.value.toFixed(0)} ms</span>
                  </div>
                ))}
              </div>

              {/* Sources */}
              {response.sources && response.sources.length > 0 && (
                <div className="bg-white dark:bg-dark-card p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-dark-border">
                  <h3 className="text-sm font-semibold text-slate-500 mb-4 uppercase tracking-wider">Retrieved Context ({response.sources.length} chunks)</h3>
                  <div className="space-y-3">
                    {response.sources.map((src: any, i: number) => (
                      <div key={i} className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg text-sm border border-slate-100 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-mono text-primary-600 dark:text-primary-400">{src.chunk_id}</span>
                          <span className="text-xs font-mono text-slate-400">Score: {src.score.toFixed(2)}</span>
                        </div>
                        <p className="text-slate-600 dark:text-slate-300">{src.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </motion.div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
