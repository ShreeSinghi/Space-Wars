"""
winsound.PlaySound('sound.wav', tags)

Meteor attacks from front/back
Meteor attacks l/r (create black bars)
Meteor targets player

"""

import winsound       
from tkinter import mainloop, Canvas, Tk
from PIL import Image, ImageTk
from ctypes import windll
from random import gauss, randint, uniform, choice
from math import sin, cos, radians, ceil
from time import sleep
from numpy import sign
import numpy as np
from numpy import clip

tags =  winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP

def playsound(name, tag):
    try:
        winsound.PlaySound(name, tag)
    except Exception:
        pass

def conv(*args):
    global ratio, shift
    return [(shift+val*ratio) if i%2==0 else ratio*val for i,val in enumerate(args)]

def resize(picname, lratio, degrees=0, white=True, black=True):
    image = Image.open(picname)
    image = image.resize((int(image.size[0]*lratio), int(image.size[1]*lratio)),
                         Image.ANTIALIAS).rotate(-degrees).convert("RGBA")
    newData = []
    for item in image.getdata():
        if ((white and item[0]==255 and item[1]==255 and item[2]==255) or
            (black and item[0]==0 and item[1]==0 and item[2]==0)):
            newData.append((0, 0, 0, 0))
        else:
            newData.append(item)
    image.putdata(newData)
    return ImageTk.PhotoImage(image)

def keyup(e):
    if e.keycode in keys:
        keys.pop(keys.index(e.keycode))

def keydown(e):
    if not e.keycode in keys:
        keys.append(e.keycode)

def pr(px,py,x1,y1,x2,y2):
    return min(x1,x2)<px<max(x1,x2) and min(y1,y2)<py<max(y1,y2)

def rr(x1,y1,x2,y2,x3,y3,x4,y4):
    x1, y1, x2, y2 = min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)
    x3, y3, x4, y4 = min(x3,x4), min(y3,y4), max(x3,x4), max(y3,y4)
    return (((y3<y1<y4 or y3<y2<y4) and (x3<x1<x4 or x3<x2<x4)) or
            ((y1<y3<y2 or y1<y4<y2) and (x1<x3<x2 or x1<x4<x2)))

def cr(cx,cy,r,rx,ry,rectw,recth):
    circdistx, circdisty = abs(rx-cx), abs(ry-cy)
    
    if circdistx > rectw/2+r or circdisty > recth/2+r:  return False
    if circdistx < rectw/2 or circdisty < recth/2:      return True 

    return (circdistx-rectw/2)**2 + (circdisty-recth/2)**2 < r**2

def cc(obj1,obj2,r):
    x1, y1, x2, y2 = obj1.x, obj1.y, obj2.x, obj2.y
    return ((x1-x2)**2 + (y1-y2)**2)<r**2

def rearrange():
    cv.tag_raise('bullet')
    cv.tag_raise('alien')
    cv.tag_raise('player')
    cv.tag_raise('rock')
    cv.tag_raise('laser')
    if player.beaming>0: cv.tag_raise('player')
    cv.tag_lower('stars')

class stars:
    def __init__(self, count):
        self.ys = []
        self.stars = []
        for i in range(count):
            size, randx, y = randint(1,3), randint(0,500)*2, 1000*i//count
            self.stars.append(cv.create_rectangle(*conv(randx,y,randx+size,y+size),
                                                  fill='white',outline='',tag='star'))
            self.ys.append(y)
    
    def shift(self, val):
        for index, star in enumerate(self.stars):
            self.ys[index] += val
            if self.ys[index]>1000:
                cv.move(star,0,(val-self.ys[index])*ratio)
                self.ys[index] = 0
            else:
                cv.move(star,0,val*ratio)

class bullet:
    def __init__(self, x, y, angle, speed, col1, col2):
        self.x, self.y = x, y
        self.speed = speed
        self.xvel = sin(radians(angle))*self.speed
        self.yvel = -cos(radians(angle))*self.speed
        self.sprite = cv.create_oval(*conv(x-5,y,x+5,y+10), fill=col1,
                                     outline=col2,width=2*ratio, tags=(col2,'bullet'))
    
    def move(self):
        self.x += self.xvel
        self.y += self.yvel
        cv.move(self.sprite, self.xvel*ratio, self.yvel*ratio)

