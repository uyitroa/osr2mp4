
# Circle
from ImageProcess import imageproc
from ImageProcess.PrepareFrames.YImage import YImage

hitcircle = "hitcircle"
hitcircleoverlay = "hitcircleoverlay"
sliderstartcircleoverlay = "sliderstartcircleoverlay"
sliderstartcircle = "sliderstartcircle"
approachcircle = "approachcircle"

default_size = 128
overlay_scale = 1.05


def prepare_approach(path, scale, time_preempt, fps):
	"""
	:param path: string without filename
	:param scale: float
	:param time_preempt: the time the circle is on screen
	:param fps: fps
	:return: [PIL.Image]
	"""
	img = YImage(path + approachcircle).img
	approach_frames = []
	interval = int(1000/fps)
	time_preempt = round(time_preempt)
	s = 3.5
	for time_left in range(time_preempt, 0, -interval):
		s -= 2.5 * interval / time_preempt
		p = imageproc.change_size(img, s * scale, s * scale)
		approach_frames.append(p)
	return approach_frames


def overlayhitcircle(overlay, circle, color, scale):

	color_circle = imageproc.add_color(circle, color)
	overlay_img = overlay.copy()

	x1 = circle.size[0] // 2
	y1 = circle.size[1] // 2

	imageproc.add(overlay_img, color_circle, x1, y1, channel=4)
	return imageproc.change_size(color_circle, scale, scale)


def overlayapproach(circle, approach, alpha):

	x1 = approach.size[0] // 2
	y1 = approach.size[1] // 2

	imageproc.add(circle, approach, x1, y1, channel=4)
	return imageproc.newalpha(approach, alpha/100)


def prepare_fadeout(img):
	fadeout = []
	for x in range(100, 140, 4):
		size = x / 100
		im = imageproc.newalpha(img, 1 - (x - 100) / 40)
		im = imageproc.change_size(im, size, size)
		fadeout.append(im)
	return fadeout


def calculate_ar(ar, fps):
	interval = 1000 / fps
	if ar < 5:
		time_preempt = 1200 + 600 * (5 - ar) / 5
		fade_in = 800 + 400 * (5 - ar) / 5
	elif ar == 5:
		time_preempt = 1200
		fade_in = 800
	else:
		time_preempt = 1200 - 750 * (ar - 5) / 5
		fade_in = 800 - 500 * (ar - 5) / 5
	opacity_interval = int(100 * interval / fade_in)
	return opacity_interval, time_preempt, fade_in


def load(path):
	circle = YImage(path + hitcircle).img
	c_overlay = YImage(path + hitcircleoverlay).img
	slider = YImage(path + sliderstartcircle).img
	s_overlay = YImage(path + sliderstartcircleoverlay).img
	return circle, c_overlay, slider, s_overlay


def prepare_circle(beatmap, path, scale, skin, fps):
	# prepare every single frame before entering the big loop, this will save us a ton of time since we don't need
	# to overlap number, circle overlay and approach circle every single time.

	opacity_interval, time_preempt, fade_in = calculate_ar(beatmap.diff["ApproachRate"], fps)

	cs = (54.4 - 4.48 * beatmap.diff["CircleSize"]) * scale
	radius_scale = cs * overlay_scale * 2 / default_size

	circle, c_overlay, slider, s_overlay = load(path)
	approach_frames = prepare_approach(path, radius_scale, time_preempt, fps)

	fadeout = [[], []]  # circle, slider
	circle_frames = []  # [color][number][alpha]
	slidercircle_frames = []  # [color][number][alpha]

	for c in range(1, skin.colours["ComboNumber"] + 1):
		color = skin.colours["Combo" + str(c)]

		orig_circle = overlayhitcircle(c_overlay, circle, color, radius_scale)
		fadeout[0].append(prepare_fadeout(orig_circle))

		orig_slider = overlayhitcircle(s_overlay, slider, color, radius_scale)
		fadeout[1].append(prepare_fadeout(orig_slider))

		alpha = 0  # alpha for fadein
		circle_frames.append([])
		slidercircle_frames.append([])
		# we also overlay approach circle to circle to avoid multiple add_to_frame call
		for i in range(len(approach_frames)):
			approach_circle = imageproc.add_color(approach_frames[i], color)
			approach_slider = approach_circle.copy()

			circle_frames[-1].append(overlayapproach(orig_circle, approach_circle, alpha))
			slidercircle_frames[-1].append(overlayapproach(orig_slider, approach_slider, alpha))

			alpha = min(100, alpha + opacity_interval)

		# for late tapping
		slidercircle_frames[-1].append(orig_slider)
		circle_frames[-1].append(orig_circle)
		#
		# img = orig_circle.copy()
		# slider_circle.img = orig_overlay_slider.copy()
	print("done")

	return slidercircle_frames, circle_frames, fadeout