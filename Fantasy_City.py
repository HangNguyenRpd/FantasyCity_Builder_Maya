''' This script generates futuristic flying terrains and cities from basic 3D geometries.
For terrains, the script apply Perlin noise on a cone with three layers of height maps. Users are allowed to control these maps' coverage, intensity(the bumpiness) and level(how high is the map).
For the port, this script builds a curve based on the base terrain's vertices, then extrudes a cube along that curve. Users are allowed to control how the port can be built.
The bridges from the port to the base terrain, the highways and streets are made with the same principle. Users are allowed to enter number of bridges.
For cities, the script layouts buildings by picking vertices on the base terrain that do not collide with highways and streets' curves, then grows a building from there.
'''

#IMPORT EVERYTHING HERE

import maya.cmds as cmds
from functools import partial as partial
import math
import random
import sys
#please change your directory here
sys.path.append('/run/media/s5080488/KON/Python/Submission/Artefacts/') 
from perlin import SimplexNoise





#DEFINE FUNCTIONS HERE
    
def makeBuilding(terrain, sX, sZ, coverage):
	'''builds buildings on the terrain without colliding with the highways and streets
	terrain		: the base terrain
	sX			: terrain's subdivision X
	sZ			: terrain's subdivision Z
	coverage	: height map coverage (user input)
	return		: name of building group (string)
	'''
    
    #please change your directory here
	pathName = '/run/media/s5080488/KON/Python/Submission/Artefacts/'
    
    #calculate positions of highways and streets, and building height
	ground_highway_pos = int(sZ-coverage[1]*sZ/2)
	middle_highway_pos = int((coverage[1]+coverage[2])*sZ/2)
	top_highway_pos = int(coverage[2]*sZ/2)+2
	street_gap = int(sX/5)
	maxHeight = 5
	maxHeight_decre = maxHeight/sZ + 0.15
    
    #import the building
	cmds.file(pathName+'building.ma', i = True, namespace = 'building')
    #create a group containing all the buildings
	building_group_name = cmds.group(em=True, n='Buildings')
	building_index=0
    
    #loop through terrain's vertices to make buildings that does not collide with streets and decreases in height when moving away from the centre
	for z in range(0,sZ-4):
		maxHeight-=maxHeight_decre
		if maxHeight<0:
			break
		elif ((z<top_highway_pos-2) or (top_highway_pos+1<z<middle_highway_pos-2) or (middle_highway_pos+1<z<ground_highway_pos-1) or (z>ground_highway_pos+1)):
			for x in range(0,sX,2):
				if (x%street_gap)!=0 and (x%street_gap)!=1 and (x%street_gap)!=(street_gap-1):
					building_index+=1
					blockPos = cmds.xform(terrain[0]+'.vtx['+`z*sX+x`+']', q=True, ws=True, t=True)
					blockName = cmds.duplicate('building*:Building', n='Building'+`building_index`)
					cmds.xform(blockName, ws=True, s=[random.uniform(0.08,0.5), random.uniform(1,maxHeight), random.uniform(0.08,0.5)], t=blockPos)
					cmds.parent(blockName, building_group_name)
    
    #delete imported object
	cmds.delete('building*:Building')
    
	return building_group_name


