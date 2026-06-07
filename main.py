import numpy as np
import sys
import pygame
import time
import math
import utils
import random

import absoluteSolver
#import cpuSolver

#presetSelection = int(input("Пресет: "))
presetSelection = 0
def loadPreset(camera, ID = 5):
    if ID == 0:
        return
    if ID == 1:
        camera['positionX'] = -8
        camera['positionY'] = 4
        camera['positionZ'] = -16.5
        camera['directionX'] = 0.55
        camera['directionY'] = -0.25
        camera['directionZ'] = 0.75
        camera['upX'] = 0.15
        camera['upY'] = 0.95
        camera['upZ'] = 0.2
    if ID == 2:
        camera['positionX'] = 2.65
        camera['positionY'] = -0.75
        camera['positionZ'] = -15.5
        camera['directionX'] = 0
        camera['directionY'] = 0
        camera['directionZ'] = 1
        camera['upX'] = 0
        camera['upY'] = 1
        camera['upZ'] = 0
    if ID == 3:
        camera['positionX'] = -21.5
        camera['positionY'] = -1.5
        camera['positionZ'] = 1
        camera['directionX'] = 1
        camera['directionY'] = 0
        camera['directionZ'] = 0
        camera['upX'] = 0
        camera['upY'] = 1
        camera['upZ'] = 0
    if ID == 4:
        camera['positionX'] = 2
        camera['positionY'] = 20
        camera['positionZ'] = -2
        camera['directionX'] = 0
        camera['directionY'] = -1
        camera['directionZ'] = 0
        camera['upX'] = 0
        camera['upY'] = 0
        camera['upZ'] = 1
    if ID == 5:
        camera['positionX'] = 20
        camera['positionY'] = 20
        camera['positionZ'] = -19
        camera['directionX'] = -0.5
        camera['directionY'] = -0.65
        camera['directionZ'] = 0.55
        camera['upX'] = -0.4
        camera['upY'] = 0.75
        camera['upZ'] = 0.5

################################################################
FPS = 120
frame_time = 1.0 / FPS
tMultiplicator = 1
particlesCount = 1000
################################################################
pygame.init()
info = pygame.display.Info()
#screenW = info.current_w
#screenH = info.current_h
screenW = 1920
screenH = 1080
font = pygame.font.Font(None, 28)
textColor = (255, 255, 255)
# Создаем массив для рендеринга с темным фоном
screenArray = np.zeros((screenH, screenW, 3), dtype=np.uint8)
screenArray.fill(30)
################################################################
cameraType = np.dtype([
        ('positionX', np.float64),
        ('positionY', np.float64),
        ('positionZ', np.float64),
        ('directionX', np.float64),
        ('directionY', np.float64),
        ('directionZ', np.float64),
        ('upX', np.float64),
        ('upY', np.float64),
        ('upZ', np.float64),
        ('rightX', np.float64),
        ('rightY', np.float64),
        ('rightZ', np.float64),
        ('screenDistance', np.float64),
        ('screenWidthPx', np.int64),
        ('screenHeightPx', np.int64),
        ('fovHorizontal', np.float64)
    ], align=True)
cameraParams = np.zeros(1, dtype=cameraType)
cameraParams['positionX'] = 0
cameraParams['positionY'] = 0
cameraParams['positionZ'] = -7
cameraParams['directionX'] = 0
cameraParams['directionY'] = 0
cameraParams['directionZ'] = 1
cameraParams['upX'] = 0
cameraParams['upY'] = 1
cameraParams['upZ'] = 0
cameraParams['screenDistance'] = 1.0
cameraParams['screenWidthPx'] = screenW
cameraParams['screenHeightPx'] = screenH
cameraParams['fovHorizontal'] = np.pi/2
loadPreset(cameraParams, presetSelection)
camera_speed = 1
mouse_sensitivity = 0.002

