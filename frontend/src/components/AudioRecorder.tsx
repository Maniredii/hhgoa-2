import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { transcribeAudio } from '../services/api';

interface AudioRecorderProps {
    onTranscript: (transcript: string) => void;
    onError: (error: string) => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ onTranscript, onError }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<number | null>(null);

    // Stop recording automatically after 60 seconds
    const MAX_RECORDING_TIME = 60;

    useEffect(() => {
        if (isRecording) {
            timerRef.current = window.setInterval(() => {
                setRecordingTime((prev) => {
                    if (prev >= MAX_RECORDING_TIME) {
                        stopRecording();
                        return prev;
                    }
                    return prev + 1;
                });
            }, 1000);
        } else {
            if (timerRef.current) clearInterval(timerRef.current);
            setRecordingTime(0);
        }
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [isRecording]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                // Clean up tracks
                stream.getTracks().forEach((track) => track.stop());
                
                await handleUpload(audioBlob);
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Error accessing microphone:', err);
            onError('Could not access microphone. Please check permissions.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleUpload = async (audioBlob: Blob) => {
        setIsTranscribing(true);
        try {
            const response = await transcribeAudio(audioBlob);
            if (response && response.transcript) {
                onTranscript(response.transcript);
            } else {
                onError('Transcription empty or failed.');
            }
        } catch (err: any) {
            console.error('Upload error:', err);
            onError(err.response?.data?.detail || 'Failed to transcribe audio.');
        } finally {
            setIsTranscribing(false);
        }
    };

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <div className="flex items-center gap-3">
            {isRecording ? (
                <button
                    onClick={stopRecording}
                    className="flex items-center justify-center p-3 rounded-full bg-red-500 hover:bg-red-600 text-white shadow-lg transition-transform hover:scale-105 active:scale-95 animate-pulse"
                    title="Stop Recording"
                >
                    <Square size={20} className="fill-current" />
                </button>
            ) : isTranscribing ? (
                <button
                    disabled
                    className="flex items-center justify-center p-3 rounded-full bg-slate-200 text-slate-500 shadow-md cursor-not-allowed"
                    title="Transcribing..."
                >
                    <Loader2 size={20} className="animate-spin" />
                </button>
            ) : (
                <button
                    onClick={startRecording}
                    className="flex items-center justify-center p-3 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg transition-transform hover:scale-105 active:scale-95"
                    title="Start Voice Input"
                >
                    <Mic size={20} />
                </button>
            )}
            
            {isRecording && (
                <span className="text-red-500 font-medium text-sm tracking-widest">
                    {formatTime(recordingTime)}
                </span>
            )}
            {isTranscribing && (
                <span className="text-indigo-600 font-medium text-sm animate-pulse">
                    Transcribing...
                </span>
            )}
        </div>
    );
};