def makeStreet(terrain, sX, sZ, coverage):
    '''build streets and highways across terrain
    terrain		: the base terrain
    sX			: terrain's subdivision X
    sZ			: terrain's subdivision Z
    coverage	: height map coverage (user input)
    return		: name of street group (string)
    '''
    
    #create a group containing all highways and streets
    street_group_name = cmds.group(em=True, n='Streets')
    
    #check the map coverage
    if coverage[2]>coverage[1]:
        temp=coverage[1]
        coverage[1]=coverage[2]
        coverage[2]=temp
    ground_highway_pos = int(sZ-coverage[1]*sZ/2)
    middle_highway_pos = int((coverage[1]+coverage[2])*sZ/2)
    top_highway_pos = int(coverage[2]*sZ/2)+2
    
    def makeHighwayCurve(name, highway_pos, elevate, smooth):
		'''makes round highway curves
		highway_pos		: position of the curve
		elevate			: curve's height from the terrain
		smooth			: curve's smoothness
		return			: highway curve at the given position
		'''
		pos_start = cmds.xform(terrain[0]+'.vtx['+`highway_pos*sX`+']', ws=True, q=True, t=True)
		highway_Curve = cmds.curve(p=pos_start)
		for x in range(1,sX):
			pos = cmds.xform(terrain[0]+'.vtx['+`highway_pos*sX+x`+']', ws=True, q=True, t=True)
			cmds.curve(highway_Curve, append=True, p=pos)
		cmds.curve(highway_Curve, append=True, p=pos_start)
        
        #process through the curve
		cmds.xform(highway_Curve, r=True, t=[0,elevate,0])
		cmds.smoothCurve(highway_Curve+'.cv[*]', s=smooth)
		highway_closed_curve = cmds.closeCurve(highway_Curve, bb=1, n=name)
		cmds.parent(highway_closed_curve, street_group_name)
		cmds.delete(highway_Curve)
		cmds.hide(highway_closed_curve)
		return highway_closed_curve[0]
	
	#make highway curves for three map layers
    ground_highway_Curve = makeHighwayCurve('Ground_highway_curve', ground_highway_pos,2,5)
    middle_highway_Curve = makeHighwayCurve('Middle_highway_curve', middle_highway_pos,4,10)
    top_highway_Curve = makeHighwayCurve('Top_highway_curve', top_highway_pos,8,20)
    
    def makeStreetCurve(num_Street, elevate, smooth):
		'''makes street curves
		num_Street		: number of streets
		elevate			: curve's height from the terrain
		smooth			: curve's smoothness
		return			: street curve at the given position
		'''
		streetList = []
		if num_Street>0:
			street_gap = int(sX/(num_Street))
		for i in range(num_Street):
			street_num = i*street_gap
			street_pos = cmds.xform(terrain[0]+'.vtx['+`3*sX+street_num`+']', ws=True, q=True, t=True)
			street_Curve = cmds.curve(n='street_curve_'+`i`,p=street_pos)
			for z in range(4,sZ-4):
				pos = cmds.xform(terrain[0]+'.vtx['+`z*sX+street_num`+']', ws=True, q=True, t=True)
				cmds.curve(street_Curve, append=True, p=pos)
				cmds.xform(street_Curve+'.u['+`i*(sZ-5)+z`+']', r=True, t=[random.uniform(0.1,0.3),0,random.uniform(0.1,0.3)])
            #process through the curve
			cmds.xform(street_Curve, r=True, t=[0,elevate,0])
			cmds.smoothCurve(street_Curve+'.cv[*]', s=smooth)
			cmds.parent(street_Curve, street_group_name)
			streetList.append(street_Curve)
			cmds.hide(street_Curve)
		return streetList
    
    #make 5 street curves
    street_Curve = makeStreetCurve(5, 0.2, 5)
    
    #small function to extrude road along the given curve
    def buildPath(name, path, radius, thickness, rotation):
        subaxis = 10
        pathBlock = cmds.polyPipe(n=name, radius = radius, height=0.5, sc=1, sh=1, sa=subaxis, thickness=thickness)
        print path
        #delete everything except faces 35:39
        cmds.delete(pathBlock[0]+'.f[0:34]')
        block_pos = cmds.xform(path+'.cv[0]', ws=True, q=True, t=True)
        cmds.xform(pathBlock[0], ws=True, ro=rotation, t=block_pos)
        cmds.xform(pathBlock[0], r=True, t=[0,0.2,0])
        cmds.polyExtrudeFacet(pathBlock[0]+'.f[0:4]', inputCurve = path, d=sZ*2, xft=True)
        cmds.parent(pathBlock[0], street_group_name)
	
	#build all the highways and streets
    buildPath('Ground_Highway', ground_highway_Curve, 0.5, 0.2, [90,-180,0])
    buildPath('Middle_Highway', middle_highway_Curve, 0.3, 0.1, [90,-180,0])
    buildPath('Top_Highway', top_highway_Curve, 0.2, 0.1, [90,-180,0])
    for i in range(5):
        buildPath('Street_'+`i`, street_Curve[i], 0.2, 0.1,[90,-360/5*(i+1),0])
    
    return street_group_name
        
''''''

