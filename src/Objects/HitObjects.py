from Objects.abstracts import *


hitcircle = "hitcircle.png"
hitcircleoverlay = "hitcircleoverlay.png"
sliderstartcircleoverlay = "sliderstartcircleoverlay.png"
sliderstartcircle = "sliderstartcircle.png"
approachcircle = "approachcircle.png"


class HitCircleNumber(Images):
	def __init__(self, filename, circle_radius, default_circle_size):
		Images.__init__(self, filename)
		self.scale = circle_radius * 2 / default_circle_size
		self.change_size(self.scale, self.scale)
		self.orig_img = np.copy(self.img)
		self.orig_rows = self.img.shape[0]
		self.orig_cols = self.img.shape[1]
		self.to_3channel()


class Number:
	def __init__(self, radius, path, default_circle_size):
		self.combo_number = []
		for x in range(10):
			self.combo_number.append(HitCircleNumber(path + "default-" + str(x) + ".png", radius, default_circle_size))

	def draw(self, circle, number, gap):
		"""
		:param circle: array of image circle
		:param number: number
		:param gap: distance between two digits
		"""
		number = str(number)
		size = gap * (len(number) - 1)  # image number size doesn't count because we are going to overlap them.
		x_pos = int((circle.shape[1] / 2) - (size / 2))
		y_pos = int(circle.shape[0] / 2)

		for digit in number:
			self.combo_number[int(digit)].add_to_frame(circle, x_pos, y_pos, 4)
			x_pos += gap


class ApproachCircle(ACircle):
	def __init__(self, filename, hitcircle_cols, hitcircle_rows, scale, time_preempt, interval):
		ACircle.__init__(self, filename, hitcircle_cols, hitcircle_rows)
		self.scale = scale
		self.time_preempt = round(time_preempt)
		self.interval = int(interval)
		self.approach_frames = []
		self.to_3channel()
		self.prepare_sizes()

	def prepare_sizes(self):
		scale = 3
		for time_left in range(self.time_preempt, 0, -self.interval):
			scale -= 2 * self.interval / self.time_preempt
			self.change_size(scale * self.scale, scale * self.scale)
			self.approach_frames.append(self.img)

	def add_to_frame(self, background, x_offset, y_offset, time_left):
		self.img = self.approach_frames[int((self.time_preempt - time_left) / self.interval)]
		super().add_to_frame(background, x_offset, y_offset)


class CircleOverlay(ACircle):
	def __init__(self, filename, hitcircle_cols, hitcircle_rows):
		ACircle.__init__(self, filename, hitcircle_cols, hitcircle_rows)


class SliderCircleOverlay(ACircle):
	def __init__(self, filename, hitcircle_cols, hitcircle_rows):
		ACircle.__init__(self, filename, hitcircle_cols, hitcircle_rows)


class CircleSlider(ACircle):
	def __init__(self, filename, hitcircle_cols, hitcircle_rows):
		ACircle.__init__(self, filename, hitcircle_cols, hitcircle_rows)


