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

def raycastBox(rayOrigin, rayDirection, boundaryMin, boundaryMax):
    t0 = (boundaryMin - rayOrigin) / rayDirection
    t1 = (boundaryMax - rayOrigin) / rayDirection

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

    def __init__(self):
        self.transform = Transform2D()
        self.geometry = pygame.Surface((0, 0))
        self.velocity = Vector2(0, 0)

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
            "gettime" : None,
            "ready" : False
        },
        "player2" : {
            "target" : Vector2(0, 0),
            "tracking" : False,
            "gettime" : None,
            "ready" : False
        }
    }
    scene = {
        "slider1" : GameObject(),
        "slider2" : GameObject(),
        "ball" : GameObject(),
        "collision" : GameObject()
    }

    tick = time.monotonic()
    running = False

    def load(self):
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


        self.scene["slider1"].geometry = pygame.image.load("img/slider.png")
        self.scene["slider1"].transform = Transform2D(
            (self.window["size"].x * 0.1, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )
        
        self.scene["slider2"].geometry = pygame.image.load("img/slider.png")
        self.scene["slider2"].transform = Transform2D(
            (self.window["size"].x * 0.9, self.window["size"].y * 0.5),
            (25, 0),
            (0, 200)
        )

        self.scene["collision"].geometry = pygame.image.load("img/target.png")
        self.scene["collision"].transform = Transform2D(
            (0, 0),
            (30, 0),
            (0, 30)
        )

        self.scene["ball"].geometry = pygame.image.load("img/ball.png")
        self.scene["ball"].transform = Transform2D(
            (0.5 * np.array(self.window["size"])), 
            (50, 0), 
            (0, 50)
        )
        self.scene["ball"].velocity = Vector2(-80, 10)

    timest1 = time.localtime()
    def menu(self):
        self.menu = True

        #Text formatation
        fontsize = 100
        subFontSize = 75
        readyFontSize = 32
        autorFont = 20

        green = (0, 255, 30)
        blue = (0, 0, 128)
        red = (255, 65, 0)
        white = (255, 255, 255)

        fontTitle = pygame.font.SysFont('arial',fontsize)
        Title = fontTitle.render('Deec x Pong', True, green, blue)

        fontSubTitle = pygame.font.SysFont('arial',subFontSize)
        SubTitle = fontSubTitle.render('50 Anos', True, red, blue)

        fontReady = pygame.font.SysFont('arial',readyFontSize)
        readyText = fontReady.render('READY',True, white, None)
        readyText1 = fontReady.render('READY',True, white, None)

        fontAutor = pygame.font.SysFont('arial',autorFont)
        AutorText = fontAutor.render('Developed by: Rui Simão & Tobias Marsh-Hulland (Initial version by João Simões)', True, white, None)

        TitleRect = Title.get_rect()
        SubTitleRect = SubTitle.get_rect()
        ReadyRect = readyText.get_rect()
        ReadyRect1 = readyText1.get_rect()
        AutorRect = AutorText.get_rect()

        TitleRect.x, TitleRect.y = self.window["size"].x * 0.33, self.window["size"].y * 0.15
        SubTitleRect.x, SubTitleRect.y = self.window["size"].x * 0.43, self.window["size"].y * 0.32

        ReadyRect.x, ReadyRect.y = self.window["size"].x * 0.25, self.window["size"].y * 0.4750
        ReadyRect1.x, ReadyRect1.y = self.window["size"].x * 0.65, self.window["size"].y * 0.4750

        AutorRect.x, AutorRect.y = self.window["size"].x * 0.01, self.window["size"].y * 0.97

        #Show hands image
        imgredHand = pygame.image.load('img/redhand.png').convert_alpha()
        imgblueHand = pygame.image.load('img/bluehand.png').convert_alpha()
        rectredhand = imgredHand.get_rect()
        rectbluehand = imgblueHand.get_rect()

        rectredhand.center = (260 // 2, 260 // 2)
        rectbluehand.center = (260 // 2, 260 // 2)

        rectredhand.x, rectredhand.y =  self.window["size"].x * 0.20, self.window["size"].y * 0.50
        rectbluehand.x, rectbluehand.y =  self.window["size"].x * 0.60, self.window["size"].y * 0.50

        imgDeec = pygame.image.load('img/landing_title.png').convert_alpha()
        imgDeec = pygame.transform.scale(imgDeec, (300 * 0.5, 123 * 0.5))
        DeecRect = imgDeec.get_rect()

    
        DeecRect.x, DeecRect.y =  self.window["size"].x * 0.85 , self.window["size"].y * 0.02

        while self.menu:

            self.window["instance"].fill((22, 33, 44))

            self.window["instance"].blit(Title, TitleRect)
            self.window["instance"].blit(SubTitle, SubTitleRect)
            self.window["instance"].blit(AutorText, AutorRect)
            self.window["instance"].blit(imgDeec, DeecRect)

            _, frame = self.camera["instance"].read()

            results = self.camera["detector"].process(frame)

            surface = pygame.surfarray.make_surface(
                np.rot90(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            )

            surface.set_alpha(25)

            self.window["instance"].blit(surface, (0, 0))

            if (results.multi_hand_landmarks != None):
                for controller in results.multi_hand_landmarks:
    
                    target = Vector2(
                        (1 - controller.landmark[8].x) * self.window["size"].x,
                        controller.landmark[8].y * self.window["size"].y
                    )
                    if (target.x < 0.5 * self.window["size"].x):
                        self.players["player1"]["target"] = target
                    else:
                        self.players["player2"]["target"] = target

            # For each player, update state
            for i in range(1, 3):
                # Ensure that hands are detected
                player = self.players["player" + str(i)]

                pygame.draw.circle(
                    self.window["instance"], 
                    (100, 0, 0), 
                    player["target"], 
                    20
                )

            if (results.multi_hand_landmarks != None):
                #print('len land= {}'.format(len(results.multi_hand_landmarks)))
                self.timeend = time.localtime(time.time())
                
                pose_p1 = self.players["player1"]["target"]
                pose_p2 = self.players["player2"]["target"]

                # ready player one
                if self.players["player1"]["gettime"]:
                    if rectredhand.collidepoint(pose_p1):

                        self.players["player1"]["gettime"] = False
                        self.timest = time.localtime(time.time())

                else:
                    if rectredhand.collidepoint(pose_p1):
                    #texto contador com som
                        if self.timeend.tm_sec - self.timest.tm_sec  >= 3:
                            self.players["player1"]["ready"] = True
                        else:
                            print('PLayer1: Ready in {}' .format(self.timeend.tm_sec - self.timest.tm_sec))
                        
                        self.window["instance"].blit(readyText, ReadyRect) 
                            

                    else:
                        self.players["player1"]["gettime"] = True

                #ready player two
                if self.players["player2"]["gettime"]:
                    if rectbluehand.collidepoint(pose_p2):

                        self.players["player2"]["gettime"] = False
                        self.timest1 = time.localtime(time.time())
            
                else:
                    if rectbluehand.collidepoint(pose_p2):
                    #texto contador com som
                        if self.timeend.tm_sec - self.timest1.tm_sec  >= 3:
                            self.players["player2"]["ready"] = True
                        else: 
                            print('PLayer2: Ready in {}' .format(self.timeend.tm_sec - self.timest1.tm_sec))

                        self.window["instance"].blit(readyText1, ReadyRect1)

                    else:
                        self.players["player2"]["gettime"] = True
           
                if self.players["player1"]["ready"] and self.players["player2"]["ready"]:
                    self.menu = False
                    self.multiplayer = True

                if self.players["player1"]["ready"] or self.players["player2"]["ready"]: 
                    if len(results.multi_hand_landmarks) == 1:
                        self.menu = False
                    
            self.window["instance"].blit(imgredHand, rectredhand)
            self.window["instance"].blit(imgblueHand, rectbluehand)
            self.window["instance"].blit(surface, (0, 0))
            pygame.display.update()

    def run(self):
        self.running = True
        delta = 0

        while self.running:
            delta = time.monotonic() - self.tick
            self.tick = self.tick + delta

            # For every object in the scene, do physics magic
            # ball = self.scene["ball"]
            # for object in self.scene.values():
            #     if object == ball or object == self.scene["slider2"]:
            #         continue

            #     # Convert ball position to object space
            #     ortho = Transform2D(
            #         (0, 0),
            #         object.transform.right() / np.linalg.norm(object.transform.right()),
            #         object.transform.up() / np.linalg.norm(object.transform.up())
            #     )

            #     origin_t = ortho.components.dot(ball.transform.components[2] - object.transform.components[2])
            #     origin = np.array((origin_t[0], origin_t[1]))
            #     direction_t = ortho.components.dot(np.array((ball.velocity[0], ball.velocity[1], 0)))
            #     direction = np.array((direction_t[0], direction_t[1]))

            #     boundary_min = object.transform.position() - 0.5 * object.transform.size()
            #     boundary_max = object.transform.position() + 0.5 * object.transform.size()
  
            #     near, far = raycastBox(origin, direction, boundary_min, boundary_max)

            #     if (near < far):
            #         hit = origin_t + near * direction_t
                    
            #         print(hit)
            #         #self.scene["collision"].transform = Transform2D(np.linalg.inv(ortho.components).dot(hit))

            #         #print(np.linalg.inv(ortho.components).dot(hit))

            self.scene["ball"].transform = self.scene["ball"].transform + self.scene["ball"].velocity * delta

            self.event()
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

        # For each player, update state
        for i in range(1, 3):
            player = self.players["player" + str(i)]
            slider = self.scene["slider" + str(i)]

            # Interpolate slider towards target
            slider.transform.components[2][1] = lerp(
                slider.transform.components[2][1], 
                player["target"].y, 
                0.3
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

        for i in range(1, 3):
            player = self.players["player" + str(i)]

            # Visual aid for controller position
            if player["tracking"]:
                pointer = pygame.image.load("img/target.png")
                pointer = pygame.transform.smoothscale(pointer, (100, 100))
                pointer.set_alpha(30)
                screen.blit(pointer, player["target"] - 0.5 * Vector2(pointer.get_width(), pointer.get_height()))

        # For every object in the scene, render one by one
        for object in self.scene.values():
            position = object.transform.position()
            size = object.transform.size()
            angle = np.arctan2(
                object.transform.right()[1], 
                object.transform.right()[0]
            )
            
            render = pygame.transform.scale(object.geometry, size)
            render = pygame.transform.rotate(render, angle)
            screen.blit(render, position - 0.5 * np.array((render.get_width(), render.get_height())))
        
        # Maybe don't accidentally delete this
        pygame.display.update()

game = GameContainerClass()
game.load()
game.menu()
game.run()