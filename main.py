"""Alpha Pop---an alphabet learning game

Alphapop is a kid's game to help kids learn to recognize letters in 
different cases and fonts.

A bunch of bubbles with letters inside them float around the screen and
the player is asked to pop the bubble containing a specific letter.
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
    """Bubbles are the main on-screen objects in this game

    When a Bubble is created, it generates an image (with transparency)
    of itself and keeps track of the current position of the top-left
    corner of this image as well as its current direction of travel
    """
    image = pygame.image.load(os.path.join('images', 'bubble-large.png'))
    rectangle = image.get_rect()

    def __init__(self, letter, font, radius, position, direction):
        """Initialize instance variables and create an image"""
        self.letter = letter.lower()
        self.radius = radius
        self.position = position
        self.direction = direction

        # setup the image of this bubble
        diam = 2*radius
        self.image = pygame.Surface((diam, diam), pygame.SRCALPHA)
        text = font.render(letter, True, Game.WHITE)
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

    # Refresh rate
    FPS = 30

    # User-defined event types
    REFRESH_EVENT = pygame.USEREVENT
    ANNOUNCE_EVENT = pygame.USEREVENT+1
    BRAVO_EVENT = pygame.USEREVENT+2

    # Colours
    WHITE = (255, 255, 255, 255)

    # UI states
    PLAY_STATE, ANNOUNCE_STATE, BRAVO_STATE = 1, 2, 3

    # Play modes
    UPPERCASE_MODE, MIXEDCASE_MODE, LOWERCASE_MODE = 0, 1, 2

    def __init__(self):
        """Initialize this game"""

        # Set the screen size---go fullscreen on android.
        info = pygame.display.Info()        
        if android:
            self.size = (info.current_w, info.current_h)
        else:
            self.size = (800, 480)
        self.width, self.height = self.size
        self.screen = pygame.display.set_mode(self.size)

        # We develop and test at 800x480, so scale things if needed.
        scale = max(self.width, self.height)/800

        # Map the back button to the escape key.
        if android:
            android.init()
            android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)

        # Load fonts.
        self.announce_font = pygame.font.SysFont(None, int(200*scale))
        self.reminder_font = pygame.font.SysFont(None, int(40*scale))
        for root, dirs, files in os.walk('fonts'):
            fontfiles = [os.path.join(root, filename) for filename in files
                            if filename.lower().endswith("ttf")]
            self.fonts = [pygame.font.Font(f, int(60*scale)) for f in fontfiles]
        self.fonts.append(pygame.font.SysFont(None, int(60*scale)))

        # Load backgrounds.        
        for root, dirs, files in os.walk('backgrounds'):
            self.backgrounds = \
                [os.path.join(root, filename) for filename in files
                 if filename.lower().endswith("jpg")]
        random.shuffle(self.backgrounds)
        self.bg_img = self.load_background(self.backgrounds[0])

        # Load common sounds.
        self.pop_sound = self.load_sound('pop.wav')
        self.wrong_sound = self.load_sound('wrong.wav')
        self.soundtrack = self.load_sound('soundtrack.wav')
        
        # Set up UI variables.
        self.pad = int(scale*10)
        self.bubble_radius = int(min(self.width, self.height)/8)

        # Initialize mode---uppercase, mixed-case or lowercase
        self.mode = Game.UPPERCASE_MODE
        modefont = pygame.font.SysFont(None, int(20*scale)) 
        text = modefont.render('A', True, Game.WHITE)
        diam = int(text.get_height()*1.44)
        bubble = pygame.transform.smoothscale(Bubble.image, (diam, diam))
        self.mode_imgs = []
        for txt in ['A', 'Aa', 'a']:
            textcase = modefont.render(txt, True, Game.WHITE)
            img = pygame.Surface((diam, diam), pygame.SRCALPHA)
            blit_centered(img, textcase)
            img.blit(bubble, bubble.get_rect())
            self.mode_imgs.append(img)

        # Make a bunch of bubble images.
        img = pygame.Surface((diam, diam), pygame.SRCALPHA)
        blit_centered(img, text)

        img.blit(bubble, img.get_rect())
        self.bubble_imgs = []
        for i in range(1, 9):
            img2 = pygame.Surface((diam*8, diam), pygame.SRCALPHA)
            rect = img.get_rect();
            for j in range(8):
                img2.blit([bubble, img][j < i], rect)
                rect = rect.move(diam, 0)
            self.bubble_imgs.append(img2)


        # Use this to keep track of the next letter
        self.next_letter = 0

        # Use this to keep track of the number of correct answers
        self.correct = 0

        # Permute the alphabet and make the first few bubbles
        self.alphabet = [c for c in "abcdefghijklmnopqrstuvwxyz"]
        random.shuffle(self.alphabet)
        self.bubbles = []
        for i in range(4):
            self.bubbles.append(self.make_bubble())

            
        # Pick the first target and announce it.
        self.target = random.randrange(len(self.bubbles))
        self.announce_target()

    def load_image(self, filename):
        """Load an image file to get a pygame.Surface object"""
        return pygame.image.load(os.path.join('images', filename))

    def load_background(self, filename):
        """Load a background image to get a pygame.Surface object"""
        img = pygame.image.load(filename)
        return self.fit_image(img, self.width, self.height)

    def load_sound(self, filename):
        """Load a sound file to get a pygame.mixer.Sound object"""
        return mixer.Sound(os.path.join("sounds", filename))

    def announce_target(self):
        """Announce a new target letter"""
        letter = self.bubbles[self.target].letter
        question = self.load_sound("question-" + letter + ".wav")
        question.play()
        if android: # get_length() not supported by android.mixer
            ms = 2000  
        else:
            ms = int(question.get_length()*1000)
        pygame.time.set_timer(Game.ANNOUNCE_EVENT, ms)
        self.state = Game.ANNOUNCE_STATE

    def make_bubble(self):
        """Generate a new bubble"""
        radius = self.bubble_radius

        # Appear somewhere that doesn't interfere with any existing bubble
        rangex = self.width - 2*radius
        rangey = self.height - 2*radius
        retry = True
        while retry:
            retry = False
            position = [random.randrange(rangex), random.randrange(rangey)]
            center = [position[i]+radius for i in range(2)]
            for b in self.bubbles:
                if distance(b.center(), center) < b.radius + radius:
                    retry = True
                    break

        # Move in a random direction
        theta = random.random()*2*math.pi
        direction = [math.cos(theta), math.sin(theta)]

        # Choose the letter and case
        letter = self.alphabet[self.next_letter%len(self.alphabet)]
        self.next_letter += 1
        if self.mode == Game.UPPERCASE_MODE:
            letter = letter.upper()
        elif self.mode == Game.MIXEDCASE_MODE:
            letter = random.choice([letter.upper(), letter.lower()])
        else:
            letter = letter.lower()

        # Choose the font  
        font = random.choice(self.fonts)

        return Bubble(letter, font, self.bubble_radius, position, direction)

    def run(self):
        """The game's main loop"""
        self.soundtrack.play(-1, 0, 2000)
        pygame.time.set_timer(Game.REFRESH_EVENT, 1000 // Game.FPS)

        while 1 < 2:
            event = pygame.event.wait()

            # Android-specific: always be ready to sleep
            if android:
                if android.check_pause():
                    android.wait_for_resume()

            # Refresh display
            if event.type == Game.REFRESH_EVENT:
                # Android-specific: keep the soundtrack playing
                if android:
                    android.mixer.periodic()

                self.draw()
                self.physics()
                pygame.display.flip()

            # The announcement is over---start playing
            elif event.type == Game.ANNOUNCE_EVENT:
                pygame.time.set_timer(Game.ANNOUNCE_EVENT, 0)
                self.state = Game.PLAY_STATE

            # The congratulations is over---announce new target
            elif event.type == Game.BRAVO_EVENT:
                pygame.time.set_timer(Game.BRAVO_EVENT, 0)
                self.announce_target()

            # The user clicked somewhere
            elif event.type == pygame.MOUSEBUTTONDOWN \
                    and self.state != Game.BRAVO_STATE:
                self.clicked(event.pos)

            # The user hit escape (or back); quit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                break

    def get_mode_rect(self):
        """Get the rectangle that contains this game's mode indicator"""
        rect = self.mode_imgs[self.mode].get_rect()
        return rect.move (self.width-rect.width-self.pad, 
                          self.height-rect.height-self.pad)

    def get_bubbles_rect(self):
        """Get the rectangle that contains the bubble count indicator"""
        rect = self.bubble_imgs[len(self.bubbles)-1].get_rect()
        return rect.move(self.pad, self.height-rect.height-self.pad)

    def draw(self):
        """Draw this game's display"""
        
        # First the background image
        self.screen.blit(self.bg_img, self.bg_img.get_rect())

        """rect = pygame.Rect(0, 0, self.width, 
                        2*self.pad+self.mode_imgs[0].get_height())
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (75, 75, 75, 75), rect)
        self.screen.blit(surf, surf.get_rect())"""

        # Then all the bubbles
        for b in self.bubbles:
            # draw this bubble
            rect = b.image.get_rect()
            rect = rect.move(int(b.position[0]), int(b.position[1]))
            self.screen.blit(b.image, rect)
            c = [int(x) for x in b.center()]

        # Then the mode
        self.screen.blit(self.mode_imgs[self.mode], self.get_mode_rect())

        # Then the bubble count
        self.screen.blit(self.bubble_imgs[len(self.bubbles)-1],
                         self.get_bubbles_rect())

        # Finally, draw the announcement
        if self.state == Game.ANNOUNCE_STATE:
            letter = self.bubbles[self.target].letter.upper()
            text = self.announce_font.render(letter, True, Game.WHITE)
            rect = text.get_rect()
            rect = rect.move((self.width-rect.width)//2,
                             (self.height-rect.height)//2)
            self.screen.blit(text, rect)
        elif self.state == Game.PLAY_STATE:
            letter = self.bubbles[self.target].letter.upper()
            text = self.reminder_font.render(letter, True, Game.WHITE)
            rect = text.get_rect()
            rect = rect.move(self.pad, self.pad)
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
            b.position = [b.position[i] + b.direction[i]*speed
                            for i in range(2)]
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
        """The user clicked at location pos, see if they hit the target"""

        b = self.bubbles[self.target]

        # The user clicked the target bubble
        if distance(pos, b.center()) < b.radius:

            self.pop_sound.play()
            letter = b.letter
            bravo = self.load_sound("bravo-" + letter + ".wav")
            bravo.play()
            self.bubbles[self.target] = self.make_bubble()

            # After every 7 correct answers we change the background
            self.correct += 1
            if self.correct % 7 == 0:
                i = (self.correct//7) % len(self.backgrounds)
                self.bg_img = self.load_background(self.backgrounds[i])
            self.target = random.randrange(len(self.bubbles))
            self.state = Game.BRAVO_STATE
            if android:
                ms = 2000  # get_length() not supported by android.mixer
            else:
                ms = int(bravo.get_length()*1000)
            pygame.time.set_timer(Game.BRAVO_EVENT, ms)

        # User clicked the mode indicator---adjust the font choice
        elif self.get_mode_rect().collidepoint(pos):
            self.mode = (self.mode + 1) % len(self.mode_imgs)

        # User clicked the bubble count indicator---adjust the number of bubbles
        elif self.get_bubbles_rect().collidepoint(pos):
            rect = self.get_bubbles_rect()
            maxn = len(self.bubble_imgs)
            n = 1+ int( ((pos[0] - rect.left)/rect.width) * maxn)
            n = int(max(1, min(n, maxn)))
            n = max(n, 1)
            n = int(n)
            self.bubbles[self.target], self.bubbles[0] \
                    = self.bubbles[0], self.bubbles[self.target]
            self.target = 0
            while len(self.bubbles) < n:
                self.bubbles.append(self.make_bubble())
            while len(self.bubbles) > n:
                i = random.randrange(1, len(self.bubbles))
                self.bubbles[i], self.bubbles[len(self.bubbles)-1] \
                    = self.bubbles[len(self.bubbles)-1], self.bubbles[i]
                del self.bubbles[len(self.bubbles)-1]
            
        # User clicked somewhere else
        else: 
            self.wrong_sound.play()
            if android:
                android.vibrate(1)
            for i in range(len(self.bubbles)):
                b = self.bubbles[i]
                if distance(pos, b.center()) < b.radius:
                    # user clicked wrong bubble, pop it anyway
                    self.pop_sound.play()
                    self.bubbles[i] = self.make_bubble()


def main():
    Game().run()


# This isn't run on Android.
if __name__ == "__main__":
    main()

