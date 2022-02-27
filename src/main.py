import pygame
import numpy as np
import cv2
import random
import time
import mediapipe

import tween

from transform import Transform2D
from pygame.math import Vector2 as Vector2

mp_drawing = mediapipe.solutions.drawing_utils
mp_drawing_styles = mediapipe.solutions.drawing_styles
mp_hands = mediapipe.solutions.hands

def lerp(a, b, c):
    return a + (b - a) * c

def map(x, a, b, c, d):
    return (x - a) * (d - c) / (b - a) + c

# Colour refs
green = (0, 255, 30)
blue = (0, 0, 128)
red = (255, 65, 0)
white = (255, 255, 255)

# vec2 raycastBox(vec3 rayOrigin, vec3 rayDirection, vec3 boundaryMin, vec3 boundaryMax) {
#     vec3 t0 = (boundaryMin - rayOrigin) / rayDirection;
#     vec3 t1 = (boundaryMax - rayOrigin) / rayDirection;
#     vec3 tMin = min(t0, t1);
#     vec3 tMax = max(t0, t1);
    
#     return vec2(
#         max(max(tMin.x, tMin.y), tMin.z), // near
#         min(min(tMax.x, tMax.y), tMax.z)  // far
#     );
# };

def raycastBox(ray_origin, ray_direction, boundary_min, boundary_max):
    t0 = (boundary_min[0:2] - ray_origin[0:2]) / ray_direction[0:2]
    t1 = (boundary_max[0:2] - ray_origin[0:2]) / ray_direction[0:2]

    tMin = np.minimum(t0, t1)
    tMax = np.maximum(t0, t1)
    
    return (
        np.maximum(tMin[0], tMin[1]),
        np.minimum(tMax[0], tMax[1])
    )

class GameObject:
    transform = None
    geometry = None
    velocity = None
    visible = None
    transparency = None

    def __init__(self, visible = True, transparency = 0):
        self.transform = Transform2D()
        self.geometry = pygame.Surface((0, 0))
        self.velocity = Vector2(0, 0)
        self.visible = visible
        self.transparency = transparency

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
            "health" : 100
        },
        "player2" : {
            "target" : Vector2(0, 0),
            "tracking" : False,
            "ready" : False,
            "health" : 100
        }
    }
    scene = {
        "slider_player1" : GameObject(),
        "slider_player2" : GameObject(),
        "ball" : GameObject(),
        "collision" : GameObject()
    }

    tick = time.monotonic()
    
    game_time = 0

    newgame = True
    running = False

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

    def load_menu(self):
        self.scene = {
            "title" : GameObject(),
            "subtitle" : GameObject(),
            "credits" : GameObject(),
            "ready_player1" : GameObject(visible=False),
            "ready_player2" : GameObject(visible=False),
            "selector_player1" : GameObject(transparency=0.3),
            "selector_player2" : GameObject(transparency=0.3),
            "deec_logo" : GameObject(transparency=0.3),
        }

        self.scene["title"].geometry = pygame.font.SysFont('arial', 100).render('Deec x Pong', True, green, blue)
        self.scene["subtitle"].geometry = pygame.font.SysFont('arial', 75).render('50 Anos', True, red, blue)
        self.scene["credits"].geometry = pygame.font.SysFont('arial', 20).render(
            'Developed by: Rui Simão & Tobias Marsh-Hulland (Initial version by João Simões)', True, white, None
        )

        self.scene["ready_player1"].geometry = pygame.font.SysFont('arial', 32).render('READY', True, white, None)
        self.scene["ready_player2"].geometry = pygame.font.SysFont('arial', 32).render('READY', True, white, None)

        self.scene["selector_player1"].geometry = pygame.image.load("img/bluehand.png")
        self.scene["selector_player2"].geometry = pygame.image.load("img/redhand.png")

        self.scene["deec_logo"].geometry = pygame.image.load("img/deec50.png")

        self.scene["title"].transform = Transform2D(
            map(
                np.array((0.5, 0.1)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["title"].geometry.get_size()[0], 0),
            (0, self.scene["title"].geometry.get_size()[1])
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
                np.array((0.2, 0.5)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["ready_player1"].geometry.get_size()[0], 0),
            (0, self.scene["ready_player1"].geometry.get_size()[1])
        )

        self.scene["ready_player2"].transform = Transform2D(
            map(
                np.array((0.8, 0.5)), 
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

        self.scene["deec_logo"].transform = Transform2D(
            map(
                np.array((0.9, 0.1)), 
                np.array((0, 0)), np.array((1, 1)), 
                np.array((0, 0)), np.array(self.window["size"])
            ),
            (self.scene["deec_logo"].geometry.get_size()[0] / 2, 0),
            (0, self.scene["deec_logo"].geometry.get_size()[1] / 2)
        )

    def menu_agent(self):
        for name, player in self.players.items():
            bounded = 100 > np.linalg.norm(
                player["target"] - self.scene["selector_" + name].transform.position()
            )

            player["ready"] = player["tracking"] and bounded
            self.scene["ready_" + name].visible = player["ready"]

        if (self.players["player1"]["ready"] and self.players["player2"]["ready"]):
            print("Fuck\n.")
            self.newgame = False
            self.load_round()

    def load_round(self):
        self.scene = {
            "slider_player1" : GameObject(),
            "slider_player2" : GameObject(),
            "ball" : GameObject(),
            "collision" : GameObject(visible=False)
        }

        self.scene["slider_player1"].geometry = pygame.image.load("img/slider.png")
        self.scene["slider_player1"].transform = Transform2D(
            (self.window["size"].x * 0.1, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )
        
        self.scene["slider_player2"].geometry = pygame.image.load("img/slider.png")
        self.scene["slider_player2"].transform = Transform2D(
            (self.window["size"].x * 0.9, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )

        self.scene["collision"].geometry = pygame.image.load("img/target.png")
        self.scene["collision"].transform = Transform2D(
            (0, 0),
            (300, 0),
            (0, 300)
        )

        self.scene["ball"].geometry = pygame.image.load("img/ball.png")
        self.scene["ball"].transform = Transform2D(
            (0.5 * np.array(self.window["size"])), 
            (50, 0), 
            (0, 50)
        )

        self.scene["ball"].velocity = Vector2(-40, 10)

    def round_agent(self):
        # For each player, update state
        for name, player in self.players.items():
            slider = self.scene["slider_" + name]

            # Interpolate slider towards target
            slider.transform.components[2][1] = lerp(
                slider.transform.components[2][1], 
                player["target"].y, 
                0.3
            )

    def run(self):
        self.running = True
        delta = 0

        while self.running:
            delta = time.monotonic() - self.tick
            self.tick = self.tick + delta
            self.game_time += delta
           
            self.event()

            if self.newgame:
                self.menu_agent()
            else:
                self.round_agent()

            self.render()
            
        pygame.quit()

    def event(self):
        _, self.camera["frame"] = self.camera["instance"].read()

        # Assist CV somehow, implement luminosity correction later
        correction = -10
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
                pointer = pygame.image.load("img/target.png")
                pointer = pygame.transform.smoothscale(pointer, (100, 100))
                pointer.set_alpha(30)
                screen.blit(pointer, player["target"] - 0.5 * Vector2(pointer.get_width(), pointer.get_height()))
        
        # Maybe don't accidentally delete this
        pygame.display.update()

game = GameContainerClass()
game.load_menu()
game.run()