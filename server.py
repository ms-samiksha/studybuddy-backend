# Ensure eventlet monkey patching is applied before other imports
import eventlet
eventlet.monkey_patch()

# Import modules
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://dainty-longma-fd7059.netlify.app"}})
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="https://dainty-longma-fd7059.netlify.app")

# Initialize Firebase Admin SDK
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "token_uri": "https://oauth2.googleapis.com/token"
})
firebase_admin.initialize_app(cred)
db = firestore.client()

# Flask routes
@app.route('/join-room', methods=['POST'])
def join_room_http():
    try:
        data = request.get_json()
        room_id = data.get('roomId')
        user_id = data.get('userId')
        user_name = data.get('userName', f'User_{user_id[:5]}')
        if not room_id or not user_id:
            return jsonify({'error': 'Missing roomId or userId'}), 400

        room_ref = db.collection('rooms').document(room_id)
        if not room_ref.get().exists:
            return jsonify({'error': 'Room does not exist'}), 404

        room_members_ref = db.collection('rooms').document(room_id).collection('room_members')
        existing = room_members_ref.where('userId', '==', user_id).get()
        for doc in existing[1:]:
            doc.reference.delete()

        room_members_ref.document(user_id).set({
            'userId': user_id,
            'userName': user_name,
            'joinedAt': datetime.now()
        }, merge=True)
        return jsonify({'message': 'Joined room'}), 200
    except Exception as e:
        print(f"ERROR: Failed to join room: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/leave-room', methods=['POST'])
def leave_room_http():
    try:
        data = request.get_json()
        room_id = data.get('roomId')
        user_id = data.get('userId')
        if not room_id or not user_id:
            return jsonify({'error': 'Missing roomId or userId'}), 400

        db.collection('rooms').document(room_id).collection('room_members').document(user_id).delete()
        return jsonify({'message': 'Left room'}), 200
    except Exception as e:
        print(f"ERROR: Failed to leave room: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Socket.IO events
@socketio.on('join-room')
def on_join_room(data):
    room_id = data['roomId']
    user_id = data['userId']
    join_room(room_id)
    emit('user-joined', {'userId': user_id}, room=room_id, include_self=False)
    print(f"DEBUG: User {user_id} joined room {room_id}, broadcasting to {room_id}")

@socketio.on('leave-room')
def on_leave_room(data):
    room_id = data['roomId']
    user_id = data['userId']
    leave_room(room_id)
    emit('user-left', {'userId': user_id}, room=room_id, include_self=False)
    print(f"DEBUG: User {user_id} left room {room_id}")

@socketio.on('offer')
def on_offer(data):
    print(f"DEBUG: Received offer from user {data['userId']} for room {data['roomId']}, SDP: {data['sdp'].type}")
    emit('offer', {
        'userId': data['userId'],
        'sdp': data['sdp']
    }, room=data['roomId'], include_self=False)
    print(f"DEBUG: Broadcasted offer to room {data['roomId']}")

@socketio.on('answer')
def on_answer(data):
    print(f"DEBUG: Received answer from user {data['userId']} for room {data['roomId']}, SDP: {data['sdp'].type}")
    emit('answer', {
        'userId': data['userId'],
        'sdp': data['sdp']
    }, room=data['roomId'], include_self=False)
    print(f"DEBUG: Broadcasted answer to room {data['roomId']}")

@socketio.on('ice-candidate')
def on_ice_candidate(data):
    print(f"DEBUG: Received ICE candidate from user {data['userId']} for room {data['roomId']}, Candidate: {data['candidate'].candidate}")
    emit('ice-candidate', {
        'userId': data['userId'],
        'candidate': data['candidate']
    }, room=data['roomId'], include_self=False)
    print(f"DEBUG: Broadcasted ICE candidate to room {data['roomId']}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"DEBUG: Starting Flask server on http://0.0.0.0:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)