#Let's simulate gravity and rigid collisions in two dimensions (but with 3d laws)
#We will need:
    #attractive inverse square force. Could keep it flexible and do a Coulomb force with -G instead of 1/(4pieps), but I don't fancy faffing with superfluous calculation due to inertial mass = gravitational mass
    #collision check and execution - sweeping cylinders?
    #circular particles with mass (the charge for gravity), radius, 2d position, 2d velocity
    #a window with background
    #we're using pygame to add new particles, so reading inputs is needed
    #what library would allow me to use vector maths in Python?

import pygame, sys, math, random
import pygame.locals as GAME_GLOBALS
import pygame.event as GAME_EVENT
import pygame.time as GAME_TIME
#import coulomb #uncomment if I make this a separate file

#using math library for finding vector magnitudes. Could code this ourselves very easily.

windowWidth = 1600
windowHeight = 900
boxthickness = 10

pygame.init()
surface = pygame.display.set_mode((windowWidth, windowHeight))
pygame.display.set_caption("Planets and Comets")

previousMousePosition = (windowWidth/2,windowHeight/2)
mousePosition = None
mouseDown = False
#Establishes variables that will allow us to track mouse position

bodies = [] #makes a list we will add to
newBody = None
bodyCount = 0
lastBodyticks = 0
#time between new bodies
deltaNewticks = 16

gravity = -1
speedmod = 0
deltaT = 1 #I don't think this should need changing, but it's here in case
restitution = 0 #[0,1], zero for coalesce, 1 for perfectly elastic.
#When restitution is too low, code can very easily result in overlapping object due to how the collision detection loops (adjust for one collision can undo accommodating first)
#Avoid this by coding an absorption mechanism? More simply, push objects away based on their index, and accommodate further collisions as they arise?
#Still no friction, so even though bodies coalesce, they can orbit each other at high velocities while in contact

def makeBody():
    #Mass, radius, position, velocity, number from body list length? random colour?
    #let's have constant density, so mass is proportional to radius cubed - let's make it equal, for now
    #why not radius squared? because we are still using inverse square law, so there is a supposed 3rd dimension
    #let's have a diameter of at least four upto double box thickness (accounting for rounding down by int())
    #global boxthickness, deltaT, mousePosition
    r = int(2+random.random()*(boxthickness-1)) #similar to math.floor() from what I can tell, but stores as integer instead of float
    #r=10
    print(r)
    bodies.append({#"pos":[random()*(windowWidth-4*boxthickness), random()*(windowHeight-4*boxthickness)],
                   "pos":[mousePosition[0], mousePosition[1]],
                   "vel":[(random.random()-0.5)*(2*speedmod*deltaT), (random.random()-0.5)*(2*speedmod*deltaT)],
                   "radius":r,
                   "mass":(r*r*r),
                   "colour":(random.random()*240+15, random.random()*240+15, random.random()*240+15)})
    print("Number of bodies: ", len(bodies))
#if I were to make these bodies a class (not really necessary unless I wanted to distinguish between planets and comets, say by ignoring comet gravity effect on planet)
#then using a function to build a potential may be easier vs encapsulation concern? probably not necessary, newtonGrav only changes the velocity of one of the two bodies called



#this function only returns field strength at body2 due to body1, to allow for other forces later
#computeforces() will loop through bodies 1 and 2
#is that too granular?
def newtonGrav(body1, body2):
    #global gravity
    relativepos = ((body2["pos"][0]-body1["pos"][0]),(body2["pos"][1]-body1["pos"][1]))
    #get position of body 2 relative to body one
    distance = math.hypot(relativepos[0], relativepos[1])
    #check bodies aren't on top of each other
    if distance <= body1["radius"]+body2["radius"]:
        collide(body1, body2, relativepos, distance)
        #commenting return(0,0) allows acceleration calculation in same timestep as collision is resolved
        return (0,0)
    direction = ((relativepos[0]/distance), (relativepos[1]/distance))
    fieldstrength = (gravity*body1["mass"])/(distance*distance)
    return ((fieldstrength*direction[0]), (fieldstrength*direction[1]))
#could save a division by not normalising direction and instead multipling field strength and non-normalised direction before dividing by distance^3
#however, normalised direction is useful for collisions!

    