def makePort(terrain, sX, sZ, port_Circle, port_Scale):
    '''builds the port around terrain
	terrain			: the base terrain
	sX				: terrain's subdivision X
	sZ				: terrain's subdivision Z
	port_Circle		: how much the port rounds the terrain
	port_Scale		: scale factor of the port
	return          : name of the port curve and port block
    '''
    
    #build the curve 
    port_Start_Pos = cmds.xform(terrain[0]+'.vtx['+`sX*sZ-1`+']', q=True, t=True) #this point of the cone is always at the X-axis
    portCurve = cmds.curve(p= port_Start_Pos, n='Port_curve')
    curve_Start_Num = sX*(sZ-1)
    curve_End_num = int(curve_Start_Num + port_Circle*sX)
    
    for i in range(curve_Start_Num, curve_End_num ):
        pos = cmds.xform(terrain[0]+'.vtx['+`i`+']', q=True, t=True)
        cmds.curve(portCurve, append=True, p=pos)
    
    cmds.scale(port_Scale,0,port_Scale, portCurve)
    
    #place blocks along the curve
    curve_Start = cmds.xform(portCurve+'.cv[0]', q=True, t=True, ws=True)
    portBlock = cmds.polyCube(h=0.5, w=2, d=2, n='Port')
    cmds.xform(portBlock[0], t=curve_Start)
    cmds.polyExtrudeFacet(portBlock[0]+'.f[2]', inputCurve = portCurve, d=sX)
    cmds.delete(portBlock[0], ch=True)
    cmds.hide(portCurve)
    
    return portCurve, portBlock[0]
            
def makeBridge(num_Bridge, terrain, portBlock, sX, port_Scale):
    '''builds bridges from the port to the terrain
    num_Bridge    : number of bridges
    terrain       : the base terrain
    portBlock     : the created port
    sX            : terrain's subdivision X
    port_Scale    : scale factor of the port
    return        : name of list contaning bridges
    '''
    
    bridge_list=[]
    
    #calculate city centre
    cityCenter = cmds.xform(terrain[0]+'.vtx[0]', ws=True, q=True, t=True)
    
    #number of blocks in the port = sX, calculate face index and space between bridges
    port_face_index = sX*3+6
    print port_face_index
    if num_Bridge==1:
        face_bet_Bridge = 0
    else:
        face_bet_Bridge = int(sX/(num_Bridge-1))-2
    cityCenter = cmds.xform(terrain[0]+'.vtx[0]', ws=True, q=True, t=True)
    scalevalue = (1-1/(port_Scale+1))
   
    #place a bridge
    for i in range(num_Bridge):
        extrude_index = i*face_bet_Bridge+port_face_index+1
        get_pos = cmds.exactWorldBoundingBox(portBlock+'.f['+`extrude_index`+']')
        start_pos = [(get_pos[3]+get_pos[0])/2, (get_pos[4]+get_pos[1])/2, (get_pos[5]+get_pos[2])/2]
        end_pos = [cityCenter[0], start_pos[1], cityCenter[2]]
        bridgeCurve = cmds.curve(p=(start_pos, end_pos),d=1, n='Bridge_curve_'+`i`)
        cmds.xform(bridgeCurve, pivots=start_pos, s=(scalevalue, 0, scalevalue))
        cmds.polyExtrudeFacet(portBlock+'.f['+`extrude_index`+']', inputCurve = bridgeCurve, d=5)
        cmds.hide(bridgeCurve)
        bridge_list.append(bridgeCurve)
        
    return bridge_list
 
''''''

