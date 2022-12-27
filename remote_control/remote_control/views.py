'''
**********************************************************************
* Filename    : views
* Description : views for server
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-13    New release
**********************************************************************
'''

import ast
import cv2
import time
import requests
from datetime import datetime
from django.shortcuts import render_to_response
from .driver import camera, stream
from picar import back_wheels, front_wheels
from django.http import HttpResponse
import picar
from .picar_v_video_stream import Vilib

is_setup = False
is_capturing = False

def setup():
	global fw, bw, cam, SPEED, bw_status, is_setup, is_capturing
	if is_setup == True:
		return
	picar.setup()
	db_file = "/home/zilunpeng/spinning-wheel/SunFounder_PiCar-V/remote_control/remote_control/driver/config"
	fw = front_wheels.Front_Wheels(debug=True, db=db_file)
	bw = back_wheels.Back_Wheels(debug=False, db=db_file)
	cam = camera.Camera(debug=False, db=db_file)
	cam.ready()
	bw.ready()
	fw.ready()
	
	Vilib.camera_start()

	SPEED = 60
	bw_status = 0
	is_setup = True
	is_capturing = False

#test.start()
#print(stream.start())
def run_command(cmd):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result


def get_ip():
    _, result = run_command("hostname -I")
    ip = result.split(" ")
    return ip[0]


def home(request):
	return render_to_response("base.html")

def run(request):
	global SPEED, bw_status, is_capturing
	debug = ''
	if 'action' in request.GET:
		action = request.GET['action']
		if action == 'setup':
			setup()
		# ============== Back wheels =============
		elif action == 'bwready':
			bw.ready()
			bw_status = 0
		elif action == 'forward':
			bw.speed = SPEED
			bw.forward()
			bw_status = 1
			debug = "speed =", SPEED
		elif action == 'backward':
			bw.speed = SPEED
			bw.backward()
			bw_status = -1
		elif action == 'stop':
			bw.stop()
			bw_status = 0

		# ============== Front wheels =============
		elif action == 'fwready':
			fw.ready()
		elif action == 'fwleft':
			fw.turn_left()
		elif action == 'fwright':
			fw.turn_right()
		elif action == 'fwstraight':
			fw.turn_straight()
		elif 'fwturn' in action:
			print("turn %s" % action)
			fw.turn(int(action.split(':')[1]))
		
		# ================ Camera =================
		elif action == 'camready':
			cam.ready()
		elif action == "camleft":
			cam.turn_left(40)
		elif action == 'camright':
			cam.turn_right(40)
		elif action == 'camup':
			cam.turn_up(20)
		elif action == 'camdown':
			cam.turn_down(20)	

		if is_capturing:
			timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S-%f")[:-3]
			cur_speed = bw._speed
			if action == 'fwleft':
				left_angle = fw._angle['left']
				file_name = timestamp + f'-angle={left_angle}-speed={cur_speed}-bwstatus={bw_status}'
				cv2.imwrite(f'{Vilib.img_storage_path}/{file_name}.png', Vilib.img_array[0])
			elif action == 'fwright':
				right_angle = fw._angle['right']
				file_name = timestamp + f'-angle={right_angle}-speed={cur_speed}-bwstatus={bw_status}'
				cv2.imwrite(f'{Vilib.img_storage_path}/{file_name}.png', Vilib.img_array[0])
			elif action == 'fwstraight':
				straight_angle = fw._angle['straight']
				file_name = timestamp + f'-angle={straight_angle}-speed={cur_speed}-bwstatus={bw_status}'
				cv2.imwrite(f'{Vilib.img_storage_path}/{file_name}.png', Vilib.img_array[0])

	if 'speed' in request.GET:
		speed = int(request.GET['speed'])
		if speed < 0:
			speed = 0
		if speed > 100:
			speed = 100
		SPEED = speed
		if bw_status != 0:
			bw.speed = SPEED
		debug = "speed =", speed
	if 'start_capture' in request.GET:
		Vilib.camera_start_capture()
		is_capturing = True
	if 'stop_capture' in request.GET:
		Vilib.camera_stop_capture()
		is_capturing = False
	if 'start_model_control' in request.GET:
		bw.speed = 40
		start_time = time.time()
		while True:
			if len(Vilib.img_array) == 0:
				print('no image in the queue. Stop model control.')
				break
			cur_image = Vilib.img_array[0]
			_, cur_img_encoded = cv2.imencode('.jpg', cur_image)
			response = requests.post('http://172.20.10.3:8686/predict', data=cur_img_encoded.tostring(), headers={'content-type': 'image/jpeg'})
			if response.status_code != 200:
				print('request was not sent successfully.')
				break

			model_pred_dict = ast.literal_eval(response.content.decode('utf-8'))

			if model_pred_dict['model_pred_left'] >= 0.97:
				fw.turn_left()
				model_action = 'left'
			elif model_pred_dict['model_pred_right'] >= 0.97:
				fw.turn_right()
				model_action = 'right'
			else:
				model_action = 'no_action'
			time.sleep(0.25)
			fw.turn_straight()
			bw.forward()
			bw_status = 1

			timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S-%f")[:-3]
			file_name = timestamp + f'-model_action={model_action}'
			cv2.imwrite(f'{Vilib.img_storage_path}/{file_name}.png', cur_image)
			if time.time() - start_time > 120:
				print('more than 120 seconds. Stop.')
				break
			time.sleep(0.3)
	#host = stream.get_host().decode('utf-8').split(' ')[0]
	host = get_ip()
	return render_to_response("run.html", {'host': host})

def cali(request):
	if 'action' in request.GET:
		action = request.GET['action']
		# ========== Camera calibration =========
		if action == 'camcali':
			print('"%s" command received' % action)
			cam.calibration()
		elif action == 'camcaliup':
			print('"%s" command received' % action)
			cam.cali_up()
		elif action == 'camcalidown':
			print('"%s" command received' % action)
			cam.cali_down()
		elif action == 'camcalileft':
			print('"%s" command received' % action)
			cam.cali_left()
		elif action == 'camcaliright':
			print('"%s" command received' % action)
			cam.cali_right()
		elif action == 'camcaliok':
			print('"%s" command received' % action)
			cam.cali_ok()

		# ========= Front wheel cali ===========
		elif action == 'fwcali':
			print('"%s" command received' % action)
			fw.calibration()
		elif action == 'fwcalileft':
			print('"%s" command received' % action)
			fw.cali_left()
			print(fw.cali_turning_offset)
		elif action == 'fwcaliright':
			print('"%s" command received' % action)
			fw.cali_right()
		elif action == 'fwcaliok':
			print('"%s" command received' % action)
			fw.cali_ok()

		# ========= Back wheel cali ===========
		elif action == 'bwcali':
			print('"%s" command received' % action)
			bw.calibration()
		elif action == 'bwcalileft':
			print('"%s" command received' % action)
			bw.cali_left()
		elif action == 'bwcaliright':
			print('"%s" command received' % action)
			bw.cali_right()
		elif action == 'bwcaliok':
			print('"%s" command received' % action)
			bw.cali_ok()
		else:
			print('command error, error command "%s" received' % action)
	return render_to_response("cali.html")

def connection_test(request):
	return HttpResponse('OK')
