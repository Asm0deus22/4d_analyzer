import math
import random

class Particle:
    def __init__(self, x, y, z, color, lifeTime, spawnedTime, movementFunction):
        self.color = color
        self.x = x
        self.y = y
        self.z = z
        self.lifeTime = lifeTime
        self.spawnedTime = spawnedTime
        self.lastTicked = spawnedTime
        self.movementFunction = movementFunction
    def tick(self, currentTime, t):
        deltaTime = (currentTime - self.lastTicked)
        ####################### ЗАДАВАНИЕ СИСТЕМЫ
        offsetXYZ = self.movementFunction(self.x,self.y,self.z,t)
        self.x += offsetXYZ * deltaTime
        self.y += offsetXYZ * deltaTime
        self.z += offsetXYZ * deltaTime
        ####################### ЗАДАВАНИЕ СИСТЕМЫ
        self.lastTicked = currentTime
        if (currentTime - self.spawnedTime > self.lifeTime):
            return False
        return True
class FactoryParticle:
    def __init__(self, color = (0, 140, 240), lifeTime = 3):
        self.color = color
        self.lifeTime = lifeTime
    def createParticle(self, x, y, z, currentTime):
        return Particle(x,y,z,self.color, self.lifeTime, currentTime)

class DistanceParticle(Particle):
    def __init__(self, x, y, z, color1, color2, lifeTime, spawnedTime, movementFunction):
        super().__init__(x, y, z, color1, lifeTime, spawnedTime, movementFunction)
        self.color1 = color1  # Ближний цвет
        self.color2 = color2  # Дальний цвет
        
    def getColor(self, t):
        if not (0 <= t <= 1):
            t = max(0.0, min(1.0, t))
        
        # Линейная интерполяция между двумя цветами
        r = int(self.color1[0] * (1 - t) + self.color2[0] * t)
        g = int(self.color1[1] * (1 - t) + self.color2[1] * t)
        b = int(self.color1[2] * (1 - t) + self.color2[2] * t)
        
        return (r, g, b)
class FactoryDistanceParticle:
    def __init__(self, color1=(0, 140, 240), color2=(240, 140, 0), lifeTime=3):
        self.color1 = color1
        self.color2 = color2
        self.lifeTime = lifeTime
        
    def createParticle(self, x, y, z, currentTime):
        return DistanceParticle(x, y, z, self.color1, self.color2, 
                               self.lifeTime, currentTime)

class EmitterDot:
    def __init__(self, x, y, z, factoryParticle, conditionSpawn):
        self.x = x
        self.y = y
        self.z = z
        self.pF = factoryParticle
        self.sC = conditionSpawn
        self.lastSpawned = 0
    def tick(self, currentTime):
        r = self.sC(currentTime - self.lastSpawned)
        if r:
            self.lastSpawned = currentTime
            return self.pF.createParticle(self.x,self.y,self.z, currentTime)
        return False
class EmitterLine:
    def __init__(self, point1, point2, factoryParticle, conditionSpawn):
        self.point1 = point1
        self.point2 = point2
        self.pF = factoryParticle
        self.sC = conditionSpawn
        self.lastSpawned = 0
        
    def tick(self, currentTime):
        r = self.sC(currentTime - self.lastSpawned)
        if r:
            self.lastSpawned = currentTime
            
            t = random.random()
            x = self.point1[0] + t * (self.point2[0] - self.point1[0])
            y = self.point1[1] + t * (self.point2[1] - self.point1[1])
            z = self.point1[2] + t * (self.point2[2] - self.point1[2])
            
            return self.pF.createParticle(x, y, z, currentTime)
        return False
class EmitterTriangle:
    def __init__(self, point1, point2, point3, factoryParticle, conditionSpawn):
        self.points = [point1, point2, point3]
        self.pF = factoryParticle
        self.sC = conditionSpawn
        self.lastSpawned = 0
        
    def tick(self, currentTime):
        r = self.sC(currentTime - self.lastSpawned)
        if r:
            self.lastSpawned = currentTime
            
            x, y, z = self.get_random_point_in_triangle()
            
            return self.pF.createParticle(x, y, z, currentTime)
        return False
    
    def get_random_point_in_triangle(self):
        r1 = random.random()
        r2 = random.random()
        
        if r1 + r2 > 1:
            r1 = 1 - r1
            r2 = 1 - r2
        
        r3 = 1 - r1 - r2
        
        x = (r1 * self.points[0][0] + r2 * self.points[1][0] + r3 * self.points[2][0])
        y = (r1 * self.points[0][1] + r2 * self.points[1][1] + r3 * self.points[2][1])
        z = (r1 * self.points[0][2] + r2 * self.points[1][2] + r3 * self.points[2][2])
        
        return x, y, z
class EmitterCube:
    def __init__(self, point1, point2, factoryParticle, conditionSpawn):
        self.min_point = [
            min(point1[0], point2[0]),
            min(point1[1], point2[1]),
            min(point1[2], point2[2])
        ]
        self.max_point = [
            max(point1[0], point2[0]),
            max(point1[1], point2[1]),
            max(point1[2], point2[2])
        ]
        self.pF = factoryParticle
        self.sC = conditionSpawn
        self.lastSpawned = 0
        
    def tick(self, currentTime):
        r = self.sC(currentTime - self.lastSpawned)
        if r:
            self.lastSpawned = currentTime
            x = random.uniform(self.min_point[0], self.max_point[0])
            y = random.uniform(self.min_point[1], self.max_point[1])
            z = random.uniform(self.min_point[2], self.max_point[2])
            return self.pF.createParticle(x, y, z, currentTime)
        return False
