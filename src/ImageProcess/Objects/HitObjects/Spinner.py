from recordclass import recordclass

from ImageProcess import imageproc
from ImageProcess.Objects.FrameObject import FrameObject

spinnercircle = "spinner-circle"
spinnerbackground = "spinner-background"
spinnerbottom = "spinner-bottom"
spinnerspin = "spinner-spin"
spinnermetre = "spinner-metre"
spinnerapproachcircle = "spinner-approachcircle"
spinnertop = "spinner-top"


Spinner = recordclass("Spinner", "angle duration starttime_left alpha index")


class SpinnerManager(FrameObject):
	def __init__(self, frames, settings):
		super().__init__(frames)
		self.moveright = settings.moveright
		self.movedown = settings.movedown
		self.scale = settings.playfieldscale
		self.spinners = {}

		self.interval = settings.timeframe / settings.fps
		self.timer = 0

	def add_spinner(self, starttime, endtime, curtime):
		duration = endtime - starttime
		# img, duration, startime left, alpha, index, progress
		self.spinners[str(starttime) + "o"] = Spinner(0, duration, starttime - curtime, 0, 0)

	def update_spinner(self, timestamp, angle, progress):
		# angle = round(angle * 0.9)
		# n_rot = int(angle/90)
		# index = int(angle - 90*n_rot)
		# n_rot = n_rot % 4 + 1

		self.spinners[timestamp].angle = angle
		# if n_rot != 1:
		# 	self.spinners[timestamp][0] = self.spinners[timestamp][0].transpose(n_rot)

		progress = progress * 10
		if 0.3 < progress - int(progress) < 0.35 or 0.6 < progress - int(progress) < 0.65:
			progress -= 1

		self.spinners[timestamp][4] = min(10, int(progress))

	def add_to_frame(self, background, i, alone):
		if self.spinners[i].starttime_left > 0:
			self.spinners[i].starttime_left -= self.interval
			self.spinners[i].alpha = min(1, self.spinners[i].alpha + self.interval / 400)
		else:
			self.spinners[i].duration -= self.interval
			if 0 > self.spinners[i].duration > -200:
				self.spinners[i].alpha = max(0, self.spinners[i].alpha - self.interval / 200)
			else:
				self.spinners[i].alpha = 1

		img = self.frames[spinnerbackground]
		imageproc.add(img, background,  background.size[0]//2, background.size[1]//2, alpha=self.spinners[i].alpha)

		img = self.frames[spinnercircle].rotate(self.spinners[i].angle)
		imageproc.add(img, background, background.size[0] // 2, int(198.5 * self.scale) + self.movedown, alpha=self.spinners[i].alpha)

		height = self.frames[spinnermetre].size[1]
		y_start = height - self.spinners[i].index * height // 10
		width = self.frames[spinnermetre].size[0]
		img = self.frames[spinnermetre].crop((0, y_start, width, height))
		imageproc.add(img, background, background.size[0]//2, 46 + img.size[1]//2 + y_start, alpha=self.spinners[i].alpha)

