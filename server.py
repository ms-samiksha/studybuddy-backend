from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from face.capture_face import capture_face

app = Flask(__name__)
CORS(app, resources={r"/capture_face": {"origins": ["http://localhost", "http://127.0.0.1:5500", "https://your-app.netlify.app"]}})
socketio = SocketIO(app, cors_allowed_origins=["http://localhost", "http://127.0.0.1:5500", "https://your-app.netlify.app"])

@app.route("/capture_face", methods=["POST"])
def capture_face_endpoint():
    print("DEBUG: Received request to /capture_face")
    data = request.get_json()
    user_id = data.get("user_id")
    username = data.get("username")

    if not user_id or not username:
        print(f"DEBUG: Error: Missing user_id or username (user_id: {user_id}, username: {username})")
        return jsonify({"error": "User ID and username are required"}), 400

    try:
        print(f"DEBUG: Calling capture_face for user_id: {user_id}, username: {username}")
        image_path, error = capture_face(user_id, username)
        if image_path and os.path.exists(image_path):
            print(f"DEBUG: capture_face succeeded, image saved at: {image_path}")
            return jsonify({"message": "Face captured and saved", "image_path": image_path}), 200
        else:
            print(f"DEBUG: Error: capture_face failed - {error}")
            return jsonify({"error": error or "Failed to capture face, no image saved"}), 500
    except Exception as e:
        print(f"DEBUG: Error in capture_face_endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@socketio.on('join-room')
def on_join_room(data):
    room_id = data['roomId']
    user_id = data['userId']
    join_room(room_id)
    emit('user-joined', {'userId': user_id}, room=room_id, include_self=False)
    print(f"DEBUG: User {user_id} joined room {room_id}")

@socketio.on('leave-room')
def on_leave_room(data):
    room_id = data['roomId']
    user_id = data['userId']
    leave_room(room_id)
    emit('user-left', {'userId': user_id}, room=room_id)
    print(f"DEBUG: User {user_id} left room {room_id}")

@socketio.on('offer')
def on_offer(data):
    emit('offer', {
        'userId': data['userId'],
        'sdp': data['sdp']
    }, room=data['roomId'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', {
        'userId': data['userId'],
        'sdp': data['sdp']
    }, room=data['roomId'])

@socketio.on('ice-candidate')
def on_ice_candidate(data):
    emit('ice-candidate', {
        'userId': data['userId'],
        'candidate': data['candidate']
    }, room=data['roomId'])

if __name__ == "__main__":
    print("DEBUG: Starting Flask server on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    