#interested in an alternative approach using potential instead of field strength, investigate numerical Lagrangian mechanics
#for potential below, I could loop "for body in bodies" in the main() loop, as coulomb() requires, but I've included them as globals instead
#def potential(position):
#    global gravity #bodies does not have to be declared as global
#    potential = 0
#    for body in bodies:
#        distance = math.hypot((position[0]-body["pos"][0]), (position[1]-body["pos"][1]))
#        potential += (gravity*body["mass"])/distance




def collide(body1, body2, relpos, dist):
        #could remove "relpos" and "dist" inputs and calculate below, or change the arguments of atan2, but may as well save the computation
    #relativepos = ((body2["pos"][0]-body1["pos"][0]),(body2["pos"][1]-body1["pos"][1]))
        #atan has a single argument (ratio of sides), atan2 has two arguments (two sides) to return appropriate angle in (-pi,pi]
    collAngle = math.atan2(relpos[1],relpos[0])
    #print((body1["pos"][0] - body2["pos"][0]),(body1["pos"][1]-body2["pos"][1]),collAngle)
        #I could return velAdjust divided by deltaT and use it to alter returned acceleration value as a middle ground between full gravaccel and zero
    velAdjust = (1 + restitution) * ((body2["vel"][0] - body1["vel"][0])*math.cos(collAngle) + (body2["vel"][1] - body1["vel"][1])*math.sin(collAngle)) / (body1["mass"] + body2["mass"])
        #note velAdjust contains all the old velocity values we need for the next part, so don't need to worry about new velocities affecting next calculations in chain
    #print(body1["vel"][0], body1["vel"][1], body2["vel"][0], body2["vel"][1])
    body1["vel"][0] += body2["mass"]*velAdjust*math.cos(collAngle)
    body1["vel"][1] += body2["mass"]*velAdjust*math.sin(collAngle)
    body2["vel"][0] -= body1["mass"]*velAdjust*math.cos(collAngle)
    body2["vel"][1] -= body1["mass"]*velAdjust*math.sin(collAngle)


        #issue: when speed of approach is low, bodies don't move apart quickly enough to not overlap on next frame, and collide() pushes them closer together as they try to move apart due to my calculation
        #could fix by checking sign of velAdjust relative to velocity components, or I set positions to not overlap anymore so that they move apart when position step is calculated

        #weight adjustment to preserve centre of mass
    #dist = math.hypot(relativepos[0], relativepos[1])
    if dist == 0:
        dist = 1
        relpos = (1,0)
    posAdjust = ( ( (body1["radius"]+body2["radius"]) / dist) - 1) / (body1["mass"] + body2["mass"])
    body1["pos"][0] -= body2["mass"] * posAdjust * relpos[0]
    body1["pos"][1] -= body2["mass"] * posAdjust * relpos[1]
    body2["pos"][0] += body1["mass"] * posAdjust * relpos[0]
    body2["pos"][1] += body1["mass"] * posAdjust * relpos[1]
    #print(velAdjust, body1["vel"][0], body1["vel"][1], body2["vel"][0], body2["vel"][1])

        #alt - move body2 only
    #posAdjust = (body1["radius"] + body2["radius"]) / dist
    #body2["pos"][0] = body1["pos"][0] + posAdjust * relpos[0]
    #body2["pos"][1] = body1["pos"][1] + posAdjust * relpos[1]

    

