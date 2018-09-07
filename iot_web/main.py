import json
import eventlet
import paho.mqtt.client as mqtt
import time
from flask import Flask, render_template
from flask_socketio import SocketIO

eventlet.monkey_patch()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')
workerObject = None


class Worker(object):
    switch = False
    unit_of_work = 0

    def __init__(self, socket_io):
        self.socketio = socket_io
        self.switch = True

    def do_work(self):
        def on_message(client, userdata, message):
            dict_data = json.loads(message.payload.decode('utf-8'))
            dict_data['timestamp'] = str(int(time.time()))
            self.unit_of_work += 1
            self.socketio.emit("update", dict_data, namespace="/work")
            eventlet.sleep(1)
        broker_address = 'BROKER IP ADDRESS'
        mqtt_client = mqtt.Client('paho_client_{}'.format(str(int(time.time()))))  # create new instance
        mqtt_client.on_message = on_message  # attach function to callback
        mqtt_client.username_pw_set('USERNAME', 'PASSWORD')
        mqtt_client.connect(broker_address, 1883, 60)
        mqtt_client.subscribe('BROKER NAME')
        mqtt_client.loop_forever()

    def stop(self):
        self.switch = False


@app.route("/")
def index():
    return render_template('home.html')


@socketio.on('connect', namespace='/work')
def connect():
    global worker
    worker = Worker(socketio)
    socketio.emit("re_connect", {"msg": "connected"})


@socketio.on('start', namespace='/work')
def start_work():
    socketio.emit("update", {"msg": "starting worker"})
    socketio.start_background_task(target=worker.do_work)


@socketio.on('stop', namespace='/work')
def stop_work():
    worker.stop()
    socketio.emit("update", {"msg": "worker has been stopped"})


if __name__ == '__main__':
    socketio.run(app)