class PrepareCircles(Images):
	def __init__(self, slider_combo, path, diff, scale, maxcombo, gap, colors):
		"""
		:param path: str where is the skin folder
		:param diff: dict, contains ApproachRate, CircleSize, OverallDifficulty, HPDrain
		:param scale: float scale of current screen res with 512x384
		:param maxcombo: dict, biggest number we need to overlap, for preparing_circle, where we overlap every number with every circle
		:param gap: int, gap between 2 digits
		"""
		Images.__init__(self, path + hitcircle)
		self.overlay_filename = path + hitcircleoverlay
		self.slideroverlay_filename = path + sliderstartcircleoverlay
		self.diff = diff
		self.circles = []
		self.interval = 1000 / 60  # ms between 2 frames
		self.overlay_scale = 1.05
		self.ar = diff["ApproachRate"]
		self.cs = (54.4 - 4.48 * diff["CircleSize"]) * scale

		self.calculate_ar()
		self.load_circle()

		self.maxcolors = colors["ComboNumber"]
		self.colors = colors
		self.maxcombo = maxcombo
		self.gap = int(gap * self.radius_scale)

		self.slider_combo = slider_combo
		self.slider_circle = CircleSlider(path + sliderstartcircle, self.orig_cols, self.orig_rows)

		self.number_drawer = Number(self.cs * 0.9, path, self.default_circle_size)
		self.approachCircle = ApproachCircle(path + approachcircle, self.orig_cols, self.orig_rows, self.radius_scale,
		                                     self.time_preempt, self.interval)

		self.create_black_circle()

		self.circle_frames = []
		self.slidercircle_frames = []
		self.prepare_circle()

	def create_black_circle(self):
		# black support so that slider color won't affect hitcircleslider color cuz alpha when it begins to appear
		self.circle_supporter = np.copy(self.orig_img)
		self.add_color(self.circle_supporter, (0, 0, 0))
		tmp = self.orig_img
		self.orig_img = self.circle_supporter
		self.change_size(self.radius_scale, self.radius_scale, inter_type=cv2.INTER_LINEAR)
		self.circle_supporter = self.img
		self.orig_img = tmp
		self.img = np.copy(self.orig_img)
		cv2.addWeighted(self.circle_supporter, 1, self.circle_supporter, 1, 1, self.circle_supporter)  # increase opacity
		cv2.addWeighted(self.circle_supporter, 1, self.circle_supporter, 1, 1, self.circle_supporter)

	def calculate_ar(self):
		if self.ar < 5:
			self.time_preempt = 1200 + 600 * (5 - self.ar) / 5
			self.fade_in = 800 + 400 * (5 - self.ar) / 5
		elif self.ar == 5:
			self.time_preempt = 1200
			self.fade_in = 800
		else:
			self.time_preempt = 1200 - 750 * (self.ar - 5) / 5
			self.fade_in = 800 - 500 * (self.ar - 5) / 5
		self.opacity_interval = int(100 * self.interval / self.fade_in)

	def add_color(self, image, color):
		red = color[0]/255.0
		green = color[1]/255.0
		blue = color[2]/255.0
		image[:, :, 0] = np.multiply(image[:, :, 0], blue, casting='unsafe')
		image[:, :, 1] = np.multiply(image[:, :, 1], green, casting='unsafe')
		image[:, :, 2] = np.multiply(image[:, :, 2], red, casting='unsafe')
		image[image > 255] = 255

	def load_circle(self):
		self.overlay = CircleOverlay(self.overlay_filename, self.orig_cols, self.orig_rows)
		self.slidercircleoverlay = SliderCircleOverlay(self.slideroverlay_filename, self.orig_cols, self.orig_rows)
		cur_radius = self.orig_cols / 2
		self.radius_scale = self.cs * self.overlay_scale / cur_radius
		self.default_circle_size = self.orig_rows  # save for number class

	def overlayhitcircle(self, overlay, hitcircle_image):
		# still ned 4 channels so cannot do to_3channel before.
		y1, y2 = int(overlay.shape[0]/2 - hitcircle_image.shape[0]/2), int(overlay.shape[0]/2 + hitcircle_image.shape[0]/2)
		x1, x2 = int(overlay.shape[1]/2 - hitcircle_image.shape[1]/2), int(overlay.shape[1]/2 + hitcircle_image.shape[1]/2)
		ystart, yend = 0, hitcircle_image.shape[0]
		xstart, xend = 0, hitcircle_image.shape[1]

		alpha_s = overlay[y1:y2, x1:x2, 3] / 255.0
		alpha_l = 1 - alpha_s

		for c in range(3):
			overlay[y1:y2, x1:x2, c] = hitcircle_image[ystart:yend, xstart:xend, c] * alpha_l + \
			                              alpha_s * overlay[y1:y2, x1:x2, c]
		overlay[y1:y2, x1:x2, 3] = overlay[y1:y2, x1:x2, 3] + alpha_l * hitcircle_image[ystart:yend, xstart:xend, 3]

	def overlay_approach(self, background, x_offset, y_offset, circle_img, alpha):
		# still ned 4 channels so cannot do to_3channel before.
		y1, y2 = y_offset - int(circle_img.shape[0] / 2), y_offset + int(circle_img.shape[0] / 2)
		x1, x2 = x_offset - int(circle_img.shape[1] / 2), x_offset + int(circle_img.shape[1] / 2)

		y1, y2, ystart, yend = self.checkOverdisplay(y1, y2, background.shape[0])
		x1, x2, xstart, xend = self.checkOverdisplay(x1, x2, background.shape[1])

		alpha_s = background[y1:y2, x1:x2, 3] / 255.0
		alpha_l = 1 - alpha_s
		for c in range(3):
			background[y1:y2, x1:x2, c] = circle_img[ystart:yend, xstart:xend, c] * alpha_l + \
			                              background[y1:y2, x1:x2, c]
		background[y1:y2, x1:x2, 3] = background[y1:y2, x1:x2, 3] + circle_img[ystart:yend, xstart:xend, 3] * alpha_l
		background[:, :, :] = background[:, :, :] * (alpha/100)

	def to_3channel(self, image):
		# convert 4 channel to 3 channel, so we can ignore alpha channel, this will optimize the time of add_to_frame
		# where we needed to do each time alpha_s * img[:, :, 0:3]. Now we don't need to do it anymore
		alpha_s = image[:, :, 3] / 255.0
		for c in range(3):
			image[:, :, c] = (image[:, :, c] * alpha_s).astype(self.orig_img.dtype)

	def change_size2(self, img, new_col, new_row):
		n_rows = int(new_row * img.shape[1])
		n_rows -= int(n_rows % 2 == 1)  # need to be even
		n_cols = int(new_col * img.shape[0])
		n_cols -= int(n_cols % 2 == 1)  # need to be even
		return cv2.resize(img, (n_cols, n_rows), interpolation=cv2.INTER_LINEAR)

	def prepare_circle(self):
		# prepare every single frame before entering the big loop, this will save us a ton of time since we don't need
		# to overlap number, circle overlay and approach circle every single time.
		for c in range(1, self.maxcolors + 1):
			color = self.colors["Combo" + str(c)]

			orig_overlay_img = np.copy(self.overlay.img)
			orig_color_img = np.copy(self.orig_img)
			self.add_color(orig_color_img, color)
			self.overlayhitcircle(orig_overlay_img, orig_color_img)
			orig_overlay_img = self.change_size2(orig_overlay_img, self.radius_scale, self.radius_scale)
			self.to_3channel(orig_overlay_img)
			self.img = np.copy(orig_overlay_img)
			self.circle_frames.append([])

			orig_color_slider = np.copy(self.slider_circle.orig_img)
			orig_overlay_slider = np.copy(self.slidercircleoverlay.img)
			self.add_color(orig_color_slider, color)
			self.overlayhitcircle(orig_overlay_slider, orig_color_slider)
			orig_overlay_slider = self.change_size2(orig_overlay_slider, self.radius_scale, self.radius_scale)
			self.to_3channel(orig_overlay_slider)
			self.slider_circle.img = np.copy(orig_overlay_slider)
			self.slidercircle_frames.append({})   # so to find the right combo will be faster

			for x in range(1, self.maxcombo[c] + 1):
				self.number_drawer.draw(self.img, x, self.gap)

				if x in self.slider_combo:
					self.number_drawer.draw(self.slider_circle.img, x, self.gap)
					self.slidercircle_frames[-1][x] = []
				alpha = 0
				self.circle_frames[-1].append([])
				for i in range(len(self.approachCircle.approach_frames)):
					approach_circle = np.copy(self.approachCircle.approach_frames[i])
					self.add_color(approach_circle, color)
					x_offset = int(approach_circle.shape[1] / 2)
					y_offset = int(approach_circle.shape[0] / 2)

					if x in self.slider_combo:
						approach_slider = np.copy(approach_circle)
						self.overlay_approach(approach_slider, x_offset, y_offset, self.slider_circle.img, alpha)
						# approach_slider[:, :, 3] = approach_slider[:, :, 3] * (alpha / 100)
						# self.to_3channel(approach_slider)
						self.slidercircle_frames[-1][x].append(approach_slider)

					self.overlay_approach(approach_circle, x_offset, y_offset, self.img, alpha)
					# approach_circle[:, :, 3] = approach_circle[:, :, 3] * (alpha / 100)
					# self.to_3channel(approach_circle)

					self.circle_frames[-1][-1].append(approach_circle)
					alpha = min(100, alpha + self.opacity_interval)

				self.img = np.copy(orig_overlay_img)
				self.slider_circle.img = np.copy(orig_overlay_slider)
		print("done")
		del self.approachCircle

	def add_circle(self, x, y, combo_color, combo_number,  object_type=0):
		self.circles.append([x, y, self.time_preempt, -1, combo_color, combo_number, object_type])

	def add_to_frame(self, background, i):
		self.circles[i][2] -= self.interval
		self.circles[i][3] += 1
		color = self.circles[i][4] - 1
		number = self.circles[i][5]
		opacity_index = self.circles[i][3]
		if self.circles[i][6]:
			self.img = self.circle_supporter
			super().add_to_frame(background, self.circles[i][0], self.circles[i][1])
			self.img = self.slidercircle_frames[color][number][opacity_index]
		else:
			self.img = self.circle_frames[color][number - 1][opacity_index]
		super().add_to_frame(background, self.circles[i][0], self.circles[i][1])