def modifyTerrain(terrain, sX, sY, sZ, sharpness, intensity, coverage, level):
    '''creates terrain texture on the cone
    terrain        : the cone
    sX             : the cone's subvision X
    sY             : the cone's subvision Y
    sZ             : the cone's subvision Z
    sharpness      : overall texture sharpness
    intensity      : intensity of 3 map layers
    coverage       : coverage of 3 map layers
    level          : height of 3 map layers
    '''

     
    layer = [[],[],[]]
    
    #going through loop to draw height map
    for i in range(3):
        for z in range(sZ+sY):
            for x in range(sX):
                #draw 3 layers of height map
                #generate a suitable value for Simplex noise with x and z
                nx = x*10/sX
                nz = z*10/sZ
                #SimplexNoise 3D receives 3 parameters and returns a float between (-1,1)
                #increment 1 because math.pow can return false with negative value
                noise = SimplexNoise().noise3(nx,nz,random.random())+1+level[i] #apply height map
                #layer is a list containing 3 layers, each layer is a list containing noise value
                layer[i].append(noise)
                
    #now we have 3 layers of maps with different frequencies    
    print layer[0]  
    print layer[1]   
    print layer[2]
    
    #calculate middle and top layers
    for i in range(1,3):
        cover = int(sZ*coverage[i])
        print cover                                                                             
        for z in range(cover, sZ):
            for x in range(sX):
                layer[i][z*sX+x] = 0
            
    print 'final map'
    print layer[0]  
    print layer[1]   
    print layer[2]
        
    
    #apply height map to top plane of the cone
    for z in range(sZ):
        for x in range(sX):
            #putting 3 layers together
            h = intensity[0]*layer[0][z*sX+x] + intensity[1]*layer[1][z*sX+x]/(0.2*z+1) + intensity[2]*layer[2][z*sX+x]/(0.2*z+1)
            #exonential redistribution, controlling sharpnessintensity[i] = c
            h = math.pow(h, sharpness)
            #apply height map to plane by moving vertices
            cmds.xform(terrain[0]+'.vtx['+`z*sX+x`+']',r=True,t=[0,h,0])
            if z==0 and x==0:
                cmds.xform(terrain[0]+'.vtx['+`(sZ+sY-1)*sX`+']',r=True, t=[0,h,0])
                
    #apply texture to underground surface, leave out last 3 rows
    for y in range(sZ,sZ+sY-3):
        for x in range(sX):
            h = layer[0][y*sX+x] + layer[1][y*sX+x] + layer[2][y*sX+x]
            h = math.pow(h, sharpness)
            #apply height map
            cmds.xform(terrain[0]+'.vtx['+`y*sX+x`+']',r=True,t=[SimplexNoise().noise3(x,y,random.random()),-h,random.betavariate(1,5)/2])
    
    #move the last 3 rows
    for y in range(sZ+sY-3,sZ+sY-1):
        for x in range(sX):
            cmds.xform(terrain[0]+'.vtx['+`y*sX+x`+']',r=True,t=[0,-2,0])
    
    #move bottom vertex
    cmds.xform(terrain[0]+'.vtx['+`(sZ+sY-1)*sX+1`+']',r=True,t=[0,-2.5,0])
            
    
''' '''
    