def computeVelocities():
    #halfsteps of basic leapfrog - would Verlet be worth implementing? RK4 leapfrog? RK-Nystrom? Might as well at some point, and measure ticks to compare performance
        #moving surface.fill outside main loop would also provide deviations and relative accuracy (assuming leapfrog generally least accurate)
    #for body1 in bodies:
    #    for body2 in bodies:
            #would while body2 in bodies is not body1 do what I want in half-cycling, to then set body1["vel"][i] -= gravaccel2[i] * deltaT and reduce number of newtonGrav() calls?
            #could if body2 is body1: return 0 work or would is end the loop?
    #        if body2 is not body1:
    #            gravaccel2 = newtonGrav(body1, body2)
    #            body2["vel"][0] += gravaccel2[0] * deltaT
    #            body2["vel"][1] += gravaccel2[1] * deltaT
                #we could calculate positions now, but that would affect the newtonGrav calls for the other interactions, leading to a super leapfrogging
                #this would be an issue in any of the loops, hence this is only computeVelocities, not computePosition
                #body2["pos"][0] += body2["vel"][0] * deltaT
                #body2["pos"][1] += body2["vel"][1] * deltaT
                
    #do I need a max/min acceleration? nah, I'll just have collisions with edge of frame

    #We can eliminate some calls for newtonGrav using Newton's third law and uncommenting the below.
    #IMPORTANT: This version is necessary due to my implementation of collide()
    #using previous algorithm would cause collide() to run twice per pair, undoing the effect. This could be fixed by having a check for the relative sign of velAdjust, which has other benefits too
    #for now, I have not included this check
    for idx1 in range(len(bodies)-1):
        for idx2 in range((idx1+1),len(bodies)):
            accel = newtonGrav(bodies[idx1],bodies[idx2])
            bodies[idx1]["vel"][0] -= ((accel[0]*bodies[idx2]["mass"])/(bodies[idx1]["mass"])) * deltaT
            bodies[idx2]["vel"][0] += accel[0] * deltaT
            bodies[idx1]["vel"][1] -= ((accel[1]*bodies[idx2]["mass"])/(bodies[idx1]["mass"])) * deltaT
            bodies[idx2]["vel"][1] += accel[1] * deltaT



            
#this function also updates position
def drawPosition():
    for idx, body in enumerate(bodies):
        body["pos"][0] += body["vel"][0] * deltaT
        body["pos"][1] += body["vel"][1] * deltaT
        #check allows a small amount of OOB to try and return some fast-moving objects to window even after escape
        if body["pos"][0]<0-boxthickness or body["pos"][0]>windowWidth+boxthickness or body["pos"][1]<0-boxthickness or body["pos"][1]>windowHeight+boxthickness:
            #option 1: delete out of bounds. Use this once collision with box is implemented
            #bodies.pop(idx)
            #option 2: projection - have particles wrap around. More interesting than particles slowly leaving, or limits on gravity. I have not coded gravity to account for this space
            #to have gravity wrap around would require checking for whether displacement components exceed half window dimension in newtonGrav(), or simply use mod algebra
            #the implementation here is compact. I could use body["pos"][i] = (body["pos"][i]-boxthickness)%(windowDim-2*boxthickness)+boxthickness to interact with box, and have a different check for out of bounds
            body["pos"][0] %= windowWidth
            body["pos"][1] %= windowHeight
        #could check for collisions after position calculation and before drawing, recalculate position to accommodate - then we never see overlaps on screen
        #because I don't have acceleration limits, I instead check for collisions at acceleration step
        #pygame.draw.circle(surface, (200,200,200), (math.floor(body["pos"][0]), math.floor(body["pos"][1])), body["radius"], 0) #draws filled grey circle where body is
        #I was using math.floor() instead of int(), which was fine for python3, but to work with python I switched
        pygame.draw.circle(surface, body["colour"], (int(body["pos"][0]), int(body["pos"][1])), body["radius"],0)
        #a lot of these references would be easier with vectors, i.e. body["pos"] could be a vector instead of putting list elements into (b[p][0],b[p][1])
        


#quit the program
def close():
    pygame.quit()
    sys.exit()




while True:
    surface.fill((0,0,0))
    pygame.draw.rect(surface, (150,150,150), (0,0,windowWidth, windowHeight), boxthickness*2)
    #.rect draws thickness extending from position/dimension parameters, and looks ugly with a thick box
        #pushing rectangle right to edges of screen and using "twice" thickness gets the desired result
    

    for event in GAME_EVENT.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                close()
            if event.key is pygame.K_SPACE or event.key is pygame.K_r:
                bodies.clear()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouseDown = True

        if event.type == pygame.MOUSEBUTTONUP:
            mouseDown = False
            lastBodyticks = deltaNewticks

    if mouseDown:
        mousePosition = pygame.mouse.get_pos()
        if lastBodyticks > deltaNewticks:
            makeBody()
            lastBodyticks=0
        lastBodyticks += 1
                    
    computeVelocities()
    drawPosition()

    pygame.display.update()
