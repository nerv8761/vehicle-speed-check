import cv2
import dlib
import time
import threading
import math
import matplotlib.pyplot as plt
import numpy as np

carCascade = cv2.CascadeClassifier('myhaar.xml')
video = cv2.VideoCapture('2.mp4')

WIDTH = 2160
HEIGHT = 3840

def estimateSpeed(location1, location2):
	global d
	d_pixels = location2[1] +location2[3] - location1[1]-location1[3]
	if location2[1]+location2[3]<3258:
		ppm = 92
	if location2[1]+location2[3]>=3258 and location2[1]+location2[3]<3350:
		ppm = 92
		d = 5 - (location2[1] + location2[3] - 3258) / ppm
	if location2[1]+location2[3]>=3350 and location2[1]+location2[3]<3446:
		ppm = 96
		d = 4 - (location2[1] + location2[3] - 3350) / ppm
	if location2[1]+location2[3]>=3446 and location2[1]+location2[3]<3544:
		ppm = 98
		d = 3 - (location2[1] + location2[3] - 3446) / ppm
	if location2[1]+location2[3]>=3544 and location2[1]+location2[3]<3652:
		ppm = 108
		d = 2 - (location2[1] + location2[3] - 3544) / ppm
	if location2[1]+location2[3]>=3652 and location2[1]+location2[3]<=3762:
		ppm = 110
		d = 1 - (location2[1] + location2[3] - 3652) / ppm
	if location2[1]+location2[3]>3762:
		ppm = 110
	#ppm = location2[2] / 2.5
	#ppm = 18.18
	d_meters = d_pixels / ppm
	#print("d_pixels=" + str(d_pixels), "d_meters=" + str(d_meters))
	fps = 29.97
	speed = d_meters * fps * 3.6
	return speed,d





