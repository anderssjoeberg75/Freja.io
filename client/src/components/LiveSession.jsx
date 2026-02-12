import { useEffect, useRef, useState } from 'react';
import { API_URL } from '../config';

const WS_URL = API_URL.replace(/^http/, 'ws');

function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    for (let i = 0; i < float32Array.length; i += 1) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        offset += 2;
    }
    return new Uint8Array(buffer);
}

function base64FromBytes(bytes) {
    let binary = '';
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
}

function bytesFromBase64(base64) {
    const bin = atob(base64);
    const len = bin.length;
    const arr = new Uint8Array(len);
    for (let i = 0; i < len; i += 1) arr[i] = bin.charCodeAt(i);
    return arr;
}

function LiveSession() {
    const [connected, setConnected] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [cameraEnabled, setCameraEnabled] = useState(true);
    const [status, setStatus] = useState('idle');
    const [fps, setFps] = useState(0);
    const [audioLevel, setAudioLevel] = useState(0);
    const [toolActivity, setToolActivity] = useState('none');

    const wsRef = useRef(null);
    const micStreamRef = useRef(null);
    const videoStreamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    const audioContextRef = useRef(null);
    const playbackQueueRef = useRef([]);
    const isPlayingRef = useRef(false);

    const frameIntervalRef = useRef(null);
    const fpsCounterRef = useRef({ count: 0, timer: null });

    const stopAll = () => {
        setStreaming(false);
        setConnected(false);
        setStatus('stopped');

        if (frameIntervalRef.current) {
            clearInterval(frameIntervalRef.current);
            frameIntervalRef.current = null;
        }

        if (fpsCounterRef.current.timer) {
            clearInterval(fpsCounterRef.current.timer);
            fpsCounterRef.current.timer = null;
        }

        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }

        if (micStreamRef.current) {
            micStreamRef.current.getTracks().forEach((t) => t.stop());
            micStreamRef.current = null;
        }
        if (videoStreamRef.current) {
            videoStreamRef.current.getTracks().forEach((t) => t.stop());
            videoStreamRef.current = null;
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    const playNext = async () => {
        if (!audioContextRef.current || isPlayingRef.current || playbackQueueRef.current.length === 0) return;
        isPlayingRef.current = true;

        const bytes = playbackQueueRef.current.shift();
        const samples = new Int16Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 2);
        const floatData = new Float32Array(samples.length);
        for (let i = 0; i < samples.length; i += 1) {
            floatData[i] = samples[i] / 0x8000;
        }

        const sourceRate = 24000;
        const targetRate = audioContextRef.current.sampleRate;
        const ratio = sourceRate / targetRate;
        const outLength = Math.floor(floatData.length / ratio);
        const out = audioContextRef.current.createBuffer(1, outLength, targetRate);
        const ch = out.getChannelData(0);
        for (let i = 0; i < outLength; i += 1) {
            ch[i] = floatData[Math.floor(i * ratio)] || 0;
        }

        const src = audioContextRef.current.createBufferSource();
        src.buffer = out;
        src.connect(audioContextRef.current.destination);
        src.onended = () => {
            isPlayingRef.current = false;
            setTimeout(playNext, 0);
        };
        src.start();
    };

    const startSession = async () => {
        try {
            setStatus('starting');
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();

            const micStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1,
                },
                video: false,
            });
            micStreamRef.current = micStream;

            if (cameraEnabled) {
                const camStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                videoStreamRef.current = camStream;
                if (videoRef.current) {
                    videoRef.current.srcObject = camStream;
                    await videoRef.current.play();
                }
            }

            const ws = new WebSocket(`${WS_URL}/ws/live`);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                setStreaming(true);
                setStatus('connected');
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                if (message.type === 'audio_chunk_down' && message.audio) {
                    playbackQueueRef.current.push(bytesFromBase64(message.audio));
                    playNext();
                } else if (message.type === 'status') {
                    setStatus(message.status || 'status');
                } else if (message.type === 'transcript') {
                    setStatus(`transcript: ${message.text}`);
                } else if (message.type === 'tool_call') {
                    setToolActivity(`call: ${message.name}`);
                } else if (message.type === 'tool_result') {
                    setToolActivity(`result: ${message.name}`);
                } else if (message.type === 'error') {
                    setStatus(`error: ${message.message}`);
                }
            };

            ws.onerror = () => setStatus('ws_error');
            ws.onclose = () => stopAll();

            // Capture microphone audio using WebAudio and send 30ms PCM16 chunks.
            const source = audioContextRef.current.createMediaStreamSource(micStream);
            const processor = audioContextRef.current.createScriptProcessor(2048, 1, 1);
            source.connect(processor);
            processor.connect(audioContextRef.current.destination);

            let sampleBucket = [];
            processor.onaudioprocess = (e) => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                const input = e.inputBuffer.getChannelData(0);
                const level = Math.min(1, input.reduce((a, v) => a + Math.abs(v), 0) / input.length * 3);
                setAudioLevel(level);

                const inRate = audioContextRef.current.sampleRate;
                const outRate = 16000;
                const ratio = inRate / outRate;
                const resampledLength = Math.floor(input.length / ratio);
                const resampled = new Float32Array(resampledLength);
                for (let i = 0; i < resampledLength; i += 1) {
                    resampled[i] = input[Math.floor(i * ratio)] || 0;
                }

                sampleBucket.push(...resampled);
                const chunkSamples = Math.floor(outRate * 0.03);
                while (sampleBucket.length >= chunkSamples) {
                    const frame = new Float32Array(sampleBucket.slice(0, chunkSamples));
                    sampleBucket = sampleBucket.slice(chunkSamples);
                    const pcm = floatTo16BitPCM(frame);
                    wsRef.current.send(JSON.stringify({ type: 'audio_chunk_up', audio: base64FromBytes(pcm) }));
                }
            };

            // Send JPEG frames approximately once per second.
            if (cameraEnabled) {
                fpsCounterRef.current.count = 0;
                fpsCounterRef.current.timer = setInterval(() => {
                    setFps(fpsCounterRef.current.count);
                    fpsCounterRef.current.count = 0;
                }, 1000);

                frameIntervalRef.current = setInterval(() => {
                    if (!videoRef.current || !canvasRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                    const video = videoRef.current;
                    const canvas = canvasRef.current;
                    const width = video.videoWidth || 640;
                    const height = video.videoHeight || 360;
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(video, 0, 0, width, height);
                    const jpgDataUrl = canvas.toDataURL('image/jpeg', 0.6);
                    const image = jpgDataUrl.split(',')[1];
                    wsRef.current.send(JSON.stringify({ type: 'video_frame_up', image, ts: Date.now() }));
                    fpsCounterRef.current.count += 1;
                }, 1000);
            }
        } catch (error) {
            setStatus(`start_failed: ${error.message}`);
            stopAll();
        }
    };

    useEffect(() => () => stopAll(), []);

    return (
        <div className="p-8 space-y-6">
            <h2 className="text-2xl font-bold">Live Voice + Vision</h2>

            <div className="flex gap-3">
                <button onClick={startSession} disabled={streaming} className="px-4 py-2 rounded bg-mainframe-accent text-black disabled:opacity-40">Start Live Session</button>
                <button onClick={stopAll} disabled={!streaming} className="px-4 py-2 rounded bg-zinc-700 text-white disabled:opacity-40">Stop Live Session</button>
                <button onClick={() => setCameraEnabled((v) => !v)} className="px-4 py-2 rounded bg-zinc-800 text-white">
                    Camera: {cameraEnabled ? 'On' : 'Off'}
                </button>
            </div>

            <div className="text-sm text-zinc-300 space-y-1">
                <div>Connected: {connected ? 'yes' : 'no'}</div>
                <div>Streaming: {streaming ? 'yes' : 'no'}</div>
                <div>Status: {status}</div>
                <div>FPS: {fps}</div>
                <div>Audio level: {(audioLevel * 100).toFixed(0)}%</div>
                <div>Tool activity: {toolActivity}</div>
            </div>

            <video ref={videoRef} className="w-full max-w-xl rounded border border-mainframe-border" muted playsInline />
            <canvas ref={canvasRef} className="hidden" />
        </div>
    );
}

export default LiveSession;
