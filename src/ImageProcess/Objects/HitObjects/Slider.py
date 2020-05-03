import cv2
from recordclass import recordclass

from PIL import Image

from ImageProcess import imageproc
from ImageProcess.Curves.generate_slider import GenerateSlider
from ImageProcess.Curves.curve import *

from ImageProcess.PrepareFrames.HitObjects.Circles import calculate_ar

Slider = recordclass("Slider", "image x y cur_duration opacity color sliderb_i orig_duration bezier_info "
                               "cur_repeated repeated appear_f tick_a arrow_i baiser arrow_pos")


class SliderManager:
	def __init__(self, frames, diff, skin, settings):
		self.settings = settings

		self.reversearrow, self.sliderb_frames, self.sliderfollow_fadeout, self.slidertick = frames
		self.slidermax_index = len(self.sliderfollow_fadeout) - 1

		self.divide_by_255 = 1 / 255.0

		self.arrows = {}
		self.sliders = {}

		self.cs = (54.4 - 4.48 * diff["CircleSize"])

		self.sliderborder = skin.colours["SliderBorder"]
		self.slideroverride = skin.colours["SliderTrackOverride"]
		self.gs = GenerateSlider(self.sliderborder, self.slideroverride, self.cs, settings.playfieldscale)

		self.ar = diff["ApproachRate"]
		self.slidermutiplier = diff["SliderMultiplier"]

		self.interval = settings.timeframe / settings.fps
		self.opacity_interval, self.time_preempt, _ = calculate_ar(self.ar, settings)
		self.timer = 0

	def get_arrow(self, osu_d):
		pos1 = osu_d["ps"][-1]
		pos2 = osu_d["ps"][-2] if osu_d["ps"][-2].x != pos1.x or osu_d["ps"][-2].y != pos1.y else osu_d["ps"][-3]

		pos3 = osu_d["ps"][0]
		pos4 = osu_d["ps"][1] if osu_d["ps"][1].x != pos3.x or osu_d["ps"][1].y != pos3.y else osu_d["ps"][2]

		vector_x1, vector_y1 = pos2.x - pos1.x, pos2.y - pos1.y
		vector_x2, vector_y2 = pos4.x - pos3.x, pos4.y - pos3.y

		angle1 = -np.arctan2(vector_y1, vector_x1) * 180 / np.pi
		angle2 = -np.arctan2(vector_y2, vector_x2) * 180 / np.pi

		img1 = imageproc.rotate_images(self.reversearrow, angle1)
		img2 = imageproc.rotate_images(self.reversearrow, angle2)
		return img1, img2
	
	def get_slider_img(self, b_info):
		image, x_offset, y_offset = self.gs.get_slider_img(*b_info[0:3])
		image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
		return Image.fromarray(image), x_offset, y_offset

	def add_slider(self, osu_d, x_pos, y_pos, cur_time):
		pixel_length, color = osu_d["pixel length"], osu_d["combo_color"]

		# bezier info to calculate curve for sliderball. Actually the first three info is needed for the curve computing
		# function, but we add stack to reduce sliders list size
		b_info = (osu_d["slider type"], osu_d["ps"], pixel_length, osu_d["stacking"], osu_d["slider ticks"], osu_d["ticks pos"])

		img, x_offset, y_offset = self.get_slider_img(b_info)
		
		x_pos -= x_offset
		y_pos -= y_offset

		duration = osu_d["duration"] + osu_d["time"] - cur_time

		ticks_a = [0] * len(osu_d["slider ticks"])

		baiser = Curve.from_kind_and_points(*b_info[0:3])

		key = str(osu_d["time"]) + "s"
		self.sliders[key] = Slider(img, x_pos, y_pos, duration, 0, color, self.slidermax_index, osu_d["duration"], b_info,
		                           1, osu_d["repeated"], 0, ticks_a, 0, baiser, osu_d["arrow pos"])

		img1, img2 = self.get_arrow(osu_d)
		self.arrows[key] = [img2, img1]

	def draw_slider(self, img, background, x_offset, y_offset, alpha=1.0):
		a = img
		if 0 < alpha < 1:
			a = img.getchannel("A")
			a = a.point(lambda i: i * alpha)
		if alpha == 0:
			return
		background.paste(img, (x_offset, y_offset), a)

	def to_frame(self, img, background, pos, slider, alpha=1.0):
		x = int((pos.x + slider.bezier_info[3]) * self.settings.playfieldscale) + self.settings.moveright
		y = int((pos.y + slider.bezier_info[3]) * self.settings.playfieldscale) + self.settings.movedown

		imageproc.add(img, background, x, y, alpha=alpha)

	def draw_sliderb(self, slider, background, t):
		if slider.bezier_info[0] != "L":
			cur_pos = slider.baiser(round(t, 3))
		else:
			sum_x = (1 - t) * slider.bezier_info[1][0].x + t * slider.arrow_pos.x
			sum_y = (1 - t) * slider.bezier_info[1][0].y + t * slider.arrow_pos.y
			cur_pos = Position(sum_x, sum_y)
		color = slider.color - 1
		index = int(slider.sliderb_i)
		self.to_frame(self.sliderb_frames[color][index], background, cur_pos, slider)
		slider.sliderb_i = max(0, min(self.slidermax_index, slider.sliderb_i + slider.appear_f))

	def draw_arrow(self, slider, background, going_forward, i):
		cur_pos = slider.arrow_pos if going_forward else slider.bezier_info[1][0]
		self.to_frame(self.arrows[i][int(going_forward)][int(slider.arrow_i)], background, cur_pos, slider,
		              slider.opacity / 100)

		slider.arrow_i += 0.6
		if slider.arrow_i >= len(self.arrows[i][0]):
			slider.arrow_i = 0

	def draw_ticks(self, slider, background, going_forward, t):
		for count, tick_t in enumerate(slider.bezier_info[4]):
			if slider.cur_repeated == slider.repeated:
				if (going_forward and t > tick_t) or (not going_forward and t < tick_t):
					continue

			if slider.cur_duration < slider.orig_duration + 100:
				if count == 0 or slider.tick_a[count - 1] >= 0.75:
					slider.tick_a[count] = min(1, slider.tick_a[count] + 0.1)
			tick_pos = slider.bezier_info[5][count]
			self.to_frame(self.slidertick, background, tick_pos, slider, alpha=slider.opacity*slider.tick_a[count]/100)

	def add_to_frame(self, background, i, _):
		slider = self.sliders[i]

		slider.cur_duration -= self.interval
		baiser = slider.baiser

		# if sliderball is going forward
		going_forward = slider.cur_repeated % 2 == 1

		if slider.cur_duration <= 0:
			# if the slider is repeated
			if slider.cur_repeated < slider.repeated:
				slider.cur_duration = slider.orig_duration  # reset
				slider.cur_repeated += 1
				going_forward = not going_forward

			else:
				cur_pos = baiser(int(going_forward))  # if going_foward is true then t = 1 otherwise it's 0
				index = int(slider.sliderb_i)
				self.to_frame(self.sliderfollow_fadeout[index], background, cur_pos, slider)

				# frame to make the sliderfollowcircle smaller, but it's smalling too fast so instead of increase index
				# by 1, we increase it by 0.65 then convert it to integer. So some frames would appear twice.
				slider.sliderb_i = max(0, min(self.slidermax_index, slider.sliderb_i + slider.appear_f))

				slider.opacity = max(-self.opacity_interval, slider.opacity - 4 * self.opacity_interval)

		slider.opacity = min(100, slider.opacity + self.opacity_interval)
		self.draw_slider(slider.image, background, slider.x, slider.y, alpha=slider.opacity/100)

		t = slider.cur_duration / slider.orig_duration

		# if sliderball is going forward
		if going_forward:
			t = 1 - t

		self.draw_ticks(slider, background, going_forward, t)

		if 0 < slider.cur_duration <= slider.orig_duration:
			self.draw_sliderb(slider, background, t)

		if slider.cur_repeated < slider.repeated:
			self.draw_arrow(slider, background, going_forward, i)
