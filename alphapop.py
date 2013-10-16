"""Alpha Pop---an alphabet learning game

A kid's game to help kids learn to recognize letters in different cases
and fonts.
"""
from __future__ import division

import pygame
import math
import random
import os


# Import the android module. If we can't import it, set it to None - this
# lets us test it, and check to see if we want android-specific behavior.
try:
    import android
except ImportError:
    android = None

try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


# initialize pygame
pygame.init()


# the following methods do vector arithmetic on points
def distance(a, b):
    """Return the distance between two points a and b"""
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def sub(a, b):
    """Return the vector difference between a and b"""
    return [a[i] - b[i] for i in range(2)]

def add(a, b):
    """Return the vector difference between a and b"""
    return [a[i] + b[i] for i in range(2)]


def prod(a, x):
    """Return the vector a divided by the scalar x"""
    return [a[i]*x for i in range(2)]


def div(a, x):
    """Return the vector a divided by the scalar x"""
    return [a[i]/x for i in range(2)]


def dot(a, b):
    """Return the dot product (scalar product) of a and b"""
    return sum([a[i]*b[i] for i in range(2)])


def neg(a):
    """Return the negation of a"""
    return prod(a, -1)


def norm(a):
    """Return the norm of the point/vector a"""
    return distance((0, 0), a)

