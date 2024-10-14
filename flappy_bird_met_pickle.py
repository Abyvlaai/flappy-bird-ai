
import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init()  # init font

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

gen = 0

class Bird:
    """
    Bird class representing the flappy bird
    """
    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        make the bird move
        :return: None
        """
        self.tick_count += 1

        # for downward acceleration
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # calculate displacement

        # terminal velocity
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        draw the bird
        :param win: pygame window or surface
        :return: None
        """
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2


        # tilt the bird
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.img)


class Pipe():
    """
    represents a pipe object
    """
    GAP = 160
    VEL = 5

    def __init__(self, x):
        """
        initialize pipe object
        :param x: int
        :param y: int
        :return" None
        """
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        set the height of the pipe, from the top of the screen
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        move pipe based on vel
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        draw both the top and bottom of the pipe
        :param win: pygame window/surface
        :return: None
        """
        # draw top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self, bird, win):
        """
        returns if a point is colliding with the pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if b_point or t_point:
            return True

        return False

class Base:
    """
    Represnts the moving floor of the game
    """
    VEL = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        move floor so it looks like its scrolling
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotate a surface and blit it to the window
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param bird: a Bird object
    :param pipes: List of pipes
    :param score: score of the game (int)
    :param gen: current generation
    :param pipe_ind: index of closest pipe
    :return: None
    """
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    11. genomes, config toevoegen als parameters die nodig zijn. Want wanneer je een fitness functie maakt
    voor neat moet je ervoor zorgen dat je genomen en de config als parameters hebt omdat ze anders niet
    worden opgeroepen.
    wat de functie zelf doet: voert de simulatie uit van de huidige populatie van
    vogels en stelt hun conditie in op basis van de afstand die ze afleggen
    bereiken in het spel.
    """
    global WIN, gen
    win = WIN
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    "16. nets = [] toevoegen zorgt ervoor dat we de vogels kunnen bijhouden die het neurale netwerk bestuurt"
    "dus ook wat hun positie is op het scherm"
    
    "17 ge = [] is om de genomen bij te houden en wat hun fitness is en hoe ze kunnen aanpassen gebaseerd"
    "op hoe ze bewegen en hoever ze komen en/of ze iets raken"
   
    "12. birds = [] zorgt ervoor dat op alle vogels in de array tegelijk"
    "de functie eval_genomes wordt uitgevoerd"
    nets = []
    birds = []
    ge = []
    
    "18.voor elk genoom in de genomenlijst geldt de volgende: "
    "bij net = neat.nn...... wordt het genoom en config opgeroepen in het feedforwards network"
    "nets.append een neuraal netwerk wordt toegevoegd in de nets list"
    "birds.append zorgt ervoor dat alle vogels op dezelfde positie beginnen"
    "ge.append zorgt ervoor dat het genoom in de genomenlijst komt"
    "genome.fitness wordt gelijkgesteld aan 0"
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)
        
        
        with open("best.pickle","rb") as f:
            nets = [pickle.load(f)]
        with open("best_genome.pickle","rb") as f:
            ge = [pickle.load(f)[1]]
            birds = [birds[0]]
            
        
        

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(100)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # determine whether to use the first or second
                pipe_ind = 1                                                                 # pipe on the screen for neural network input
        
        "22. We stellen de pipe index op 0, dit betekent dat we gaan kijken naar de input voor ons neurale netwerk. We kijken of de lengte van de vogels gelijk is aan 0"
        " birds[0].x > pipes[0] Dit checkt dus of de vogels de pijp hebben gepasseerd"
        
        "#21. for x, bird in enumerate(birds): geeft elke vogel een fitness van 0.1 voor elke frame die ze levend blijven"
        for x, bird in enumerate(birds):  
            ge[x].fitness += 0.1
            bird.move()
            
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            
            if output[0] > 0.5:  # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()
            #23. ge[x].fitness += 0.1 dit zorgt ervoor dat de vogels meer fitness krijgen, dit resulteert in meer motivatie voor de vogels om door te gaan"
            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not        
            
            #25. output=nets..... stuurt de locatie van de vogel, stuurt de locatie van de bovenste en onderste pijp en bepalen vanuit het neurale netwerk om te springen of niet"
            
      
            #24.if output[0] > 0.5 We gebruiken hier de tanH functie zodat het resultaat tussen -1 en 1 is, als de waarde boven 0.5 ligt betekent het voor de vogels :spring"

            base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # check for collision
            
            "13. for bird in birds (hoort bij punt 12) zorgt ervoor dat er voor elke bird in de array de genome functie wordt toegepast "
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))
            """19. ge[birds.index(bird)].fitness -= 1 dit toevoegen zorgt ervoor dat elke keer wanneer een vogel een pijp raakt
            dat er 1 van de fitness score af gaat dit is zodat de vogels die ver komen niet opeens tegen de pijpen aan gaan
            kort gezegd leren de vogels die niet tegen de pijp aan gaanvan de vogels die wel tegen de pijpen aan zijn gebotst"
            deze overgebleven vogels krijgen dus een hogere fitness score"""
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            "13. if not pipe.passed .... checkt of elke pijp botst met elke vogel."
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
        "14. pipe.passed = true en add_pipe = true checken of de vogels de pijp hebben gepasseerd"
        
        if add_pipe:
            score += 1
            # can add this line to give more reward for passing through a pipe (not required)
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))
            "21. genome.fitness += 5 zorgt ervoor dat de vogels die door de pijpen heen gaan"
            "steeds slimmer worden en dus niet dood gaan bij elk volgende level"

        for r in rem:
            pipes.remove(r)
        
        "15. for bird in birds if bird y....... dit checkt of de vogel de grond raakt" 
        
        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))
           #27. if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50 zorgt ervoor dat de vogel worden dood gaan wanneer ze boven het scherm vliegen"              
            """
            20. nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird)))
                dit zorgt ervoor dat de vogels neurale netwerken en genomen worden weggehaald uit de index
            """



        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # break if score gets large enough
        if score > 25:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            pickle.dump(genomes[0], open("best_genome.pickle","wb"))
            pygame.quit()