################################################################
axes = [
    (np.array([0.0, 0.0, 0.0]), np.array([5.0, 0.0, 0.0]), (255, 0, 0)),   # X ось (красная)
    (np.array([0.0, 0.0, 0.0]), np.array([0.0, 5.0, 0.0]), (0, 255, 0)),   # Y ось (зеленая)
    (np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 5.0]), (0, 0, 255)),   # Z ось (синяя)
]
axePoints = [
    {"text": "X", "pos": [1, 0, 0], "color": (255, 0, 0)},
    {"text": "Y", "pos": [0, 1, 0], "color": (0, 255, 0)},
    {"text": "Z", "pos": [0, 0, 1], "color": (0, 0, 255)}
]
################################################################
particleType = np.dtype([
        ('x', np.float64),
        ('y', np.float64),
        ('z', np.float64),
        ('lifetime', np.float64),
        ('colors', np.uint64),
        ('lastTicked', np.float64),
        ('spawnedTime', np.float64),
        ('squaredDistanceToCamera', np.float64),
        ('screenX', np.int32),
        ('screenY', np.int32),

        ('_padding', np.int64)
    ], align=True)
particles = np.zeros(particlesCount, dtype=particleType)
for i in range(particlesCount):
    particles[i]['x'] = 0
    particles[i]['y'] = 0
    particles[i]['z'] = 0
    particles[i]['lifetime'] = random.uniform(5,15)
    particles[i]['colors'] = 0xFF0000002222FF00
    particles[i]['lastTicked'] = time.perf_counter()
    particles[i]['spawnedTime'] = 0
    particles[i]['squaredDistanceToCamera'] = 0.0
    particles[i]['screenX'] = 1
    particles[i]['screenY'] = 1

colors = np.zeros(particlesCount, dtype=np.uint32)
################################################################
emitterType = np.dtype([
        ('ID', np.int32),
        ('_padding', np.int32),
        ('X1', np.float64),
        ('Y1', np.float64),
        ('Z1', np.float64),
        ('X2', np.float64),
        ('Y2', np.float64),
        ('Z2', np.float64),
        ('X3', np.float64),
        ('Y3', np.float64),
        ('Z3', np.float64)
    ], align=True)
emittersCount = 1
emitters = np.zeros(emittersCount, dtype=emitterType)
### Emitter 1: CUBE -10 -10 -10 10 10 10
emitters[0]["ID"] = 4

emitters[0]["X1"] = -1
emitters[0]["Y1"] = 0
emitters[0]["Z1"] = -1
emitters[0]["X2"] = 1
emitters[0]["Y2"] = 0
emitters[0]["Z2"] = 1
################################################################
solver = absoluteSolver.CUDASolver()
blockParticles = (16, 1, 1)
gridParticles = (math.ceil(particlesCount / 16), 1, 1)
blockScreen = (16, 16, 1)
gridScreen = (math.ceil(screenW / 16), math.ceil(screenH / 16), 1)

shiftSystemFunction = solver.getFunction("shiftSystem")
projectPointsFunction = solver.getFunction("projectPoints")
tickEmitterSystemFunction = solver.getFunction("tickEmitterSystem")
interpolateColorsFunction = solver.getFunction("interpolateColors")

particlesPtr = solver.allocMemory(particles.nbytes, "particles")
cameraPtr = solver.allocMemory(cameraParams.nbytes, "camera")
screenPtr = solver.allocMemory(screenArray.nbytes, "screen")
emittersPtr = solver.allocMemory(emitters.nbytes, "emitters")
colorsPtr = solver.allocMemory(colors.nbytes, "colors")

solver.copyToMemory(emitters, "emitters")

#shiftSystemFunction(t,currentTime,deltaTime,cameraPtr,particlesPtr, np.int32(particlesCount), block=blockParticles,grid=gridParticles)
################################################################
def getStateT(b):
    if b:
        return "В движении"
    return "Остановлен"
def getMultT(b):
    if b:
        return "+"
    return "-"
def getCoordinatesTextCamera(cameraParams):
    cp = cameraParams[0] # Обращаемся к первому элементу массива параметров
    return f"{cp['positionX']:.3f} {cp['positionY']:.3f} {cp['positionZ']:.3f}"

def getAngleTextCamera(cameraParams):
    cp = cameraParams[0]
    return f"{cp['directionX']:.3f} {cp['directionY']:.3f} {cp['directionZ']:.3f}"