def blit_centered(surface1, surface2):
    """Blit surface2, centered, onto surface1"""
    rect = surface2.get_rect()
    rect = rect.move((surface1.get_width()-rect.width)//2,
                     (surface1.get_height()-rect.height)//2)
    surface1.blit(surface2, rect)

class Bubble(object):
    """Bubbles are the main on-screen objects in this game"""
    image = pygame.image.load(os.path.join('images', 'bubble-large.png'))
    rectangle = image.get_rect()
    font = pygame.font.SysFont(None, 40)


    def __init__(self, letter, radius, position, direction):
        self.letter = letter
        self.radius = radius
        self.position = position
        self.direction = direction
        diam = 2*radius
        # setup an image of this bubble
        self.image = pygame.Surface((diam, diam), pygame.SRCALPHA)
        if random.randrange(2):
            c = letter.upper()
        else:
            c = letter.lower()
        text = Bubble.font.render(c, True, Game.WHITE)
        blit_centered(self.image, text)
        bubble = pygame.transform.smoothscale(Bubble.image, (diam, diam))
        self.image.blit(bubble, self.image.get_rect())


    def diameter(self):
        """Return the diameter of this bubble"""
        return 2 * self.radius


    def center(self):
        """Return the center of this bubble"""
        return [self.position[i]+self.radius for i in range(2)]
        
class Game(object):
    """Encapsulates our newly-created game"""

    # global constants
    FPS = 30
    REFRESH_EVENT = pygame.USEREVENT
    ANNOUNCE_EVENT = pygame.USEREVENT+1
    BRAVO_EVENT = pygame.USEREVENT+2
    BLACK = (0, 0, 0, 255)
    RED = (255, 0, 0, 255)
    WHITE = (255, 255, 255, 255)
    PLAY_STATE = 1
    ANNOUNCE_STATE = 2
    BRAVO_STATE = 3


    def __init__(self):
        """Initialize this game"""

        info = pygame.display.Info()        

        # Set the screen size.
        if android:
            size = (info.current_w, info.current_h)
        else:
            size = (800, 480)

        self.size = size
        self.width, self.height = size[0], size[1]
        self.screen = pygame.display.set_mode(size, pygame.DOUBLEBUF)

        # Map the back button to the escape key.
        if android:
            android.init()
            android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)

        # Load resources
        self.announce_font = pygame.font.SysFont(None, 200)

        img = self.load_image('background.jpg')
        self.bg_img = self.fit_image(img, self.width, self.height)

        self.pop_sound = self.load_sound('pop.wav')
        self.wrong_sound = self.load_sound('wrong.wav')
        self.soundtrack = self.load_sound('soundtrack.wav')
        
        self.bubble_radius = min(self.width, self.height)//8

        self.duration = 0
        self.alphabet = [c for c in "abcdefghijklmnopqrstuvwxyz"]
        random.shuffle(self.alphabet)
        self.next = 0
        self.bubbles = []
        for i in range(3):
            self.bubbles.append(self.make_bubble())
        self.target = random.randrange(len(self.bubbles))
        self.announce_target()


    def load_image(self, filename):
        """Load an image file to get a pygame.Surface object"""
        return pygame.image.load(os.path.join('images', filename))


    def load_sound(self, filename):
        """Load a sound file to get a pygame.mixer.Sound object"""
        return pygame.mixer.Sound(os.path.join("sounds", filename))


    def announce_target(self):
        """Announce a new target letter"""
        letter = self.bubbles[self.target].letter
        question = self.load_sound("question-" + letter + ".wav")
        self.soundtrack.set_volume(0.1)
        question.set_volume(1)
        question.play()
        ms = int(question.get_length()*1000)
        pygame.time.set_timer(Game.ANNOUNCE_EVENT, ms)
        self.state = Game.ANNOUNCE_STATE


    def make_bubble(self):
        """Generate a new bubble"""
        radius = self.bubble_radius
        diam = 2*radius
        rangex = self.width - diam
        rangey = self.height - diam
        position = []
        retry = True
        while retry:
            retry = False
            position = [ random.randrange(rangex), random.randrange(rangey) ]
            center = [position[i]+self.bubble_radius for i in range(2)]
            for b in self.bubbles:
                if distance(b.center(), center) < b.radius + radius:
                    retry = True
                    break
        theta = random.random()*2*math.pi
        direction = [ math.cos(theta), math.sin(theta) ]
        letter = self.alphabet[self.next]
        self.next = (self.next + 1) % len(self.alphabet)
        return Bubble(letter, self.bubble_radius, position, direction)


    def run(self):
        """The game's main loop"""
        self.soundtrack.set_volume(0.3)
        self.soundtrack.play(-1, 0, 2000)
        pygame.time.set_timer(Game.REFRESH_EVENT, 1000 // Game.FPS)

        while 1 < 2:
            event = pygame.event.wait()

            # Android-specific:
            if android:
                if android.check_pause():
                    android.wait_for_resume()

            # Refresh display
            if event.type == Game.REFRESH_EVENT:
                self.draw()
                self.physics()
                pygame.display.flip()

            # announcement is over---start playing and turn up the volume
            elif event.type == Game.ANNOUNCE_EVENT:
                pygame.time.set_timer(Game.ANNOUNCE_EVENT, 0)
                self.soundtrack.set_volume(.3)
                self.state = Game.PLAY_STATE

            # congratulations is over---announce new target
            elif event.type == Game.BRAVO_EVENT:
                pygame.time.set_timer(Game.BRAVO_EVENT, 0)
                self.announce_target()

            # the user clicked somewhere
            elif event.type == pygame.MOUSEBUTTONDOWN \
                    and self.state != Game.BRAVO_STATE:
                self.clicked(event.pos)

            # User hit escape (or back); quit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                break


    def draw(self):
        """Draw this game's display"""
        
        # first the background image
        self.screen.blit(self.bg_img, self.bg_img.get_rect())

        # then all the bubbles
        for b in self.bubbles:
            # draw this bubble
            rect = b.image.get_rect()
            rect = rect.move(int(b.position[0]), int(b.position[1]))
            self.screen.blit(b.image, rect)
            c = [int(x) for x in b.center()]
        
        # the announcement, if appropriate
        if self.state == Game.ANNOUNCE_STATE:
            letter = self.bubbles[self.target].letter.upper()
            text = self.announce_font.render(letter, True, Game.WHITE)
            rect = text.get_rect()
            rect = rect.move((self.width-rect.width)//2,
                             (self.height-rect.height)//2)
            self.screen.blit(text, rect)


    def fit_image(self, img, width, height):
        """Return an image that is scaled and cropped to the given size"""
        if img.get_height()/height > img.get_width()/width:
            # scale is determined by width
            w = width
            h = int(math.ceil(img.get_height() * (w/img.get_width())))
        else:
            # scale is determined by height
            h = height
            w = int(math.ceil(img.get_width() * (h/img.get_height())))
        img = pygame.transform.smoothscale(img, (w,h))
        rect = img.get_rect()
        rect = rect.move((width-w)//2, (height-h)//2)
        img2 = pygame.Surface((width, height))
        img2.blit(img, rect)
        return img2


    def physics(self):
        """Do the in-game physics"""
        # bubbles moves
        for b in self.bubbles:
            speed = self.height/(5*Game.FPS)
            b.position = [b.position[i] + b.direction[i]*speed for i in range(2)]
        # bubbles bounce off walls
            for i in range(2):
                if b.position[i] < 0 and b.direction[i] < 0: 
                    b.direction[i] = -b.direction[i]
                elif b.position[i] + b.diameter() > self.size[i] \
                     and b.direction[i] > 0:
                    b.direction[i] = -b.direction[i]
        # bubbles bounce off each other
        for i in range(len(self.bubbles)):
            bi = self.bubbles[i]
            ci = bi.center()
            for j in range(i+1, len(self.bubbles)):
                bj = self.bubbles[j]
                cj = bj.center()
                dij = distance(ci, cj)
                if dij < bi.radius + bj.radius:
                    vij = div(sub(cj, ci), dij)
                    tij = prod(vij, dot(vij, bi.direction))
                    tji = prod(vij, dot(vij, bj.direction))
                    bj.direction = add(bj.direction, tij)
                    bi.direction = sub(bi.direction, tij)
                    bi.direction = add(bi.direction, tji)
                    bj.direction = sub(bj.direction, tji)


    def clicked(self, pos):
        """The user clicked at location pos"""
        b = self.bubbles[self.target]
        if distance(pos, b.center()) < b.radius:
            # user clicked the target bubble
            self.pop_sound.play()
            letter = b.letter
            bravo = self.load_sound("bravo-" + letter + ".wav")
            self.soundtrack.set_volume(0.1)
            bravo.set_volume(1)
            bravo.play()
            self.bubbles[self.target] = self.make_bubble()
            self.duration += 1
            if self.duration % 7 == 0 and len(self.bubbles) < 8:
                self.bubbles.append(self.make_bubble())
            self.target = random.randrange(len(self.bubbles))
            self.state = Game.BRAVO_STATE
            ms = int(bravo.get_length()*1000)
            pygame.time.set_timer(Game.BRAVO_EVENT, ms)
        else:
            self.wrong_sound.play()            

def main():
    Game().run()


# This isn't run on Android.
if __name__ == "__main__":
    main()

