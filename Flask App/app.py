from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms = {}

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create_room():
    room_code = generate_room_code()
    embed_link = request.form['embed_link']
    rooms[room_code] = {
        'embed_link': embed_link,
        'controller': request.remote_addr,
        'state': 'pause',
        'time': 0
    }
    return redirect(url_for('room', room_code=room_code))

@app.route('/join', methods=['POST'])
def join_room_route():
    room_code = request.form['room_code']
    if room_code in rooms:
        return redirect(url_for('room', room_code=room_code))
    return "Room not found!", 404

@app.route('/room/<room_code>')
def room(room_code):
    if room_code in rooms:
        return render_template('room.html', room_code=room_code, embed_link=rooms[room_code]['embed_link'])
    return "Room not found!", 404

@socketio.on('join')
def handle_join(data):
    room_code = data['room']
    join_room(room_code)
    emit('message', {'msg': f"{request.remote_addr} has entered the room."}, to=room_code)
    emit('sync', rooms[room_code], to=request.sid)

@socketio.on('leave')
def handle_leave(data):
    room_code = data['room']
    leave_room(room_code)
    emit('message', {'msg': f"{request.remote_addr} has left the room."}, to=room_code)

@socketio.on('control')
def handle_control(data):
    room_code = data['room']
    if request.remote_addr == rooms[room_code]['controller']:
        rooms[room_code]['state'] = data['action']
        rooms[room_code]['time'] = data['time']
        emit('control', data, to=room_code)

if __name__ == '__main__':
    socketio.run(app, debug=True)
