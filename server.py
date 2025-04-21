# Ensure eventlet monkey patching is applied before any other imports
import eventlet
eventlet.monkey_patch()

# Now import other modules
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost", "http://127.0.0.1:5500", "https://dainty-longma-fd7059.netlify.app"]}})
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=[
    "http://localhost",
    "http://127.0.0.1:5500",
    "https://dainty-longma-fd7059.netlify.app"
])

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

if __name__ == "__main__":
    print("DEBUG: Starting Flask server on http://0.0.0.0:10000")
    socketio.run(app, host="0.0.0.0", port=10000, debug=False)