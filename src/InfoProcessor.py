

class Updater:
	def __init__(self, resultinfo, component):
		self.resultinfo = resultinfo
		self.component = component
		self.info_index = 0

	def process_combo(self):
		if self.info.combostatus == 1:
			self.component.combocounter.add_combo()
		elif self.info.combostatus == -1:
			self.component.combocounter.breakcombo()

	def process_acc(self):
		objtype = type(self.info.more).__name__
		if objtype == "Circle":
			idd = str(self.info.id) + "c"
			x, y = self.info.more.x, self.info.more.y
			if self.info.more.state == 1:
				self.component.hitobjmanager.notelock_circle(idd)
			elif self.info.more.state == 2:
				self.component.hitobjmanager.fadeout_circle(idd)
				self.component.urbar.add_bar(self.info.more.deltat, self.info.hitresult)
				if self.info.more.sliderhead:
					self.component.hitobjmanager.sliderchangestate(self.info.more.followstate,
					                                               str(self.info.id) + "s")

		elif objtype == "Slider":
			idd = str(self.info.id) + "s"
			x, y = self.info.more.x, self.info.more.y
			followbit = self.info.more.followstate
			if int(followbit[0]):
				self.component.hitobjmanager.sliderchangestate(int(followbit[1]), idd)
			self.component.scorecounter.bonus_score(self.info.more.hitvalue)

		else:
			idd = str(self.info.id) + "o"
			x, y = 384 * 0.5, 512 * 0.5
			self.component.spinner.update_spinner(idd, self.info.more.rotate, self.info.more.progress)
			self.component.scorecounter.bonus_score(self.info.more.hitvalue)
			if self.info.more.bonusscore >= 1:
				self.component.spinbonus.set_bonusscore(self.info.more.bonusscore)

		if self.info.hitresult is not None:
			if not (objtype == "Circle" and self.info.more.sliderhead):
				self.component.hitresult.add_result(self.info.hitresult, x, y)
				self.component.accuracy.update_acc(self.info.hitresult)
			if objtype != "Slider" or self.info.more.tickend:
				self.component.scorecounter.update_score(self.info.score)

	def update(self, cur_time):
		if self.info_index >= len(self.resultinfo) or self.resultinfo[self.info_index].time > cur_time:
			return
		self.info = self.resultinfo[self.info_index]
		self.process_combo()
		self.process_acc()
		self.info_index += 1
