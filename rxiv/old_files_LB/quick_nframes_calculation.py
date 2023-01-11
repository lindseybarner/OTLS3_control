import math

binFactor = 1
xcenter = 5.2
ycenter = 1.9
zcenter = -3.65
xMin = xcenter - .0528 #2 #2MM BY 2MM BY 200UM
xMax = xcenter + 0.0 #.2
yMin = ycenter - 0.0
yMax = ycenter + 0.4
zMin = zcenter - 0.
zMax = zcenter + 0.03

xWidth = 0.206 #in um, not mm (2nd gen system 0.48) 
yWidth = 0.37 # mm (2nd gen system 0.8)
zWidth = 0.03 # mm calculated based on 610px/125um 11-20-19(2nd gen system 0.07)
camY = 256 # pixels
camX = 2048 # pixels
expTime = 4.99 # ms

xLength = xMax - xMin # mm
yLength = math.ceil((yMax - yMin)/yWidth)*yWidth # mm
zLength = math.ceil((zMax - zMin)/zWidth)*zWidth # mm
xOff = xMax - (xLength)/2
yOff = yMax - yLength/2
zOff = zMin

xWidth = xWidth*binFactor
camY = int(camY/binFactor)
camX = int(camX/binFactor)
nFrames = int(round(xLength/(xWidth/1000))) #number of frames in X direction
yTiles = int(round(yLength/yWidth))
zTiles = int(round(zLength/zWidth))

print('xlength = ' + str(xLength))
print('xwidth = ' + str(xWidth))
print('nFrames = ' + str(nFrames))