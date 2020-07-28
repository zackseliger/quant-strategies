class Statistics:
	def __init__(self):
		self.inprogressdata = []
		self.completedata = []

	def newpoint(self, **kwargs):
		complete = False
		point = {}

		# add keywords to point
		for key, value in kwargs.items():
			point[key] = value
			if key == 'pnl':
				complete = True

		# if pnl was in point, we're done
		if complete == True:
			self.completedata.append(point)
		else:
			self.inprogressdata.insert(0,point)

		return point

	def completepoint(self, point, **kwargs):
		# add kwargs to point
		for key, value in kwargs.items():
			point[key] = value

		# remove point from inprogress point
		self.inprogressdata.pop(self.inprogressdata.index(point))

		self.completedata.append(point)

	def getpoint(self, key, value):
		for point in self.inprogressdata:
			if key in point and point[key] == value:
				return point
		return -1

	# TODO
	def to_csv(self, path):
		f = open(path, 'w')

		# headers from keys of first point
		keys = self.completedata[0].keys()
		for key in keys:
			f.write(key+",")
		f.write("\n")

		for point in self.completedata:
			for key in keys:
				f.write(str(point[key])+",")
			f.write("\n")
		f.close()