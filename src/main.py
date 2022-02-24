import imp
import pygame
import numpy
import cv2
import random
import time
import mediapipe

import tween

from pygame.math import Vector2 as Vector2

mp_drawing = mediapipe.solutions.drawing_utils
mp_drawing_styles = mediapipe.solutions.drawing_styles
mp_hands = mediapipe.solutions.hands

def lerp(a, b, c):
    return a + (b - a) * c

def map(x, a, b, c, d):
    return (x - a) * (d - c) / (b - a) + c

# Create interface sequence system

interface = {
    # Landing screen
    "menu" : {
        "landing_title" : pygame.transform.smoothscale(
            pygame.image.load("img/landing_title.png"),
            0.5 * Vector2(1000, 340)
        )
    }
}

class GameContainerClass:
    # Game hierarchy & states
    window = {
        "instance" : None,
        "size" : Vector2(1280, 720)
    }
    camera = {
        "instance" : None,
        "detector" : None
    }
    components = {
        "player1" : {
            "slider" : None,
            "target" : Vector2(0, 0)
        },
        "player2" : {
            "slider" : None,
            "target" : Vector2(0, 0)
        }
    }
    running = False

    def load(self):
        pygame.init()

        pygame.display.set_caption('Pong!')
        
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


        self.components["player1"]["target"] = 0.5 * self.window["size"]
        self.components["player2"]["target"] = 0.5 * self.window["size"]

        self.components["player1"]["slider"] = pygame.Rect(
            self.window["size"].x * 0.1,
            self.window["size"].y * 0.5,
            25,
            200
        )
        
        self.components["player2"]["slider"] = pygame.Rect(
            self.window["size"].x * 0.9,
            self.window["size"].y * 0.5,
            25,
            200
        )

        
        pygame.display.update()


    def run(self):
        self.running = True
        
        while self.running:
            self.render()

            for instance in tween.instances:
                instance.updatez()

            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
        pygame.quit()
   
    def render(self):
        self.window["instance"].fill((22, 33, 44))
        
        _, frame = self.camera["instance"].read()

        results = self.camera["detector"].process(frame)

        surface = pygame.surfarray.make_surface(
            numpy.rot90(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        )

        surface.set_alpha(25)

        self.window["instance"].blit(surface, (0, 0))

        # Ensure that at least one hand is detected
        if (results.multi_hand_landmarks != None):
            for controller in results.multi_hand_landmarks:
                target = Vector2(
                    (1 - controller.landmark[8].x) * self.window["size"].x,
                    controller.landmark[8].y * self.window["size"].y
                )
                if (target.x < 0.5 * self.window["size"].x):
                    self.components["player1"]["target"] = target
                else:
                    self.components["player2"]["target"] = target

        # For each player, update state
        for i in range(1, 3):
            player = self.components["player" + str(i)]
            # Visual aid for controller position
            pygame.draw.circle(
                self.window["instance"], 
                (42, 53, 64), 
                player["target"], 
                20
            )
            # Interpolate slider towards target
            player["slider"].y = lerp(
                player["slider"].y, 
                player["target"].y, 
                0.3
            )
            # Display player's slider
            pygame.draw.rect(
                self.window["instance"],
                (230, 230, 230), 
                player["slider"]
            )
                    
        pygame.display.update()

game = GameContainerClass()
game.load()
game.run()