def trackMultipleObjects():
	rectangleColor = (0, 255, 0)
	frameCounter = 0
	currentCarID = 0
	fps = 0
	
	carTracker = {}
	carNumbers = {}
	carLocation1 = {}
	carLocation2 = {}
	speed = [None] * 1000
	
	# Write output to video file
	out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 29.97, (540,960))

	while True:
		global count,nb
		start_time = time.time()
		rc, image = video.read()
		if type(image) == type(None):
			break

		image = cv2.resize(image, (WIDTH, HEIGHT))
		resultImage = image.copy()
		
		frameCounter = frameCounter + 1
		
		carIDtoDelete = []

		for carID in carTracker.keys():
			trackingQuality = carTracker[carID].update(image)
			
			if trackingQuality < 7:
				carIDtoDelete.append(carID)
				
		for carID in carIDtoDelete:
			print ('Removing carID ' + str(carID) + ' from list of trackers.')
			print ('Removing carID ' + str(carID) + ' previous location.')
			print ('Removing carID ' + str(carID) + ' current location.')
			carTracker.pop(carID, None)
			carLocation1.pop(carID, None)
			carLocation2.pop(carID, None)
		
		if not (frameCounter % 10):
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			cars = carCascade.detectMultiScale(gray, 1.1, 80, 120, (100, 100))
			
			for (_x, _y, _w, _h) in cars:
				x = int(_x)
				y = int(_y)
				w = int(_w)
				h = int(_h)
			
				x_bar = x + 0.5 * w
				y_bar = y + 0.5 * h
				
				matchCarID = None
			
				for carID in carTracker.keys():
					trackedPosition = carTracker[carID].get_position()
					
					t_x = int(trackedPosition.left())
					t_y = int(trackedPosition.top())
					t_w = int(trackedPosition.width())
					t_h = int(trackedPosition.height())
					
					t_x_bar = t_x + 0.5 * t_w
					t_y_bar = t_y + 0.5 * t_h
				
					if ((t_x <= x_bar <= (t_x + t_w)) and (t_y <= y_bar <= (t_y + t_h)) and (x <= t_x_bar <= (x + w)) and (y <= t_y_bar <= (y + h))):
						matchCarID = carID
				
				if matchCarID is None:

					print ('Creating new tracker ' + str(currentCarID))
					tracker = dlib.correlation_tracker()
					tracker.start_track(image, dlib.rectangle(x, y, x + w, y + h))
					carTracker[currentCarID] = tracker
					carLocation1[currentCarID] = [x, y, w, h]
					currentCarID = currentCarID + 1
		
		cv2.line(resultImage,(0,3258),(2160,3258),(255,0,0),6)
		cv2.line(resultImage,(0,3762),(2160,3762),(255,0,0),6)

		for carID in carTracker.keys():

			trackedPosition = carTracker[carID].get_position()
			t_x = int(trackedPosition.left())
			t_y = int(trackedPosition.top())
			t_w = int(trackedPosition.width())
			t_h = int(trackedPosition.height())
			
			cv2.rectangle(resultImage, (t_x, t_y), (t_x + t_w, t_y + t_h), rectangleColor, 4)
			
			# speed estimation
			carLocation2[carID] = [t_x, t_y, t_w, t_h]

		end_time = time.time()
		if not (end_time == start_time):
			fps = 1.0/(end_time - start_time)
		#print(end_time-start_time,fps)
		
		#cv2.putText(resultImage, 'FPS: ' + str(int(fps)), (620, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)


		for i in carLocation1.keys():
			if frameCounter % 1 == 0:
				[x1, y1, w1, h1] = carLocation1[i]
				[x2, y2, w2, h2] = carLocation2[i]

				# print 'previous location: ' + str(carLocation1[i]) + ', current location: ' + str(carLocation2[i])
				carLocation1[i] = [x2, y2, w2, h2]
		
				# print 'new previous location: ' + str(carLocation1[i])
				#if [x1, y1, w1, h1] != [x2, y2, w2, h2]:
				y0 = y1 + h1
				#if (speed[i] == None or speed[i] == 0) and y0 >=570  and y0 <= 580:
				i
				if y0>=3258 and y0<=3762:
					speed[i],distance = estimateSpeed([x1, y1, w1, h1], [x2, y2, w2, h2])

					s1.append(speed[i])
					s3.append(speed[i])
					if len(s1)==15:
						del s1[0]
					if len(s3)==30:
						del s3[0]
					s2 = sum(s1) / len(s1)
					s4 = sum(s3) / len(s3)
					v2.append(speed[i])
					v5.append(distance)
					v1.append(s2)
					v4.append(s4)
					#print(velocity)
					cv2.putText(resultImage, str(int(s2)) + " km/h", (int(x1 + w1 / 2), int(y1 - 5)),cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 0), 6)

		t.append(end_time - start_time)
				#print(y2 + h2 >= y1 + h1,speed[i],nb)


					#print ('CarID ' + str(i) + ': speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')

					#else:
					#	cv2.putText(resultImage, "Far Object", (int(x1 + w1/2), int(y1)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

						#print ('CarID ' + str(i) + ' Location1: ' + str(carLocation1[i]) + ' Location2: ' + str(carLocation2[i]) + ' speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')
		resultImage = cv2.resize(resultImage, (540, 960))
		#cv2.imshow('result', resultImage)
		#Write the frame into the file 'output.avi'
		out.write(resultImage)


		if cv2.waitKey(33) == 27:
			break
	out.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':
	count = 0
	nb = 0
	s1 = []
	s3 = []
	v2 = []
	v1 = []
	v4 = []
	v5 = []
	t = []
	d = 0
	trackMultipleObjects()
	n = np.arange(0,len(v2),1) / 29.97

	plt.figure()
	plt.xlabel("t [s]")
	plt.ylabel("v [km/h]")
	plt.plot(n,v2, label='raw data')
	#plt.plot(n,v1, label='Noise-reduced data(0.5s)')
	plt.legend(loc = 'upper right')

	plt.figure()
	plt.xlabel("t [s]")
	plt.ylabel("v [km/h]")
	plt.plot(n, v2, label='raw data')
	plt.plot(n, v4, label='Noise-reduced data(1s)')
	plt.legend(loc = 'upper right')

	plt.figure()
	plt.xlabel("t [s]")
	plt.ylabel("d [m]")
	plt.plot(n, v5, label='raw data')
	plt.legend(loc = 'upper right')

	m1 = 0
	m2 = 0
	vv1 = 0
	vv2 = 0
	for i in range(120,150):
		m1=m1+v1[i]
		m2=m2+v4[i]

	mean1=m1/30
	mean2=m2/30

	for i in range(120,150):
		vv1=vv1+(v1[i]-mean1)*(v1[i]-mean1)
		vv2=vv2+(v4[i]-mean2)*(v4[i]-mean2)
	var1=vv1/30
	var2=vv2/30

	print(mean1)

	print(mean2)
	print(var1)
	print(var2)
	#plt.figure()
	#plt.xlabel("n")
	#plt.ylabel("t [s]")
	#plt.plot(t)

	plt.show()
