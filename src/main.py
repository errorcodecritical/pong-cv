import pygame
import numpy as np
import cv2
import random
import time
import mediapipe

from transform import Transform2D
from pygame.math import Vector2 as Vector2

mp_drawing = mediapipe.solutions.drawing_utils
mp_drawing_styles = mediapipe.solutions.drawing_styles
mp_hands = mediapipe.solutions.hands

def lerp(a, b, c):
    return a + (b - a) * c

def map(x, a, b, c, d):
    return (x - a) * (d - c) / (b - a) + c

def rand(a, b):
    return map(random.random(), 0, 1, a, b)

def raycastBox(ray_origin, ray_direction, boundary_min, boundary_max):
    t0 = (boundary_min[0:2] - ray_origin[0:2]) / ray_direction[0:2]
    t1 = (boundary_max[0:2] - ray_origin[0:2]) / ray_direction[0:2]

    tMin = np.minimum(t0, t1)
    tMax = np.maximum(t0, t1)
    
    return (
        np.maximum(tMin[0], tMin[1]),
        np.minimum(tMax[0], tMax[1])
    )

#MACRO

GREEN = (0, 255, 30)
BLUE = (0, 0, 128)
RED = (255, 65, 0)
WHITE = (255, 255, 255)

COUNTDOWN_DURATION = 5
GAME_DURATION = 30
NUMBER_OF_ROUNDS = 3
PLAYER_MAX_POINTS = 100
CAMERA_CORRECTION = -30

BALL_MIN_VELOCITY = 200
BALL_MAX_VELOCITY = 800

class GameObject:
    transform = None
    geometry = None
    velocity = None
    visible = None
    transparency = None
    collisions = None

    def __init__(self, visible = True, transparency = 0, collisions = True):
        self.transform = Transform2D()
        self.geometry = pygame.Surface((0, 0))
        self.velocity = Vector2(0, 0)
        self.visible = visible
        self.transparency = transparency
        self.collisions = collisions

