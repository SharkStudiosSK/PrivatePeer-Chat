import os
import hashlib
import asyncio
import json
import websockets
import logging
from threading import Thread
from flask import Flask, request, render_template
from kademlia.network import Server
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder
from nacl.secret import SecretBox
from hkdf import hkdf_expand
from crypto_utils import derive_room_key, validate_peer
from tor_manager import start_tor, get_onion_address

APP_NAME = "PrivatePeer Chat"
VERSION = "1.0.0"
WS_PORT = 9000
WEB_PORT = 5000

app = Flask(__name__)
dht = Server()
connections = {}
user_identity = None

logging.basicConfig(level=logging.INFO)

class PeerSession:
    def __init__(self, websocket):
        self.websocket = websocket
        self.rooms = {}
        self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key
        self.peer_id = hashlib.sha256(self.verify_key.encode()).hexdigest()[:16]

async def handle_connection(websocket, path):
    session = PeerSession(websocket)
    try:
        # Exchange identity information
        await websocket.send(json.dumps({
            "type": "identity",
            "peer_id": session.peer_id,
            "verify_key": session.verify_key.encode(encoder=HexEncoder).decode()
        }))

        # Handle messages
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'join_room':
                await handle_room_join(session, data)
            elif data['type'] == 'message':
                await handle_message(session, data)

    except Exception as e:
        logging.error(f"Connection error: {e}")
    finally:
        for room_id in session.rooms:
            connections[room_id].discard(websocket)

async def handle_room_join(session, data):
    room_id = derive_room_key(data['secret']).hexdigest()
    session.rooms[room_id] = derive_room_key(data['secret'])
    
    # Publish to DHT
    await dht.set(f"room:{room_id}:{session.peer_id}", {
        "onion": get_onion_address(),
        "verify_key": session.verify_key.encode(encoder=HexEncoder).decode()
    })
    
    # Find existing peers
    peers = await dht.get(f"room:{room_id}:*")
    for peer in peers or []:
        if validate_peer(peer) and peer['peer_id'] != session.peer_id:
            await connect_to_peer(session, peer)

async def handle_message(session, data):
    room_id = data['room_id']
    if room_id in session.rooms:
        box = SecretBox(session.rooms[room_id])
        ciphertext = bytes.fromhex(data['ciphertext'])
        plaintext = box.decrypt(ciphertext).decode()
        
        # Broadcast to other peers
        for peer in connections.get(room_id, []):
            if peer != session.websocket:
                await peer.send(json.dumps({
                    "type": "message",
                    "room_id": room_id,
                    "sender": session.peer_id,
                    "ciphertext": data['ciphertext']
                }))

async def connect_to_peer(session, peer_data):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with websockets.connect(
                f"ws://{peer_data['onion']}:{WS_PORT}",
                socks_proxy="socks5://127.0.0.1:9050"
            ) as ws:
                connections.setdefault(peer_data['room_id'], set()).add(ws)
                await ws.send(json.dumps({
                    "type": "peer_handshake",
                    "peer_id": session.peer_id,
                    "verify_key": session.verify_key.encode(encoder=HexEncoder).decode()
                }))
                return
        except Exception as e:
            logging.error(f"Connection failed to {peer_data['onion']} on attempt {attempt + 1}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

def run_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(handle_connection, "0.0.0.0", WS_PORT)
    loop.run_until_complete(start_server)
    loop.run_forever()

@app.route('/')
def interface():
    return render_template('interface.html', name=APP_NAME, version=VERSION)

if __name__ == "__main__":
    start_tor()
    Thread(target=lambda: asyncio.run(dht.bootstrap([("127.0.0.1", 8468)]))).start()
    Thread(target=run_websocket_server).start()
    app.run(port=WEB_PORT)