class PrepareSlider:
	def __init__(self, slidermultiplier, time_preempt, opacity_interval, scale):
		self.sliders = []
		self.slidermutiplier = slidermultiplier
		self.time_preempt = time_preempt
		self.interval = 1000/60
		self.opacity_interval = opacity_interval
		self.scale = scale

	def add_slider(self, image, x_offset, y_offset, x_pos, y_pos, pixel_legnth, beat_duration):
		slider_duration = beat_duration * pixel_legnth / (100 * self.slidermutiplier)

		self.sliders.append([image, x_pos - x_offset, y_pos - y_offset, slider_duration + self.time_preempt, 0])

	# crop everything that goes outside the screen
	def checkOverdisplay(self, pos1, pos2, limit):
		start = 0
		end = pos2 - pos1
		if pos1 < 0:
			start = -pos1
			pos1 = 0
		if pos2 >= limit:
			end -= pos2 - limit + 1
			pos2 = limit - 1
		return pos1, pos2, start, end

	def to_frame(self, img, background, x_offset, y_offset):
		# to_3channel done in generate_slider.py
		y1, y2 = y_offset, y_offset + img.shape[0]
		x1, x2 = x_offset, x_offset + img.shape[1]

		y1, y2, ystart, yend = self.checkOverdisplay(y1, y2, background.shape[0])
		x1, x2, xstart, xend = self.checkOverdisplay(x1, x2, background.shape[1])
		alpha_s = img[ystart:yend, xstart:xend, 3] / 255.0
		alpha_l = 1.0 - alpha_s

		for c in range(3):
			background[y1:y2, x1:x2, c] = (
					img[ystart:yend, xstart:xend, c] + alpha_l * background[y1:y2, x1:x2, c])

	def add_to_frame(self, background, i):
		self.sliders[i][3] -= self.interval
		self.sliders[i][4] = min(100, self.sliders[i][4] + self.opacity_interval)
		cur_img = np.copy(self.sliders[i][0])
		cur_img[:, :, 0:3] = cur_img[:, :, 0:3] * (self.sliders[i][4]/100)
		self.to_frame(cur_img, background, self.sliders[i][1], self.sliders[i][2])


