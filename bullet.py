import pygame
import math

class Bullet:
    def __init__(self, startx, starty,endx,endy):
        self.x = startx
        self.y = starty
        self.endx=endx
        self.endy=endy
        self.size = 3
        self.speed=2
        self.active=True

        dx = endx - startx
        dy = endy - starty
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1
        self.velocity_x = dx / distance * self.speed
        self.velocity_y = dy / distance * self.speed

    def update(self):
        if abs(self.x - self.endx) > abs(self.velocity_x) or abs(self.y - self.endy) > abs(self.velocity_y):
            self.x += self.velocity_x
            self.y += self.velocity_y
        else:
            self.active = False

    def draw(self, g):
        pygame.draw.circle(g, (0, 0, 0), (int(self.x), int(self.y)), self.size)