import hashlib
from hkdf import hkdf_expand

def derive_room_key(secret):
    return hkdf_expand(secret.encode(), b'ppchat-room-key', 32)

def validate_peer(peer_data):
    required_fields = ['onion', 'verify_key', 'peer_id']
    return all(field in peer_data for field in required_fields)

def generate_fingerprint(key):
    return hashlib.sha256(key.encode()).hexdigest()[:16]