import { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';
import { API_URL } from '../config';

export const useSocket = () => {
    const [connected, setConnected] = useState(false);
    const socketRef = useRef(null);

    useEffect(() => {
        const socket = io(API_URL || window.location.origin, {
            path: '/socket.io',
            transports: ['websocket'],
            autoConnect: true,
            reconnection: true,
            reconnectionAttempts: 10
        });

        socket.on('connect', () => {
            console.log('Socket connected');
            setConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('Socket disconnected');
            setConnected(false);
        });

        // Listen for status events
        socket.on('status', (data) => {
            console.log('Status update:', data);
        });

        socketRef.current = socket;

        return () => {
            socket.disconnect();
        };
    }, []);

    return { socket: socketRef.current, connected };
};
