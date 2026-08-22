import { useState, useRef, useEffect } from 'react';
import { transcribeAudio } from '../services/api';

export const useAudioRecorder = (onTranscript: (t: string) => void, onError: (e: string) => void, setAppState: (state: any) => void) => {
    const [recordingTime, setRecordingTime] = useState(0);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<number | null>(null);

    const MAX_RECORDING_TIME = 60;

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
                stream.getTracks().forEach((track) => track.stop());
                await handleUpload(audioBlob);
            };

            mediaRecorder.start();
            setAppState('LISTENING');
            setRecordingTime(0);

            timerRef.current = window.setInterval(() => {
                setRecordingTime((prev) => {
                    if (prev >= MAX_RECORDING_TIME) {
                        stopRecording();
                        return prev;
                    }
                    return prev + 1;
                });
            }, 1000);

        } catch (err) {
            console.error('Error accessing microphone:', err);
            onError('Could not access microphone. Please check permissions.');
            setAppState('ERROR');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            if (timerRef.current) clearInterval(timerRef.current);
        }
    };

    const handleUpload = async (audioBlob: Blob) => {
        setAppState('TRANSCRIBING');
        try {
            const response = await transcribeAudio(audioBlob);
            if (response && response.transcript) {
                onTranscript(response.transcript);
                setAppState('REVIEWING');
            } else {
                onError('Transcription empty or failed.');
                setAppState('ERROR');
            }
        } catch (err: any) {
            console.error('Upload error:', err);
            onError(err.response?.data?.detail || 'Failed to transcribe audio.');
            setAppState('ERROR');
        }
    };

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, []);

    return { startRecording, stopRecording, recordingTime };
};
