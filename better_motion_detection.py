#!/usr/bin/python3

import config

import time
import smtplib

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput2, PyavOutput

from email.mime.text import MIMEText


lsize = (320, 240)
picam2 = Picamera2()
main = {"size": (1280, 720), "format": "RGB888"}
lores = {"size": lsize, "format": "YUV420"}
video_config = picam2.create_video_configuration(main, lores=lores)
picam2.configure(video_config)

duration = 2
encoder = H264Encoder(bitrate=1000000, repeat=True)
output = CircularOutput2(buffer_duration_ms=duration * 1000)
picam2.start_recording(encoder, output)

smtp = smtplib.SMTP_SSL(config.server_url, config.server_port)
smtp.set_debuglevel(1)
print("opening smtp - Done")

w, h = lsize
prev = None
encoding = False
ltime = 0
timestr = None

while True:
    cur = picam2.capture_array("lores")[:h, :w]
    if prev is not None:
        # Measure pixels difference between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        if mse > 7:
            if not encoding:
                timestr = time.strftime("%Y-%m-%d_%H%M%S%z")

                output.open_output(PyavOutput(f"rec_{timestr}.mp4"))
                encoding = True
                print("New Recording started: mse", mse)

            ltime = time.time()
        else:
            if encoding and time.time() - ltime > duration + 2.0:
                output.close_output()
                print("Recording stopped")
                encoding = False


                msg = MIMEText("Motion detected", _charset="utf-8")
                
                msg['Subject'] = f"Camera alert {timestr}"
                msg['From']    = config.send_from
                msg['To']      = config.send_to

                print("Logging in..")
                smtp.login(config.send_from, config.password)
                
                print("Sending..")
                smtp.sendmail(config.send_from, config.send_to, msg.as_string())

                print("Sending email - Done")
    prev = cur

smtp.close()