class GameContainerClass:
    # Game hierarchy & states
    window = {
        "instance" : None,
        "size" : Vector2(1280, 720)
    }
    camera = {
        "instance" : None,
        "detector" : None,
        "frame" : None
    }
    players = {
        "player1" : {
            "target" : Vector2(0, 0),
            "tracking" : False,
            "ready" : False,
            "points" : 0
        },
        "player2" : {
            "target" : Vector2(0, 0),
            "tracking" : False,
            "ready" : False,
            "points" : 0
        }
    }
    scene = {}

    running = False
    tick = time.monotonic()
    game_time = 0
    countdown_time = 0
    round = 0

    state = "reset"
    
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Deec x Pong!')
        
        self.window["instance"] = pygame.display.set_mode(
            (self.window["size"].x, self.window["size"].y)
        )

        self.window["instance"].fill((22, 33, 44))
        
        self.camera["instance"] = cv2.VideoCapture(0)
        self.camera["instance"].set(3, self.window["size"].x)
        self.camera["instance"].set(4, self.window["size"].y)

        self.camera["detector"] = mp_hands.Hands(
            model_complexity = 0,
            min_detection_confidence = 0.5, 
            min_tracking_confidence = 0.5
        )

        self.players["player1"]["target"] = 0.5 * self.window["size"]
        self.players["player2"]["target"] = 0.5 * self.window["size"]

    def menu_load(self):
        self.scene = {
            "title" : GameObject(),
            "subtitle" : GameObject(),
            "credits" : GameObject(),
            "ready_player1" : GameObject(visible=False, transparency=0.1),
            "ready_player2" : GameObject(visible=False, transparency=0.1),
            "selector_player1" : GameObject(transparency=0.1),
            "selector_player2" : GameObject(transparency=0.1),
        }

        self.scene["title"].geometry = pygame.image.load("assets/landing_title.png")
        self.scene["subtitle"].geometry = pygame.font.SysFont('arial', 25).render('slapper edition', True, WHITE, None)
        self.scene["credits"].geometry = pygame.font.SysFont('arial', 20).render(
            'Developed by: Code-Critical & Disreaper', True, WHITE, None
        )

        self.scene["ready_player1"].geometry = pygame.font.SysFont('arial', 32).render('READY', True, WHITE, None)
        self.scene["ready_player2"].geometry = pygame.font.SysFont('arial', 32).render('READY', True, WHITE, None)

        self.scene["selector_player1"].geometry = pygame.image.load("assets/hand_right.png")
        self.scene["selector_player2"].geometry = pygame.image.load("assets/hand_left.png")

        self.scene["title"].transform = Transform2D(
            map(
                np.array((0.5, 0.15)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["title"].geometry.get_size()[0] / 2.5, 0),
            (0, self.scene["title"].geometry.get_size()[1] / 2.5)
        )

        self.scene["subtitle"].transform = Transform2D(
            map(
                np.array((0.5, 0.3)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["subtitle"].geometry.get_size()[0], 0),
            (0, self.scene["subtitle"].geometry.get_size()[1])
        )

        self.scene["credits"].transform = Transform2D(
            map(
                np.array((0.35, 0.95)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["credits"].geometry.get_size()[0], 0),
            (0, self.scene["credits"].geometry.get_size()[1])
        )

        self.scene["ready_player1"].transform = Transform2D(
            map(
                np.array((0.15, 0.4)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["ready_player1"].geometry.get_size()[0], 0),
            (0, self.scene["ready_player1"].geometry.get_size()[1])
        )

        self.scene["ready_player2"].transform = Transform2D(
            map(
                np.array((0.85, 0.4)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["ready_player2"].geometry.get_size()[0], 0),
            (0, self.scene["ready_player2"].geometry.get_size()[1])
        )

        self.scene["selector_player1"].transform = Transform2D(
            map(
                np.array((0.25, 0.6)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["selector_player1"].geometry.get_size()[0] / 2, 0),
            (0, self.scene["selector_player1"].geometry.get_size()[1] / 2)
        )

        self.scene["selector_player2"].transform = Transform2D(
            map(
                np.array((0.75, 0.6)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["selector_player2"].geometry.get_size()[0] / 2, 0),
            (0, self.scene["selector_player2"].geometry.get_size()[1] / 2)
        )

        pygame.mixer.music.load("assets/menusong.wav")
        pygame.mixer.music.play(-1)

        return "menu"

    def menu_agent(self):
        for name, player in self.players.items():
            bounded = 100 > np.linalg.norm(
                player["target"] - self.scene["selector_" + name].transform.position()
            )

            player["ready"] = player["tracking"] and bounded
            self.scene["ready_" + name].visible = player["ready"]

        if self.players["player1"]["ready"]:
            self.scene["selector_player1"].geometry = pygame.image.load("assets/hand_right_filled.png")
        else:
            self.scene["selector_player1"].geometry = pygame.image.load("assets/hand_right.png")

        if self.players["player2"]["ready"]:
            self.scene["selector_player2"].geometry = pygame.image.load("assets/hand_left_filled.png")
        else:
            self.scene["selector_player2"].geometry = pygame.image.load("assets/hand_left.png")
            
        if (self.players["player1"]["ready"] and self.players["player2"]["ready"]):
            pygame.mixer.music.stop()
            return "ready"
        
        return self.state

    def round_load(self):
        self.scene = {
            "countdown" : GameObject(collisions=False, transparency=0.1),

            "timer" : GameObject(collisions=False, transparency=0.1, visible=False),
            "points_player1" : GameObject(collisions=False, transparency=0.1, visible=False),
            "points_player2" : GameObject(collisions=False, transparency=0.1, visible=False),
            "divider" : GameObject(collisions=False, transparency=0.2, visible=False),

            "slider_player1" : GameObject(),
            "slider_player2" : GameObject(),
            "ball" : GameObject(visible=False),
            
            "wall_left" : GameObject(visible=True),
            "wall_right" : GameObject(visible=True),
            "wall_top" : GameObject(visible=True),
            "wall_bottom" : GameObject(visible=True),

            "collision" : GameObject(visible=True, collisions=False, transparency=0.8)
        }

        self.countdown_time = COUNTDOWN_DURATION
        self.game_time = GAME_DURATION

        self.scene["countdown"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(self.game_time), True, WHITE, None
        )
        self.scene["countdown"].transform = Transform2D(
            map(
                np.array((0.5, 0.5)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["countdown"].geometry.get_size()[0], 0),
            (0, self.scene["countdown"].geometry.get_size()[1])
        )

        self.scene["timer"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(self.game_time), True, WHITE, None
        )
        self.scene["timer"].transform = Transform2D(
            map(
                np.array((0.5, 0.08)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["timer"].geometry.get_size()[0], 0),
            (0, self.scene["timer"].geometry.get_size()[1])
        )

        self.scene["points_player1"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(self.players["player1"]["points"]), True, WHITE, None
        )
        self.scene["points_player1"].transform = Transform2D(
            map(
                np.array((0.4, 0.2)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["points_player1"].geometry.get_size()[0], 0),
            (0, self.scene["points_player1"].geometry.get_size()[1])
        )

        self.scene["points_player2"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(self.players["player2"]["points"]), True, WHITE, None
        )
        self.scene["points_player2"].transform = Transform2D(
            map(
                np.array((0.6, 0.2)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["points_player2"].geometry.get_size()[0], 0),
            (0, self.scene["points_player2"].geometry.get_size()[1])
        )

        self.scene["slider_player1"].geometry = pygame.image.load("assets/slider.png")
        self.scene["slider_player1"].transform = Transform2D(
            (self.window["size"].x * 0.1, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )
        
        self.scene["slider_player2"].geometry = pygame.image.load("assets/slider.png")
        self.scene["slider_player2"].transform = Transform2D(
            (self.window["size"].x * 0.9, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )

        self.scene["divider"].geometry = pygame.image.load("assets/divider.png")
        self.scene["divider"].transform = Transform2D(
            map(
                np.array((0.5, 0.55)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (10, 0),
            (0, self.window["size"].y * 0.9)
        )

        self.scene["wall_left"].geometry = pygame.image.load("assets/block.png")
        self.scene["wall_left"].transform = Transform2D(
            map(
                np.array((0, 0.5)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (10, 0),
            (0, self.window["size"].y)
        )

        self.scene["wall_right"].geometry = pygame.image.load("assets/block.png")
        self.scene["wall_right"].transform = Transform2D(
            map(
                np.array((1, 0.5)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (10, 0),
            (0, self.window["size"].y)
        )

        self.scene["wall_top"].geometry = pygame.image.load("assets/block.png")
        self.scene["wall_top"].transform = Transform2D(
            map(
                np.array((0.5, 0)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.window["size"].x, 0),
            (0, 10)
        )

        self.scene["wall_bottom"].geometry = pygame.image.load("assets/block.png")
        self.scene["wall_bottom"].transform = Transform2D(
            map(
                np.array((0.5, 1)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.window["size"].x, 0),
            (0, 10)
        )

        self.scene["collision"].geometry = pygame.image.load("assets/target.png")
        self.scene["collision"].transform = Transform2D(
            (0, 0),
            (100, 0),
            (0, 100)
        )

        self.scene["ball"].geometry = pygame.image.load("assets/ball.png")
        self.scene["ball"].transform = Transform2D(
            (0.5 * np.array(self.window["size"])), 
            (50, 0), 
            (0, 50)
        )

        direction = np.array((rand(-1, 1), rand(-.2, .2)))
        self.scene["ball"].velocity = BALL_MIN_VELOCITY * direction / np.linalg.norm(direction) 

        pygame.mixer.music.load("assets/main.wav")
        pygame.mixer.music.play(-1)

        return "countdown"

    def round_countdown(self, delta):
        self.countdown_time -= delta

        if (self.countdown_time > 1):
            self.scene["countdown"].geometry = pygame.font.SysFont('arial', 70).render(
                '{}'.format(int(self.countdown_time)), True, WHITE, None
            )
            self.scene["countdown"].transform = Transform2D(
                self.scene["countdown"].transform.position(),
                (self.scene["countdown"].geometry.get_size()[0], 0),
                (0, self.scene["countdown"].geometry.get_size()[1])
            )
            return "countdown"

        elif (self.countdown_time > 0):
            self.scene["countdown"].geometry = pygame.font.SysFont('arial', 70).render(
                'START!', True, WHITE, None
            )
            self.scene["countdown"].transform = Transform2D(
                self.scene["countdown"].transform.position(),
                (self.scene["countdown"].geometry.get_size()[0], 0),
                (0, self.scene["countdown"].geometry.get_size()[1])
            )
            return "countdown"
        else:
            self.scene["countdown"].visible = False
            self.scene["ball"].visible = True
            self.scene["timer"].visible = True
            self.scene["divider"].visible = True
            self.scene["points_player1"].visible = True
            self.scene["points_player2"].visible = True

        return "playing"

    def round_agent(self, delta):
        self.game_time -= delta

        self.scene["timer"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(int(self.game_time)), True, WHITE, None
        )
        self.scene["timer"].transform = Transform2D(
            self.scene["timer"].transform.position(),
            (self.scene["timer"].geometry.get_size()[0], 0),
            (0, self.scene["timer"].geometry.get_size()[1])
        )

        self.scene["points_player1"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(int(self.players["player1"]["points"])), True, WHITE, None
        )
        self.scene["points_player1"].transform = Transform2D(
            self.scene["points_player1"].transform.position(),
            (self.scene["points_player1"].geometry.get_size()[0], 0),
            (0, self.scene["points_player1"].geometry.get_size()[1])
        )

        self.scene["points_player2"].geometry = pygame.font.SysFont('arial', 70).render(
            '{}'.format(int(self.players["player2"]["points"])), True, WHITE, None
        )
        self.scene["points_player2"].transform = Transform2D(
            self.scene["points_player2"].transform.position(),
            (self.scene["points_player2"].geometry.get_size()[0], 0),
            (0, self.scene["points_player2"].geometry.get_size()[1])
        )
        
        # For each player, update state
        for name, player in self.players.items():
            slider = self.scene["slider_" + name]

            # Interpolate slider towards target
            slider.transform.components[2][1] = lerp(
                slider.transform.components[2][1], 
                player["target"].y, 
                0.3
            )

        ball = self.scene["ball"]
        radius = np.linalg.norm(ball.transform.size() / 2)

        velocity_scalar = np.linalg.norm(ball.velocity)
        velocity_unit = ball.velocity / velocity_scalar

        ray_origin = ball.transform.position()
        ray_direction = velocity_unit
        normal = np.array((0, 0))
        near, far = radius, radius

        collided_object = None

        for name, object in self.scene.items():
            if object.collisions == False:
                continue
            if object == ball:
                continue

            t0, t1 = raycastBox(
                ray_origin, 
                ray_direction, 
                object.transform.position() - object.transform.size() / 2, 
                object.transform.position() + object.transform.size() / 2
            )

            if ((-radius <= t0) and (t0 <= near) and (t0 <= t1)):
                collided_object = object
                near = t0
                far = t1

        if (near < far):
            # calculate normal
            hit = ray_origin + near * ray_direction
            relative = np.append((hit - collided_object.transform.position()), 0)

            sx, sy = collided_object.transform.size()
            x = 2 * relative[0] / sx
            y = 2 * relative[1] / sy

            if (x >= y) and (x >= -y):
                normal = np.array((1, 0))
            if (x <= y) and (x <= -y):
                normal = np.array((-1, 0))
            elif (x >= y) and (x <= -y):
                normal = np.array((0, 1))
            elif (x <= y) and (x >= -y):
                normal = np.array((0, -1))
            
            self.scene["collision"].transform = Transform2D(hit, (100, 0), (0, 100))

            jitter = np.array((rand(-1, 1), rand(-.5, .5)))
            jitter = jitter / np.linalg.norm(jitter)

            velocity_unit -= 2 * velocity_unit.dot(normal) * normal + jitter / 6

        if (collided_object == self.scene["slider_player1"]) or (collided_object == self.scene["slider_player2"]):
            velocity_scalar *= 1.5

        elif (collided_object == self.scene["wall_left"]):
            print("point for player2!")
            self.players["player2"]["points"] += 1
            velocity_scalar /= 1.5
            
        elif (collided_object == self.scene["wall_right"]):
            print("point for player1!")
            self.players["player1"]["points"] += 1
            velocity_scalar /= 1.5
            
        ball.velocity = np.clip(
            velocity_scalar,
            BALL_MIN_VELOCITY, 
            BALL_MAX_VELOCITY
        ) * velocity_unit
        
        ball.transform = Transform2D(
            np.clip(ball.transform.position() + ball.velocity * delta, (1, 1), self.window["size"] - (1, 1)),
            (50, 0),
            (0, 50)
        )

        if ((self.game_time <= 0) or 
            (self.players["player1"]["points"] >= PLAYER_MAX_POINTS) or
            (self.players["player2"]["points"] >= PLAYER_MAX_POINTS)) and self.round < NUMBER_OF_ROUNDS:
        
            self.round += 1
            print(self.round)
            return "ready"

        if (self.round >= NUMBER_OF_ROUNDS):
            return "finished"

        return "playing"

    def run(self):
        self.running = True
        delta = 0

        while self.running:
            delta = time.monotonic() - self.tick
            self.tick = self.tick + delta
           
            self.event()
            
            if (self.state == "reset"):
                self.state = self.menu_load()
            elif (self.state == "menu"):
                self.state = self.menu_agent()
            elif (self.state == "ready"):
                self.state = self.round_load()
            elif (self.state == "countdown"):
                self.state = self.round_countdown(delta)
            elif (self.state == "playing"):
                self.state = self.round_agent(delta)
            elif (self.state == "finished"):
                print("player1", self.players["player1"]["points"])
                print("player2", self.players["player2"]["points"])

                pass

            self.render()

        pygame.quit()

    def event(self):
        _, self.camera["frame"] = self.camera["instance"].read()

        # Assist CV somehow, implement luminosity correction later
        correction = CAMERA_CORRECTION
        result = np.uint8(np.double(self.camera["frame"]) + correction)

        results = self.camera["detector"].process(result)

        self.players["player1"]["tracking"] = False
        self.players["player2"]["tracking"] = False

        # Ensure that at least one hand is detected
        if (results.multi_hand_landmarks != None):
            for controller in results.multi_hand_landmarks:
                target = Vector2(
                    (1 - controller.landmark[8].x) * self.window["size"].x,
                    controller.landmark[8].y * self.window["size"].y
                )

                player = ""
                if (target.x < 0.5 * self.window["size"].x):
                    player = "player1"
                else:
                    player = "player2"

                self.players[player]["tracking"] = True

                self.players[player]["target"] = lerp(
                    self.players[player]["target"],
                    target,
                    0.4
                )

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def render(self):
        screen = self.window["instance"]

        surface = pygame.surfarray.make_surface(
            np.rot90(cv2.cvtColor(self.camera["frame"], cv2.COLOR_BGR2RGB))
        )
        surface.set_alpha(25)

        screen.fill((22, 33, 44))
        screen.blit(surface, (0, 0))

        # For every object in the scene, render one by one
        for object in self.scene.values():
            if object.visible:
                position = object.transform.position()
                size = object.transform.size()
                angle = np.arctan2(
                    object.transform.right()[1], 
                    object.transform.right()[0]
                )
                
                render = pygame.transform.scale(object.geometry, size)
                render = pygame.transform.rotate(render, angle)
                render.set_alpha(255 * (1 - object.transparency))

                screen.blit(render, position - 0.5 * np.array((render.get_width(), render.get_height())))

        for i in range(1, 3):
            player = self.players["player" + str(i)]

            # Visual aid for controller position
            if player["tracking"]:
                pointer = pygame.image.load("assets/target.png")
                pointer = pygame.transform.smoothscale(pointer, (100, 100))
                pointer.set_alpha(30)
                screen.blit(pointer, player["target"] - 0.5 * Vector2(pointer.get_width(), pointer.get_height()))
        
        # Maybe don't accidentally delete this
        pygame.display.update()

game = GameContainerClass()
game.run()