import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  onRecordingComplete: (blob: Blob) => void;
  isProcessing: boolean;
}

export const VoiceRecorder: React.FC<Props> = ({ onRecordingComplete, isProcessing }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.current.push(e.data);
        }
      };

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        onRecordingComplete(audioBlob);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone", err);
      alert("Could not access the microphone. Please grant permission.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-slate-200 dark:border-dark-border">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        className={`relative w-24 h-24 rounded-full flex items-center justify-center text-white transition-colors ${
          isProcessing ? 'bg-slate-400 cursor-not-allowed' :
          isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-primary-600 hover:bg-primary-500'
        }`}
      >
        {isProcessing ? (
          <Loader2 className="w-10 h-10 animate-spin" />
        ) : isRecording ? (
          <Square className="w-10 h-10 fill-current" />
        ) : (
          <Mic className="w-10 h-10" />
        )}
        
        {isRecording && (
          <motion.div
            initial={{ scale: 1, opacity: 0.8 }}
            animate={{ scale: 1.5, opacity: 0 }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="absolute inset-0 bg-red-500 rounded-full z-[-1]"
          />
        )}
      </motion.button>
      
      <p className="mt-4 text-sm font-medium text-slate-500 dark:text-slate-400">
        {isProcessing ? 'Processing query...' : isRecording ? 'Tap to stop recording' : 'Tap to speak'}
      </p>
    </div>
  );
};
