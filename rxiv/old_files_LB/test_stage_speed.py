import laser.obis as obis
import xyz_stage.ms2000 as ms2000

xyzStage = ms2000.MS2000(baudrate = 9600, port = 'COM5')
xyzStage.setScanF(1)
xyzStage.setBacklash(0)
xyzStage.setTTL(0)
initialPos = xyzStage.getPosition()
laser = obis.Obis(baudrate = 9600, port = 'COM4')

xPos = -5.3
yPos = -15.6
xLength = 0.2
moveSpeed = 0.8
scanSpeed = 0.05

xyzStage.goAbsolute('X', -xPos, False) #used to be -xPos - .035

xyzStage.setVelocity('X',scanSpeed)
xyzStage.setScanR(-xPos, -xPos + xLength)
xyzStage.setScanV(yPos) 
xyzStage.scan(False,laser,-xPos) #laser turns off laser as soon as scan is done, and others commeand...
				