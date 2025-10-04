const startVideoCall = (roomName) => {
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');

    let localStream;
    let peerConnection;
    const config = {
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    };

    // Connect to WebSocket signaling server
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const signalingSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/videocall/${roomName}/`);

    signalingSocket.onmessage = async (message) => {
        const data = JSON.parse(message.data);

        if (!peerConnection) await startPeer();

        try {
            if (data.type === 'offer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data));
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                signalingSocket.send(JSON.stringify(peerConnection.localDescription));
            } else if (data.type === 'answer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data));
            } else if (data.type === 'candidate') {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        } catch (error) {
            console.error(error);
        }
    };

    signalingSocket.onopen = () => {
        startPeer();
    };

    async function startPeer() {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localVideo.srcObject = localStream;

        peerConnection = new RTCPeerConnection(config);

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                signalingSocket.send(JSON.stringify({ type: 'candidate', candidate: event.candidate }));
            }
        };

        peerConnection.ontrack = (event) => {
            remoteVideo.srcObject = event.streams[0];
        };

        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        signalingSocket.send(JSON.stringify(peerConnection.localDescription));
    }
};
