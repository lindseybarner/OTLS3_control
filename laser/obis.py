import traceback
import time
import rs232.RS232 as RS232

class Obis(RS232.RS232):

	def __init__(self,**kwds):
		self.on = False
		try:
			super().__init__(**kwds)
			assert not(self.commWithResp("?SYStem:INFormation:MODel?") == None)

			self.pmin = 0.0
			self.pmax = 5.0
			[self.pmin, self.pmax] = self.getPowerRange()
			print([self.pmin, self.pmax])
			self.setExtControl(False)

		except Exception:
			print(traceback.format_exc())
			self.live = False
			print("Failed to connect to the Cobolt Skyra!")

	def getPowerRange(self):
		self.sendCommand("SOURce:POWer:LIMit:LOW?")
		pmin = 1000.0*float(self.waitResponse()[:-6])
		self.sendCommand("SOURce:POWer:LIMit:HIGH?")
		pmax = 1000.0 * float(self.waitResponse()[:-6])
		return [pmin, pmax]


	def getExtControl(self):
		self.sendCommand("SOURce:AM:SOURce?")
		response = self.waitResponse()
		print(response)
		if("CWP" in response) or ("CWC" in response):
			return False
		else:
			return True

	def setExtControl(self, mode):
		if mode:
			self.sendCommand("SOURce:AM:EXTernal DIGital")
		else:
			self.sendCommand("SOURce:AM:INTernal CWP")
		self.waitResponse()

	def setPower(self, power_in_mw):
		if power_in_mw > self.pmax:
			power_in_mw = self.pmax
		self.sendCommand("SOURce:POWer:LEVel:IMMediate:AMPLitude " + str(0.001*power_in_mw))
		self.waitResponse()

	def turnOn(self):
		self.sendCommand("SOURce:AM:STATe ON")
		self.waitResponse()
		time.sleep(8)
		print('laser on')
	def turnOff(self):
		self.sendCommand("SOURce:AM:STATe OFF")
		self.waitResponse()