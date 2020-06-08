import ctypes
import time

import cv2

from multiprocessing import Process, Pipe
from multiprocessing.sharedctypes import RawArray
from .AFrames import *
from .Draw import draw_frame, Drawer
from .FrameWriter import write_frame


def create_frame(settings, beatmap, replay_info, resultinfo, videotime, showranking):

	frames = PreparedFrames(settings, beatmap, Mod.Hidden in replay_info.mod_combination)

	if settings.process >= 1:
		shared_array = []
		shared_pipe = []
		drawers = []
		writers = []

		start_index, end_index = videotime

		osr_interval = int((end_index - start_index) / settings.process)
		start = start_index

		my_file = open(settings.temp + "listvideo.txt", "w")
		for i in range(settings.process):

			if i == settings.process - 1:
				end = end_index
			else:
				end = start + osr_interval

			shared = RawArray(ctypes.c_uint8, settings.height * settings.width * 4)
			conn1, conn2 = Pipe()

			# extract container
			f = "output" + str(i) + settings.output[-4:]

			vid = (start, end)

			drawer = Process(target=draw_frame, args=(
				shared, conn1, beatmap, frames, replay_info, resultinfo, vid, settings, showranking and i == settings.process-1))

			writer = Process(target=write_frame, args=(shared, conn2, settings.temp + f, settings, i == settings.process-1))

			shared_array.append(shared)
			shared_pipe.append((conn1, conn2))
			drawers.append(drawer)
			writers.append(writer)

			my_file.write("file '{}'\n".format(f))

			drawer.start()
			writer.start()

			start += osr_interval
		my_file.close()

		return drawers, writers, shared_pipe, shared_array


	else:

		print("process start")

		shared = RawArray(ctypes.c_uint8, settings.height * settings.width * 4)
		drawer = Drawer(shared, beatmap, frames, replay_info, resultinfo, videotime, settings)

		f = settings.temp + "outputf" + settings.output[-4:]
		writer = cv2.VideoWriter(f, cv2.VideoWriter_fourcc(*settings.codec), settings.fps, (settings.width, settings.height))

		print("setup done")
		framecount = 0
		startwritetime = time.time()
		while drawer.frame_info.osr_index < videotime[1]:
			status = drawer.render_draw()

			if status:
				im = cv2.cvtColor(drawer.np_img, cv2.COLOR_BGRA2RGB)
				writer.write(im)

				framecount += 1
				if framecount == 100:
					filewriter = open(settings.temp + "speed.txt", "w")
					deltatime = time.time() - startwritetime
					filewriter.write("{}\n{}\n{}\n{}".format(framecount, deltatime, f, startwritetime))
					filewriter.close()


		if showranking:
			for x in range(int(5 * settings.fps)):
				drawer.draw_rankingpanel()
				im = cv2.cvtColor(drawer.np_img, cv2.COLOR_BGRA2RGB)
				writer.write(im)
		writer.release()
		print("\nprocess done")

		return None, None, None, None