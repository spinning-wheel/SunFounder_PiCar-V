import numpy as np
import cv2
import threading
import os
import time
from datetime import datetime
from flask import Flask, render_template, Response
from multiprocessing import Process, Manager

app = Flask(__name__)
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    while True:  

        frame = cv2.imencode('.jpg', Vilib.img_array[0])[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        

@app.route('/mjpg')
def video_feed():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 

def web_camera_start():
    app.run(host='0.0.0.0', port=8765,threaded=True)


class Vilib(object): 

    video_source = 0

    detect_obj_parameter = Manager().dict()
    img_array = Manager().list(range(2))
    rt_img = np.ones((320,240),np.uint8)     
    img_array[0] = rt_img
    img_storage_path = '/home/zilunpeng/storage'

    @staticmethod
    def camera_start(web_func = True):
        Vilib.worker_carcam = Process(name='worker 2', target=Vilib.camera_clone, args=(False,))
        Vilib.worker_carcam.daemon = True
        if web_func == True:
            Vilib.worker_webcam = Process(name='worker 1', target=web_camera_start)
            Vilib.worker_webcam.start()
        Vilib.worker_carcam.start()
    
    @staticmethod
    def camera_clone(should_capture):
        Vilib.camera(should_capture)     

    @staticmethod
    def camera(should_capture, front_wheel=None, back_wheel=None):
        camera = cv2.VideoCapture(Vilib.video_source)
        camera.set(3,320)
        camera.set(4,240)
        width = int(camera.get(3))
        height = int(camera.get(4))
        camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        cv2.setUseOptimized(True)
        while True:
            _, img = camera.read()
            Vilib.img_array[0] = img
            if should_capture:
                timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S-%f")[:-3]
                # file_name = timestamp + f'-turnOffset={front_wheel.}-'
                cv2.imwrite(f'{img_storage_path}/{timestamp}.png', img)
            time.sleep(0.5)

    @staticmethod
    def camera_start_capture(front_wheel, back_wheel):
        print(front_wheel)
        print(back_wheel)
        # terminate worker_1 process
        Vilib.worker_carcam.terminate()
        Vilib.worker_carcam.join()
        Vilib.worker_carcam.close()
        print('terminated worker_carcam')

        Vilib.worker_carcam = Process(name='worker 2', target=Vilib.camera_clone, args=(True,))
        Vilib.worker_carcam.daemon = True
        Vilib.worker_carcam.start()
        print('started new car cam process')

if __name__ == "__main__":
    Vilib.camera_start()
    while True:
        pass