class rock:
    def __init__(self, x, xvel, yvel):
        self.x = x
        self.y = -50
        self.xvel = xvel
        self.yvel = yvel
        self.sprite = cv.create_image(shift+ratio*x, ratio*self.y,
                                      image=choice(rockimgs), tag='rock')

    def move(self):
        self.x += self.xvel
        self.y += self.yvel
        cv.tag_raise(self.sprite)
        cv.move(self.sprite, ratio*self.xvel, ratio*self.yvel)

class energy:
    def __init__(self, x, y, size=12):
        self.x, self.y = x, y
        self.dir = 1
        self.col = 0
        filcol = '#%02x%02x%02x'%(20+9*self.col,20+12*self.col,240)
        outcol = '#%02x%02x%02x'%(200-10*self.col,200-9*self.col,240)
        self.sprite = cv.create_oval(*conv(x-size,y,x+size,y+size*2), fill=filcol,
                                     outline=outcol, width=0.1*ratio*size)
    
    def change(self):
        global ratio
        self.col += self.dir
        if not 0<self.col<17:
            self.dir *= -1
        filcol = '#%02x%02x%02x'%(20+9*self.col,20+12*self.col,240)
        outcol = '#%02x%02x%02x'%(200-10*self.col,200-9*self.col,240)
        cv.itemconfig(self.sprite, width=ratio*(1+round(self.col/2.5)), fill=filcol, outline=outcol)
    
    def move(self):
        global ratio
        self.y += 5
        if self.y>1015:
            self.delete()
            return
        self.change()
        cv.move(self.sprite, 0, 5*ratio)
        
    def delete(self):
        global ball
        ball = False
        cv.delete(self.sprite)
        
class heart:
    def __init__(self, x, y):
        global scrhealth
        scrhealth += 1
        self.x, self.y = x, y
        self.sprite = cv.create_image(*conv(x,self.y), image=heartimg)
    def move(self):
        self.y += 5
        cv.move(self.sprite, 0, ratio*5)
    def delete(self):
        cv.delete(self.sprite)
        scrhearts.remove(self)

def endgame():
    im = cv.create_image(shift+ratio*500, ratio*500, image=yodudeimg)
    for i in range(7):
        cv.itemconfig(player.sprite, image=bombimgs[i], state='normal')
        sleep(0.15)
        screen.update_idletasks()
    cv.itemconfig(player.sprite, state='hidden')
    cv.itemconfig(im, state='hidden')
    screen.update_idletasks()
    sleep(1)
    cv.itemconfig(im, image=goverimg, state='normal')
    screen.update_idletasks()
    sleep(2.5)
    screen.destroy()

def albullmethod():
    global meteor
    for index, bullet in enumerate(albulls):
        bullet.move()
        if not (0<bullet.x<1000 and 0<bullet.y<1000):
            cv.delete(bullet.sprite)
            albulls.pop(index)
        elif meteor and cc(bullet,meteor, 70):
            x, y = meteor.xvel, meteor.yvel
            meteor.xvel, meteor.yvel = (x+2/(1+(y/x)**2)**0.5*sign(x/y),
                                        y+2/(1+(x/y)**2)**0.5)
            cv.delete(bullet.sprite)
            albulls.pop(index)
        elif player.beaming and abs(bullet.x-player.x)<lwidth+5:
            cv.delete(bullet.sprite)
            albulls.pop(index)
        else:
            if cc(bullet,player,55):
                cv.delete(bullet.sprite)
                albulls.pop(index)
                if not player.invinc:   player.damage()
            else:
                for gbull in player.bullets:
                    if cc(bullet,gbull, 10):
                        cv.delete(bullet.sprite)
                        albulls.remove(bullet)
                        cv.delete(gbull.sprite)
                        player.bullets.remove(gbull)
                        break