class HitObjectManager:
	def __init__(self, slider_combo, path, diff, scale, maxcombo, gap, colors):
		self.preparecircle = PrepareCircles(slider_combo, path, diff, scale, maxcombo, gap, colors)
		self.time_preempt = self.preparecircle.time_preempt
		self.prepareslider = PrepareSlider(diff["SliderMultiplier"], self.time_preempt, self.preparecircle.opacity_interval, scale)
		self.hitobject = []
		self.interval = 1000 / 60
		self.IS_CIRCLE = 0
		self.IS_CIRCLESLIDER = 1
		self.IS_SLIDER = 2

	def add_slider(self, image, x_offset, y_offset, x_pos, y_pos, pixel_legnth, beat_duration):
		self.prepareslider.add_slider(image, x_offset, y_offset, x_pos, y_pos, pixel_legnth, beat_duration)
		sliderduration = self.prepareslider.sliders[-1][3]
		self.hitobject.append([self.IS_SLIDER, sliderduration])

	def add_circle(self, x, y, combo_color, combo_number,  object_type=0):
		self.preparecircle.add_circle(x, y, combo_color, combo_number,  object_type)
		circleduration = self.time_preempt
		self.hitobject.append([object_type, circleduration])

	def add_to_frame(self, background):
		slider_index = len(self.prepareslider.sliders)
		circle_index = len(self.preparecircle.circles)
		i = len(self.hitobject) - 1

		while i > -1:
			self.hitobject[i][1] -= self.interval
			if self.hitobject[i][0] == self.IS_CIRCLE or self.hitobject[i][0] == self.IS_CIRCLESLIDER:
				circle_index -= 1
				if self.hitobject[i][1] < 0:
					del self.preparecircle.circles[circle_index]
					del self.hitobject[i]
					circle_index -= 1
					i -= 1
					continue
				self.preparecircle.add_to_frame(background, circle_index)
			else:
				slider_index -= 1
				if self.hitobject[i][1] < 0:
					del self.prepareslider.sliders[slider_index]
					del self.hitobject[i]
					slider_index -= 1
					i -= 1
					continue
				self.prepareslider.add_to_frame(background, slider_index)
			i -= 1