def run(config_file):
    
    
    """
    1.
    voert het NEAT-algoritme uit om een ​​neuraal netwerk te trainen om flappy bird te spelen.
    :param config_file: locatie van configuratiebestand
    :return: Geen

    """
    """
    5.config =neat.config ..... dit  defineerd al de subheadings die in het configfeedworward bestand
    zitten zoals DefaultGenome, DefaultSpeciesSet, DefaultReproduction, DefaultStagnation.
    Wat we eigenlijk dus doen is we vertellen tegen de config file de eigenschappen die we in het bestand
    hebben gegeven.
    Neat.neat hoeft hier niet per se bij omdat het code niet runnt zonder de NEAT subheading.
    
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    #6. p = neat.Population(config) Maak de populatie. Dit is het object op het hoogste niveau voor een NEAT-run.
    #Dit isgebaseerd op wat voor eigenschappen in de configfile zitten door de subheadings
    p = neat.Population(config)
    """
     Add a stdout reporter to show progress in the terminal.
    7. Dit geeft ons output dus wanneer we het algoritme uitvoeren, in plaats van dat we niet zien wat er gebeurt
    in de console, hierdoor zien wij gedetailleerde statistieken over elke generatie en wat de beste fitness is nu 
    """
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
   
    """
    8. p.add_reporter(stats) geeft ons de output van de statistieken dit stelt de population dus de groep in
    
    """
  
    """
    9. winner =p.run(...) Het progamma blijft runnen totdat er 50 generaties vogels zijn geweest
    """
    winner = p.run(eval_genomes, 50)
    """
    10. we hebben hier eval_genomes toegevoegd in de p.run functie zodat de eval_genomes functie 50 keer oproepen
    en het doorgeven aan alle genomen dus vogels. Dus hierdoor kan ook de huidige generatie vogels en ook de config file
    elke keer geupdate worden. En vervolgens wordt er dus een game gegenereerd gebaseerd op alle vogels die het
    genoom ontvangen.
    """
    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    #2. local_dir.... toevoegen geeft ons het pad naar de directory waar we nu in zittten
    #omdat we dat moeten gebruken om het configuratiebestand te laden ongeacht de huidige werkmap
    
    #3. config_path ... toevoegen dit zorgt ervoor dat we het exacte pad naar het configuratie bestand krijgen wat we nodig hebben
    
    #4. run(config_path) toevoegen om het config path uit te voeren
    local_dir = os.path.dirname(__file__) 
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
    
    pygame.quit()
    
    