def actionProc(_height, _radius, _sharpness, _intensity, _coverage, _level, _port_Circle, _port_Scale, _num_Bridge, _):
    '''generates city after clicking OK button
    _height			: terrain height value from GUI
    _radius			: terrain radius value from GUI
    _sharpness		: overall texture sharpness from GUI
    _intensity		: intensity(bumpiness) of 3 map layers from GUI
    _coverage		: map coverage of 3 layers from GUI
    _level			: height of 3 map layers from GUI
    _port_Circle	: ow much the port rounds the terrain from GUI
    _port_Scale		: scale factor of the port from GUI
    _num_Bridge		: number of bridges from GUI
    '''
    
    #geab input from GUI
    intensity = [[],[],[]]
    coverage = [[],[],[]]
    level = [[],[],[]]
    height = cmds.floatField(_height, q=True, value=True)
    radius = cmds.floatField(_radius, q=True, value=True)
    sharpness = cmds.floatSliderGrp(_sharpness, q=True, value=True)
    for i in range(3):
        intensity[i] = cmds.floatSliderGrp(_intensity[i], q=True, value=True)
        if i!=0:
            coverage[i] = cmds.floatSliderGrp(_coverage[i], q=True, value=True)
        level[i] = cmds.floatSliderGrp(_level[i], q=True, value=True)
    port_Circle = cmds.floatSliderGrp(_port_Circle, q=True, value=True)
    port_Scale = cmds.floatSliderGrp(_port_Scale, q=True, value=True)
    num_Bridge = cmds.intSliderGrp(_num_Bridge, q=True, value=True)
    
    #make flying terrain
    sX = int(radius*4)
    sY = int(height*2)
    sZ = int(radius*2)
    terrain = cmds.polyCone(n='Terrain', h=height, r=radius, sx=sX, sy=sY, sz=sZ)
    cmds.xform(terrain[0], ro=[180,0,0])
    
    #build port around the terrain
    port = makePort(terrain, sX, sZ, port_Circle, port_Scale)
    city = cmds.group(terrain[0], port[0], port[1], n='City')
    cmds.xform(city, shear=[random.random(),random.random(),0])
    cmds.makeIdentity(terrain[0], apply=True)
    
    #apply terrain texture on the cone, then move the port to ground level
    modifyTerrain(terrain, sX, sY, sZ, sharpness, intensity, coverage, level)
    port_Height = cmds.xform(terrain[0]+'.vtx['+`sX*(sZ-1)`+']', q=True, t=True)
    cmds.xform(port[0],port[1], r=True, t=(0,port_Height[1],0))
    
    
    #build bridges
    if num_Bridge!=0:
        bridge = makeBridge(num_Bridge, terrain, port[1], sX, port_Scale)

    #generate surrounding terrains randomly
    pv = cmds.xform(terrain[0],q=True, rp=True)
    for i in range(random.randint(0,2)):
        smallterrain = cmds.duplicate(terrain[0], n='Small_Terrain_'+`i`)
        cmds.xform(smallterrain, pivots=pv, s=[0.4/(i+1),0.4/(i+1),0.4/(i+1)],ro = [0,random.random(),0],t=[random.randint(-2,height//3),radius*1.2, radius*1.2],r=True)
        cmds.xform(smallterrain, ws=True, rp=pv, ro=[0,i*180,0])
        cmds.xform(smallterrain, ws=True, s=[random.random(), random.random(), random.random()])
    
    #build city on top of terrain
    street = makeStreet(terrain, sX, sZ, coverage)
    building = makeBuilding(terrain, sX, sZ, coverage)
    
    #group everything under group city
    cmds.parent(street, building, bridge, city)
    
    cmds.delete(all=True, ch=True)
    
    print 'Build City Done'
        
        
        
''' '''

def createUI():
    '''This function creates GUI for user to enter input'''        
    
    #check if window exists, avoid opening multiple windows
    windowID = 'Terrain'
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    #make new window
    cmds.window(windowID, title='Fantasy City', widthHeight=(500,600), bgc=[0.25,0.25,0.25])
    
    #create layout
    cmds.columnLayout('column',adj=True, cat=['both',10], rowSpacing=10)
    
    #create input fields: height and radius of city, overall sharpness
                          #3 layers ground, middle and top which have: intensity, level
    cmds.frameLayout(label='TERRAIN', font='boldLabelFont')
    cmds.text(label=' ')
    cmds.text(label='Height of the map', align='left')
    height = cmds.floatField(ann='Height of the map', minValue=0, maxValue=40, value=10)
    cmds.text(label='Radius of the map', align='left')
    radius = cmds.floatField(ann='Radius of the map', minValue=0, maxValue=40, value=15)
    sharpness = cmds.floatSliderGrp(label='sharpness', minValue=0.001, maxValue=2, value=0.4, field=True,step=0.001)
    frequency=[]
    
    intensity = []
    coverage = [1]
    level = []
    for i in range(3):
        if i==0:
            cmds.text(label='GROUND', align='left')
        elif i==1:
            cmds.text(label='MIDDLE', align='left')
            cover = cmds.floatSliderGrp(label='Coverage',minValue=0, maxValue=1, value=0.5, field=True,step=0.1)
            coverage.append(cover)
        else:
            cmds.text(label='TOP', align='left')
            cover = cmds.floatSliderGrp(label='Coverage',minValue=0, maxValue=1, value=0.3, field=True,step=0.1)
            coverage.append(cover)
            
        lv = cmds.floatSliderGrp(label='Level', minValue=0, maxValue=10, value=1, field=True,step=0.01)
        level.append(lv)
        intens = cmds.floatSliderGrp(label='Intensity', minValue=0, maxValue=50, value=1, field=True, step=0.1)
        intensity.append(intens)
    
    cmds.frameLayout(label='PORT')
    port_Circle = cmds.floatSliderGrp(label='Port circle', minValue=0.1, maxValue=1, value=0.5, field=True, step=0.1)
    port_Scale = cmds.floatSliderGrp(label='Port scale', minValue=1.2, maxValue=5, value=2, field=True, step=0.1)
    num_Bridge = cmds.intSliderGrp(label='Number of bridges', minValue=0, maxValue=5, value=3, field=True, step=1)
    
    #OK button
    cmds.button('OK', command = partial(actionProc, height, radius, sharpness, intensity, coverage, level, port_Circle, port_Scale, num_Bridge))
    
    
    #show window
    cmds.showWindow()



# MAIN PROGRAM
if __name__ == "__main__":
	createUI()