class ship:
    def __init__(self, x, y, keys):
        global maxpower, shift, ratio, ldivs
        self.x, self.y = x, y
        self.health = 3
        self.invinc = 0
        self.score = 0
        self.power = maxpower
        self.beamframes = 0
        self.lastshot = 0
        self.charge = 0
        self.beaming = False
        self.angle = 0
        self.active = False 
        self.xvel = self.yvel = 0
        self.speed = 5
        self.maxspeed = 18
        self.sprite = cv.create_image(*conv(self.x, self.y), image=shipimgs[0],
                                      tag='player')
        self.text = cv.create_text(1.5*shift+1000*ratio, 100*ratio, text='Score: 0',
                                   fill='white', font=('Consolas', int(33*ratio)))
        self.bullets = []
        self.lkey, self.rkey, self.dkey, self.ukey, self.skey, self.pkey = keys

        div = 8
        lb, width, bot = shift/2-ratio*50, ratio*100/div, ratio*(500+50*maxpower/2)
        cols = ['#%02x%02x%02x'%(45+16*j,45+16*j,255) for j in range(div)]
        [cv.create_rectangle(lb+j*width, bot-ratio*50*i, lb+width*(j+1),
                             bot-ratio*(50*i+45), fill=col, outline='',
                             tags=f'power{i}') for (j,
                             col) in enumerate(cols) for i in range(maxpower)]
        
        
        cols = ['#%02x%02x%02x'%(45+10*j,45+18*j,255) for j in range(ldivs)][::-1]
        cols += cols
        [cv.create_rectangle(0,0,0,0, fill=col, outline='',
                             tags=(f'laser{j}', 'laser')) for j,col in enumerate(cols)]
        
        top = ratio*(500-50*maxpower/2)/2
        [cv.create_image(shift/(self.health+1)*(i+1), top, image=heartimg,
                         tag=f'heart{i+1}') for i in range(self.health)]

    def goto(self, x, y):
        self.x, self.y = x, y
        cv.coords(self.sprite, shift+ratio*x, y*ratio)
    
    def move(self, x, y):
        if self.x+x<45:     x = 45-self.x
        elif self.x+x>955:  x = 955-self.x
        if self.y+y<550:    y = 550-self.y
        elif self.y+y>960:  y = 960-self.y
        self.goto(x+self.x, self.y+y)

    def beam(self):
        global ldivs
        self.beaming = True
        
        if self.beamframes == 0:
            playsound('buzz.wav', tags | winsound.SND_LOOP)
        
        if self.beamframes<10:      #initialize beams
            for i in range(ceil(self.beamframes/10*ldivs)):
                cv.itemconfig(f'laser{i}', state='normal')
                rect = conv(self.x-i*7,self.y,self.x-i*7-7,0)
                cv.coords(f'laser{i}',*rect)
                cv.itemconfig(f'laser{i+ldivs}', state='normal')
                rect = conv(self.x+i*7,self.y,self.x+i*7+7,0)
                cv.coords(f'laser{i+ldivs}', *rect)
        
        elif self.beamframes<90:    #let em stae
            for i in range(ldivs):
                rect = conv(self.x-i*7,self.y,self.x-i*7-7,0)
                cv.coords(f'laser{i}',*rect)
                rect = conv(self.x+i*7,self.y,self.x+i*7+7,0)
                cv.coords(f'laser{i+ldivs}', *rect)
        else:
            for i in range(ldivs):
                cv.itemconfig(f'laser{i}', state='hidden')
                cv.itemconfig(f'laser{i+ldivs}', state='hidden')
            self.beamframes = 0
            self.active = False
            self.beaming = False
 
            playsound(None, 0)
            return
        
        self.beamframes += 1
        
    def heal(self):
        self.health += 1
        cv.itemconfig(f'heart{self.health}', state='normal')
    
    def damage(self):
        global gameover, maxpower, scrhealth
        cv.itemconfig(f'heart{self.health}', state='hidden')
        cv.itemconfig('laser', state='hidden')
        self.health -= 1
        scrhealth -= 1
        playsound(None, 0)
        playsound('explosion.wav', tags)
        
        if self.health==0:
            gameover = True
        else:
            self.invinc = 104
            self.lastshot = 0
            self.angle = 0
            self.beamframes = 0
            self.active = False
            self.charge = 0
            self.beaming = False
            self.power = maxpower
            self.xvel = self.yvel = 0
            self.goto(500,800)
            self.drawpower()
            
    def shoot(self):
        global shootcool
        
        playsound('laser.wav', tags)

        self.power -= 1
        self.drawpower()
        self.yvel += 1
        self.lastshot = shootcool
        self.bullets.append(bullet(self.x+40*sin(radians(self.angle)),
                                   self.y-40*cos(radians(self.angle)),
                                   self.angle, 18, 'lightgreen', 'green'))
    
    def drawpower(self):
        global maxpower
        for i in range(self.power):
            cv.itemconfig(f'power{i}', state='normal')
        for i in range(self.power, maxpower):
            cv.itemconfig(f'power{i}', state='hidden')  
    
    def update(self):
        global maxpower, meteor, scrhealth, ball, lwidth

        if not self.invinc and meteor and cc(self,meteor, 100):
            self.damage()
            return
        
        if self.lkey in keys:   self.xvel -= self.speed
        elif self.rkey in keys: self.xvel += self.speed
        if self.ukey in keys:   self.yvel -= self.speed
        elif self.dkey in keys: self.yvel += self.speed
        
        self.xvel = clip(self.xvel*0.9, -self.maxspeed, self.maxspeed)
        self.yvel = clip(self.yvel*0.9, -self.maxspeed, self.maxspeed)
        
        beaming = self.beamframes>0 or (self.active and self.pkey in keys and self.invinc==0)
        if beaming:
            self.yvel += 4
            self.move(gauss(0,5)+self.xvel*0.4,gauss(0,1.2)+self.yvel)
            self.beam()
        else:
            self.move(gauss(0,1.5)+self.xvel,gauss(0,1.2)+self.yvel)
        
        
        self.angle = round(self.xvel/self.maxspeed*15)
        cv.itemconfig(self.sprite, image = shipimgs[self.angle])
        
        if self.lastshot == 0:
            if self.skey in keys and self.power>0 and not beaming:
                self.shoot()

        else:   self.lastshot -= 1
        
        if self.power<maxpower:
            self.charge += 1
        
        if self.charge == chargetime:
            self.charge = 0
            if self.power<maxpower:
                self.power += 1
                self.drawpower()

        # Hide/show self, according to invincibilty
        if self.invinc>0:
            if (self.invinc//8)%2==0:
                cv.itemconfig(self.sprite, state='normal')
            else:
                cv.itemconfig(self.sprite, state='hidden')
            self.invinc -= 1
    
        for bullet in self.bullets:
            bullet.move()
            if (not (0<bullet.x<1000 and 0<bullet.y<1000) or
                self.beamframes>0 and abs(bullet.x-self.x)<lwidth+5):
                cv.delete(bullet.sprite)
                self.bullets.remove(bullet)
            elif meteor and cc(bullet,meteor, 70):
                x, y = meteor.xvel, meteor.yvel
                meteor.xvel, meteor.yvel = (x-2/(1+(y/x)**2)**0.5*sign(x*y),
                                            y-2/(1+(x/y)**2)**0.5)
                cv.delete(bullet.sprite)
                self.bullets.remove(bullet)
            else:
                for alien in aliens:
                    if cc(bullet,alien, 50):
                        cv.delete(bullet.sprite)
                        self.bullets.remove(bullet)
                        alien.kill()
                        self.score += 1
                        cv.itemconfig(self.text, text=f'Score: {self.score}')
                        if randint(0,1):
                            alien.drop()
                        break
        
        for scrheart in scrhearts:
            if cc(self, scrheart, 70):
                self.heal()
                scrheart.delete()
        
        if ball and cc(self, ball, 65):
            self.active = True
            ball.delete()

class ufo:
    def __init__(self, x):
        global alspeed, shift, ratio
        self.entry = True
        self.x, self.y = x, -200
        self.angle = 0
        self.speed = 5
        self.dir = randint(0,1)*2-1
        self.lastshot = 0
        self.xvel = self.yvel = 0
        self.sprite = cv.create_image(*conv(self.x, self.y), image=alienimgs[0],
                                      tag='alien')

    def goto(self, x, y):
        self.x, self.y = x, y
        cv.coords(self.sprite, *conv(x,y))
    
    def drop(self):
        global ball
        if randint(0,1) and not player.active and not ball:
            ball = energy(self.x, self.y)
        elif scrhealth<3:
            scrhearts.append(heart(self.x,self.y))
    
    def move(self, x, y):
        if self.x+x<45:         x = 45-self.x
        elif self.x+x>955:      x = 955-self.x
        if not self.entry:
            if self.y+y>450:    y = 450-self.y
            elif self.y+y<45:   y = 45-self.y
        self.goto(x+self.x, self.y+y)
    
    def ai(self):
        global meteor
        objs  = cv.find_enclosed(*conv(self.x-75, self.y+20, self.x+75, self.y+300))
        bulls = cv.find_withtag('green')
        bulls = [obj for obj in objs if obj in bulls]
        shoot = bool(bulls)
        xvel, yvel = self.xvel, self.yvel
        
        if player.beaming and abs(player.x-self.x)<150:
            xvel += sign(self.x-player.x)*self.speed*0.2
            yvel += self.dir*self.speed
        
        elif shoot:
            coords = np.array([cv.coords(bull)[:2] for bull in bulls])
            coords[:,0] -= shift; coords /= ratio;
            i = coords[:,1].argmin()
            xvel += sign(self.x-coords[i,0])*self.speed
            yvel += ((coords[i,1]-self.y>100)*2-1)*self.speed
        
        elif meteor and cc(self,meteor, 230):
            xvel += sign(self.x-meteor.x)*self.speed
            yvel += sign(self.y-meteor.y)*self.speed
            
        elif abs(self.x-player.x)>50:
            if not randint(0,15):
                xvel += sign(player.x-self.x)*self.speed
                yvel += self.dir*self.speed
        else:
            if randint(0,5):    shoot = True
            
            self.xvel += uniform(-1, 1)*self.speed
            self.yvel += uniform(0, 1)*self.speed*self.dir


        mx, my = (-1000,-1000) if not meteor else (meteor.x,meteor.y)
        if (abs(self.x-mx)<50 and self.y<my and meteor.yvel<0) or not randint(0,50):
            shoot = True
            
        if self.y>50:   self.entry = False
        if self.entry:  yvel = (yvel+self.speed)/2
        
        return xvel, yvel, shoot

    def kill(self):
        global player
        aliens.remove(self)
        cv.delete(self.sprite)
        rand = randint(50,950)
        while abs(rand-player.x)<300 and player.beaming:
            rand = randint(50,950)
            
        aliens.append(ufo(randint(50,950)))
        
        if player.score%7 == 0:
            aliens.append(ufo(randint(50,950)))
        
    def shoot(self):
        self.lastshot = alcool
        albulls.append(bullet(self.x-40*sin(radians(self.angle)),
                              self.y+40*cos(radians(self.angle)),
                              self.angle, -albspeed, 'pink', 'red'))
        
    def update(self):
        global meteor, player, alspeed, ball, lwidth
        
        if meteor and cc(self,meteor,100):
            if meteor.yvel<0:
                player.score += 1
                cv.itemconfig(player.text, text=f'Score: {player.score}')
                self.drop()
            self.kill()
            return
        elif player.beaming>0 and abs(self.x-player.x)<lwidth+60 and self.y>-50:
            player.score += 1
            cv.itemconfig(player.text, text=f'Score: {player.score}')
            self.kill()
            return
        
        self.xvel, self.yvel, shoot = self.ai()
        
        if self.lastshot == 0:
            if shoot:
                self.shoot()
        else:
            self.lastshot -= 1
        
        if self.y>445:          self.dir  = -1
        elif self.y<50:         self.dir  =  1
        elif not randint(0,20): self.dir *= -1
        
        self.xvel = max(-alspeed,min(self.xvel*0.9,alspeed))
        self.yvel = max(-alspeed,min(self.yvel*0.9,alspeed))
        self.move(self.xvel,gauss(0,1)+self.yvel)
        
        self.angle = -round(self.xvel/alspeed*15)
        cv.itemconfig(self.sprite, image=alienimgs[self.angle])
            
        cv.tag_raise(self.sprite)

def gameloop():
    global meteor, lwidth
    
    for alien in aliens:
        alien.update()
    
    for heart in scrhearts:
        heart.move()
    
    albullmethod()
    player.update()
    
    if not player.active or player.beaming:
        cv.itemconfig(scrball.sprite, state='hidden')
    else:
        cv.itemconfig(scrball.sprite, state='normal')
        scrball.change()
    
    if meteor:
        meteor.move()
        if (not -70<meteor.y<1070 or
            player.beaming and abs(meteor.x-player.x)<lwidth+65):
            cv.delete(meteor.sprite)
            meteor = False
            
    elif not randint(0,50):
        x = randint(100,900)
        yvel = uniform(5,10)
        xvel = sign(500-x)*uniform(0, abs(x-900)*yvel/1100)
        meteor = rock(x, xvel, yvel)
    
    if ball:    ball.move()
        
    background.shift(1)
    rearrange()

    if gameover:
        screen.after(30, endgame)
    else:
        screen.after(27, gameloop)

def gameinit():
    global gameover, meteor, ball, scrhealth, maxpower, shootcool, chargetime
    global alcool, alspeed, albspeed, maxals, ldivs, lwidth, albulls, aliens
    global scrball, player, scrhearts, background
    
    # Create Gaming Canvas
    cv.create_rectangle(*conv(-3,0,0,1000), fill='gray', outline='')
    cv.create_rectangle(*conv(1000,0,1003,1000), fill='gray', outline='')
    cv.create_text(swidth-shift/2, sheight-60,
                   font=('Century Gothic', int(12*ratio)),
                   anchor='center', text='Created by Shree Singhi\nsinghishree@gmail.com', fill='white')
    
    # Initialize global variables
    gameover = False
    meteor = False
    ball = False
    scrhealth = 3
    
    maxpower = 10
    shootcool = 7
    chargetime = 30
    ldivs = 5
    lwidth = 7*ldivs
    
    alcool = 7
    alspeed = 5
    albspeed = 18
    maxals = 3
    
    # Create objects
    background = stars(100)
    aliens = [ufo(250), ufo(750)]
    albulls= []
    scrhearts = []
    player = ship(500, 800, (65,68,83,87,186,222))
    scrball = energy(-shift/ratio/2, 180, 18)
    cv.itemconfig(scrball.sprite, state='hidden')

def menuloop():
    global bol, brate, blink
    brate += 1
    if (brate//17)%2:
        cv.itemconfig(blink, state='normal')
    else:
        cv.itemconfig(blink, state='hidden')
    
    bol.change()
    if 13 in keys:
        del bol, brate, blink
        cv.delete('all')
        gameinit()
        screen.after(30,gameloop)
    else:
        screen.after(30,menuloop)

def menuinit():
    global bol, blink, brate
    brate = 0
    bol = energy(0, 200, 30)
    cv.create_image(*conv(0,400), image=bheartimg)
    cv.create_text(*conv(100, 400), font=('Consolas', int(25*ratio)),
                   text='Aliens will drop this occasionally\n'
                        'Collect it to regain health', fill='white', anchor='w')
    cv.create_text(*conv(100, 220), font=('Consolas', int(25*ratio)),
                   text='Aliens will drop this occasionally\n'
                        'USE IT TO SHOOT A BLOODY BEAM THAT\n'
                        'ANNHILATES ALL OF HUMANITY', fill='white', anchor='w')
    cv.create_text(*conv(500, 600), text='Move using WASD, and shoot using the ; key\n'
                                       '    Use the death beam with the \' key',
                   font=('Consolas', int(35*ratio)), fill='white', anchor='center')
    cv.create_text(swidth-10, sheight-10, text='the ai is quite dope, so good luck',
                   font=('Consolas', int(6*ratio)), fill='white', anchor='se')
    
    blink = cv.create_text(*conv(500, 900), text='[Press enter to continue]',
                   font=('Consolas', int(30*ratio)), fill='light gray', anchor='center')

def screeninit():
    global keys, swidth, sheight, ratio, shift, screen, cv, shipimgs, heartimg
    global bheartimg, bombimgs, rockimgs, alienimgs, yodudeimg, goverimg, windll
    
    keys = []
    # Get screen coors, create convertion variables
    swidth, sheight = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)
    del windll
    ratio = sheight/1000               #divides height and width intos 1000 units
    shift = swidth/2-sheight/2         #add shift to all x
    
    # Setup root window and canvas
    screen = Tk()
    screen.title('Space Invaders')
    screen.geometry(f'{swidth}x{sheight}+0+0')
    screen.attributes('-fullscreen', True)
    screen.bind('<Escape>', lambda foo: screen.destroy())
    screen.bind('<KeyPress>', keydown)
    screen.bind('<KeyRelease>', keyup)
    screen.focus_set()
    # screen.attributes('-alpha', 0.5)
    cv = Canvas(screen, width=swidth, height=sheight, bg='black')
    cv.pack()
    
    # Create image files
    temp     = [resize('ship2.png', 0.15*ratio, angle) for angle in range(-15,16)]
    shipimgs = dict(zip(list(range(-15,16)), temp))
    heartimg = resize('heart.png', 1.1*ratio)
    bheartimg= resize('heart.png', 2*ratio)
    bombimgs = [resize(f'bomb\ ({i}).gif', 0.2*ratio, 0) for i in range(1,8)]
    rockimgs = [resize('smallrock.png', 0.7*ratio, angle) for angle in range(0,360,36)]
    temp     = [resize('alien.png', 0.7*ratio, angle) for angle in range(-15,16)]
    alienimgs= dict(zip(list(range(-15,16)), temp))
    yodudeimg= resize('yodude.png', 2*ratio, 0)
    goverimg = resize('endgame.png', 2*ratio, 0)
    del temp

screeninit()
menuinit()
menuloop()
mainloop()
