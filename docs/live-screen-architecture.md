# Live Screen Architecture

## Goal
Provide low-latency, permission-protected live viewing of QA station screens for incident supervision and investigation.

## Protocol Stack
- WebRTC for media transport
- Django Channels for signaling
- Redis for channel layer and fan-out
- coturn for STUN/TURN relay services
- HTTPS and internal CA certificates for browser security requirements

## Flow
1. QA station requests a live session.
2. Super Admin approves the request.
3. Station publishes media using WebRTC.
4. Viewer connects through a Channels websocket room.
5. Signaling messages are exchanged over the websocket.
6. All connect, disconnect, approval, and access attempts are logged.

## Security
- Only Super Admin may view live sessions.
- TURN authentication is required.
- Access is tied to audit records and session identifiers.
- Sessions expire and should be closed after the incident or supervision window ends.

## Scaling Notes
- Support multiple concurrent sessions by using one websocket room per station session.
- Keep media traffic off the API servers.
- Place coturn near the internal network edge for lower latency.