def getUpTextCamera(cameraParams):
    cp = cameraParams[0]
    return f"{cp['upX']:.3f} {cp['upY']:.3f} {cp['upZ']:.3f}"
################################################################

screen = pygame.display.set_mode((screenW, screenH), pygame.FULLSCREEN)
pygame.display.set_caption("Диффуры. Фазовый портрет")
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)  # Захватываем мышь

running = True
elapsed = 0
array_surface = pygame.Surface((screenW, screenH))

t = 0
isPlusT = True
isMovingT = False
lastUpdatedT = time.perf_counter()
lastTicked = time.perf_counter()

# Центрируем мышь
center_x, center_y = screenW // 2, screenH // 2
pygame.mouse.set_pos(center_x, center_y)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_KP_ENTER:
                isMovingT = True
                lastUpdatedT = time.perf_counter()
            if event.key == pygame.K_KP_PERIOD:
                isMovingT = False
            if event.key == pygame.K_KP_PLUS:
                isPlusT = True
            if event.key == pygame.K_KP_MINUS:
                isPlusT = False

    # START TICK
    start_time = time.perf_counter()

    pos = np.array([
        float(cameraParams['positionX'].item()),
        float(cameraParams['positionY'].item()),
        float(cameraParams['positionZ'].item())
    ])
    dir_vec = np.array([
        float(cameraParams['directionX'].item()),
        float(cameraParams['directionY'].item()),
        float(cameraParams['directionZ'].item())
    ])
    up_vec = np.array([
        float(cameraParams['upX'].item()),
        float(cameraParams['upY'].item()),
        float(cameraParams['upZ'].item())
    ])
    pos = pos.flatten()
    dir_vec = dir_vec.flatten()
    up_vec = up_vec.flatten()

    # Обработка мыши
    dx, dy = pygame.mouse.get_rel()
    new_dir, new_up = utils.rotateCameraEuler(
        dir_vec,
        up_vec,
        dx, dy,
        mouse_sensitivity
    )
    cameraParams['directionX'],cameraParams['directionY'],cameraParams['directionZ'] = new_dir
    cameraParams['upX'],cameraParams['upY'],cameraParams['upZ'] = new_up

    #обработка с клавиатуры
    # Движение камеры WASD
    keys = pygame.key.get_pressed()
    move_speed = camera_speed
    pos = np.array([
        float(cameraParams['positionX'].item()),
        float(cameraParams['positionY'].item()),
        float(cameraParams['positionZ'].item())
    ])
    dir_vec = np.array([
        float(cameraParams['directionX'].item()),
        float(cameraParams['directionY'].item()),
        float(cameraParams['directionZ'].item())
    ])
    up_vec = np.array([
        float(cameraParams['upX'].item()),
        float(cameraParams['upY'].item()),
        float(cameraParams['upZ'].item())
    ])
    right_vec = np.cross(dir_vec, up_vec)
    right_vec = right_vec / np.linalg.norm(right_vec)
    if keys[pygame.K_w]:
        pos += dir_vec * move_speed * elapsed
    if keys[pygame.K_s]:
        pos -= dir_vec * move_speed * elapsed
    if keys[pygame.K_a]:
        pos += right_vec * move_speed * elapsed
    if keys[pygame.K_d]:
        pos -= right_vec * move_speed * elapsed
    if keys[pygame.K_SPACE]:
        pos += up_vec * move_speed * elapsed
    if keys[pygame.K_LSHIFT]:
        pos -= up_vec * move_speed * elapsed
    cameraParams['positionX'],cameraParams['positionY'],cameraParams['positionZ'] = pos.tolist()
    cameraParams['rightX'], cameraParams['rightY'], cameraParams['rightZ'] = right_vec
    solver.copyToMemory(cameraParams, "camera")
    #print(f"Camera: {cameraParams[0]}")

    #затенение
    screenArray = np.clip(screenArray.astype(np.int16) - 3, 30, 255).astype(np.uint8)

    # Отображаем оси на экране
    for axe in axes:
        r = utils.renderSegmentOnCamera([axe[0],axe[1]], cameraParams)
        if r:
            utils.renderLineFast(screenArray, r[0], r[1], axe[2])
    for p in axePoints:
        utils.renderTextBillboard(screenArray, p["text"], p["pos"], cameraParams, base_scale=5, color=p["color"])
    # Обрабатываем партикльные системы
    currentTime = time.perf_counter()
    deltaTime = currentTime - lastTicked
    #print(currentTime, deltaTime, sep="\n")
    solver.copyToMemory(particles, "particles")
    tickEmitterSystemFunction(np.float64(currentTime), particlesPtr, np.int32(particlesCount), emittersPtr, np.int32(emittersCount), block=blockParticles, grid=gridParticles)
    solver.copyFromMemory(particles, "particles")
    shiftSystemFunction(np.float64(t), np.float64(currentTime), np.float64(deltaTime), cameraPtr, particlesPtr, np.int32(particlesCount), block=blockParticles, grid=gridParticles)
    projectPointsFunction(particlesPtr, np.int32(particlesCount), cameraPtr, block=blockParticles, grid=gridParticles)
    solver.copyFromMemory(particles, "particles")
    #print(f"Sample particle: x={particles[0]['x']:.2f}, y={particles[0]['y']:.2f}, z={particles[0]['z']:.2f}, screen=({particles[0]['screenX']}, {particles[0]['screenY']})")
    #print(f"spawnedTime[0] = {particles[0]['spawnedTime']:.2f}, pos = ({particles[0]['x']:.2f}, {particles[0]['y']:.2f}, {particles[0]['z']:.2f})")

    minDistanceParticle = particles['squaredDistanceToCamera'].min()
    maxDistanceParticle = particles['squaredDistanceToCamera'].max()

    interpolateColorsFunction(np.float64(minDistanceParticle), np.float64(maxDistanceParticle), particlesPtr, np.int32(particlesCount), colorsPtr, block=blockParticles, grid=gridParticles)
    solver.copyFromMemory(colors, "colors")

    TOTAL_ST = 0
    i = particlesCount
    while i > 0:
        i -= 1
        if (particles[i]["screenX"] != -1):
            ST = time.perf_counter()
            utils.draw_particle_fast(screenArray, particles[i]["screenX"], particles[i]["screenY"], ((colors[i] >> 24) & 0xFF, (colors[i] >> 16) & 0xFF, (colors[i] >> 8) & 0xFF))
            TOTAL_ST += time.perf_counter() - ST

    pygame.surfarray.blit_array(array_surface, screenArray.swapaxes(0, 1))
    screen.blit(pygame.transform.scale(array_surface, (screenW, screenH)), (0, 0))
    #print(TOTAL_ST)

    # Выводим информацию
    text_surface = font.render("Затраты на рендер: " + str(int(elapsed * 100000) / 100) + "мс", True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 20))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Параметр t = " + str(int(t * 100) / 100), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 40))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Состояние параметра t: " + getStateT(isMovingT), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 60))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Движение параметра t: " + getMultT(isPlusT), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 80))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Координаты камеры: " + getCoordinatesTextCamera(cameraParams), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 110))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Вектор взгляда камеры: " + getAngleTextCamera(cameraParams), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 130))
    screen.blit(text_surface, text_rect)

    text_surface = font.render("Верх камеры: " + getUpTextCamera(cameraParams), True, textColor)
    text_rect = text_surface.get_rect(midleft=(20, 150))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()

    # END TICK
    lastTicked = time.perf_counter()
    elapsed = time.perf_counter() - start_time

    if (isMovingT):
        if (isPlusT):
            t -= (lastUpdatedT - time.perf_counter()) * tMultiplicator
        else:
            t += (lastUpdatedT - time.perf_counter()) * tMultiplicator
        lastUpdatedT = time.perf_counter()

    # Центрируем мышь (чтобы она не уходила за пределы экрана)
    pygame.mouse.set_pos(center_x, center_y)

    if elapsed < frame_time:
        time.sleep(frame_time - elapsed)

pygame.quit()
solver.freeAllMemory()
