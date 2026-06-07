import numpy as np
from numba import njit, prange

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

@njit
def xorshift32(state):
    state ^= state << 13
    state ^= state >> 17
    state ^= state << 5
    return state

@njit
def dot(x1, y1, z1, x2, y2, z2):
    return x1*x2 + y1*y2 + z1*z2

@njit
def cross(ax, ay, az, bx, by, bz):
    return ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx

@njit
def length(x, y, z):
    return np.sqrt(x*x + y*y + z*z)

@njit
def normalize(x, y, z):
    l = length(x, y, z)
    if l > 1e-10:
        x /= l
        y /= l
        z /= l
    return x, y, z

@njit
def offset_system(x, y, z, t, delta_time):
    offset_x = y - 0.5 * x
    offset_y = np.sin(x)
    offset_z = np.sin(t)
    x += offset_x * delta_time
    y += offset_y * delta_time
    z += offset_z * delta_time
    return x, y, z

@njit(parallel=True)
def shift_system_kernel(t, current_time, delta_time, camera, particles, num_points):
    cam = camera[0]
    cam_x = cam['positionX']
    cam_y = cam['positionY']
    cam_z = cam['positionZ']
    for idx in prange(num_points):
        p = particles[idx]
        if p['lifetime'] + p['spawnedTime'] > current_time:
            x, y, z = p['x'], p['y'], p['z']
            x, y, z = offset_system(x, y, z, t, delta_time)
            particles[idx]['x'] = x
            particles[idx]['y'] = y
            particles[idx]['z'] = z
            dx = x - cam_x
            dy = y - cam_y
            dz = z - cam_z
            particles[idx]['squaredDistanceToCamera'] = dx*dx + dy*dy + dz*dz

@njit(parallel=True)
def tick_emitter_kernel(current_time, particles, num_points, emitters, emitters_count):
    for idx in prange(num_points):
        p = particles[idx]
        if p['lifetime'] + p['spawnedTime'] <= current_time:
            seed = np.uint32(int(current_time * 1e9)) ^ np.uint32(idx)
            r = xorshift32(seed)
            selecting = r % emitters_count
            em = emitters[selecting]
            if em['ID'] == 1:
                particles[idx]['x'] = em['X1']
                particles[idx]['y'] = em['Y1']
                particles[idx]['z'] = em['Z1']
                particles[idx]['spawnedTime'] = current_time
            elif em['ID'] == 4:
                particles[idx]['x'] = 1.0
                particles[idx]['y'] = 1.0
                particles[idx]['z'] = 0.0
                particles[idx]['spawnedTime'] = current_time

@njit(parallel=True)
def project_points_kernel(particles, num_particles, camera):
    cam = camera[0]
    cam_pos_x = cam['positionX']
    cam_pos_y = cam['positionY']
    cam_pos_z = cam['positionZ']
    cam_dir_x = cam['directionX']
    cam_dir_y = cam['directionY']
    cam_dir_z = cam['directionZ']
    cam_up_x = cam['upX']
    cam_up_y = cam['upY']
    cam_up_z = cam['upZ']
    cam_right_x = cam['rightX']
    cam_right_y = cam['rightY']
    cam_right_z = cam['rightZ']
    screen_dist = cam['screenDistance']
    screen_width_px = cam['screenWidthPx']
    screen_height_px = cam['screenHeightPx']
    fov_horizontal = cam['fovHorizontal']
    epsilon = 1e-6

    dir_len = length(cam_dir_x, cam_dir_y, cam_dir_z)
    if dir_len > 1e-10:
        cam_dir_x /= dir_len
        cam_dir_y /= dir_len
        cam_dir_z /= dir_len

    cam_up_x, cam_up_y, cam_up_z = normalize(cam_up_x, cam_up_y, cam_up_z)

    right_x, right_y, right_z = cross(cam_up_x, cam_up_y, cam_up_z, cam_dir_x, cam_dir_y, cam_dir_z)
    right_len = length(right_x, right_y, right_z)
    if right_len < epsilon:
        if abs(cam_up_x) > epsilon:
            right_x = cam_up_y
            right_y = -cam_up_x
            right_z = 0.0
        else:
            right_x = 0.0
            right_y = cam_up_z
            right_z = -cam_up_y
        right_len = length(right_x, right_y, right_z)

    if right_len > epsilon:
        right_x /= right_len
        right_y /= right_len
        right_z /= right_len
    else:
        right_x, right_y, right_z = cam_right_x, cam_right_y, cam_right_z
        right_x, right_y, right_z = normalize(right_x, right_y, right_z)

    up_x, up_y, up_z = cross(cam_dir_x, cam_dir_y, cam_dir_z, right_x, right_y, right_z)
    up_x, up_y, up_z = normalize(up_x, up_y, up_z)

    for idx in prange(num_particles):
        p = particles[idx]
        vec_x = p['x'] - cam_pos_x
        vec_y = p['y'] - cam_pos_y
        vec_z = p['z'] - cam_pos_z

        dot_dir = dot(vec_x, vec_y, vec_z, cam_dir_x, cam_dir_y, cam_dir_z)

        if dot_dir <= epsilon:
            particles[idx]['screenX'] = -1
            particles[idx]['screenY'] = -1
            continue

        t = screen_dist / dot_dir

        if dot_dir > 1000.0 or not np.isfinite(t):
            particles[idx]['screenX'] = -1
            particles[idx]['screenY'] = -1
            continue

        p_screen_x = cam_pos_x + t * vec_x
        p_screen_y = cam_pos_y + t * vec_y
        p_screen_z = cam_pos_z + t * vec_z

        screen_center_x = cam_pos_x + screen_dist * cam_dir_x
        screen_center_y = cam_pos_y + screen_dist * cam_dir_y
        screen_center_z = cam_pos_z + screen_dist * cam_dir_z

        screen_vec_x = p_screen_x - screen_center_x
        screen_vec_y = p_screen_y - screen_center_y
        screen_vec_z = p_screen_z - screen_center_z

        x_world = dot(screen_vec_x, screen_vec_y, screen_vec_z, right_x, right_y, right_z)
        y_world = dot(screen_vec_x, screen_vec_y, screen_vec_z, up_x, up_y, up_z)

        screen_width_world = 2.0 * screen_dist * np.tan(fov_horizontal / 2.0)
        screen_height_world = screen_width_world * screen_height_px / screen_width_px

        if abs(x_world) > screen_width_world * 10.0 or abs(y_world) > screen_height_world * 10.0:
            particles[idx]['screenX'] = -1
            particles[idx]['screenY'] = -1
            continue

        x_norm = x_world / (screen_width_world / 2.0) if abs(screen_width_world) >= epsilon else 0.0
        y_norm = y_world / (screen_height_world / 2.0) if abs(screen_height_world) >= epsilon else 0.0


        if x_norm < -10.0: x_norm = -10.0
        if x_norm > 10.0: x_norm = 10.0
        if y_norm < -10.0: y_norm = -10.0
        if y_norm > 10.0: y_norm = 10.0

        x_px = (x_norm + 1.0) * (screen_width_px / 2.0)
        y_px = (1.0 - y_norm) * (screen_height_px / 2.0)

        if x_px < 0 or x_px >= screen_width_px or y_px < 0 or y_px >= screen_height_px:
            particles[idx]['screenX'] = -1
            particles[idx]['screenY'] = -1
            continue

        particles[idx]['screenX'] = int(x_px)
        particles[idx]['screenY'] = int(y_px)

@njit(parallel=True)
def interpolate_colors_kernel(min_dist, max_dist, particles, num_points, colors):
    sqrt_min = np.sqrt(min_dist)
    sqrt_max = np.sqrt(max_dist)
    denom = sqrt_max - sqrt_min
    if denom == 0.0:
        for idx in prange(num_points):
            col = particles[idx]['colors']
            one = col >> 32
            r = (one >> 24) & 0xFF
            g = (one >> 16) & 0xFF
            b = (one >> 8) & 0xFF
            a = one & 0xFF
            colors[idx] = (r << 24) | (g << 16) | (b << 8) | a
        return

    for idx in prange(num_points):
        dist_sq = particles[idx]['squaredDistanceToCamera']
        offset = (np.sqrt(dist_sq) - sqrt_min) / denom
        col = particles[idx]['colors']
        one = col >> 32
        two = col & 0xFFFFFFFF
        r = int(((one >> 24) & 0xFF) * (1 - offset) + ((two >> 24) & 0xFF) * offset)
        g = int(((one >> 16) & 0xFF) * (1 - offset) + ((two >> 16) & 0xFF) * offset)
        b = int(((one >> 8) & 0xFF) * (1 - offset) + ((two >> 8) & 0xFF) * offset)
        a = int((one & 0xFF) * (1 - offset) + (two & 0xFF) * offset)
  
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        a = max(0, min(255, a))
        colors[idx] = (r << 24) | (g << 16) | (b << 8) | a

class CPUSolver:
    def __init__(self):
        self.memory = {}

    def allocMemory(self, nbytes, name):
        if name in self.memory:
            raise KeyError(f"Cannot alloc non unique sector {name}")
        self.memory[name] = np.zeros(nbytes, dtype=np.uint8)
        return self.memory[name]

    def copyToMemory(self, npArr, name):
        if name not in self.memory:
            raise KeyError(f"Not found memory sector {name}")
        buf = self.memory[name]
        if buf.size != npArr.nbytes:
            raise ValueError(f"Size mismatch: buffer {buf.size} bytes vs array {npArr.nbytes} bytes")
        buf[:] = npArr.view(np.uint8).ravel()

    def copyFromMemory(self, npArr, name):
        if name not in self.memory:
            raise KeyError(f"Not found memory sector {name}")
        buf = self.memory[name]
        if buf.size != npArr.nbytes:
            raise ValueError(f"Size mismatch: buffer {buf.size} bytes vs array {npArr.nbytes} bytes")
        npArr[:] = buf.view(npArr.dtype).reshape(npArr.shape)

    def freeMemory(self, name):
        if name not in self.memory:
            raise KeyError(f"Not found memory sector {name}")
        del self.memory[name]

    def freeAllMemory(self):
        self.memory.clear()

    def __del__(self):
        self.freeAllMemory()

    def getFunction(self, title):
        if title == "shiftSystem":
            return self._shift_system_wrapper
        elif title == "tickEmitterSystem":
            return self._tick_emitter_wrapper
        elif title == "projectPoints":
            return self._project_points_wrapper
        elif title == "interpolateColors":
            return self._interpolate_colors_wrapper
        else:
            raise ValueError(f"Unknown function {title}")

    def _shift_system_wrapper(self, t, currentTime, deltaTime, camera_bytes, particles_bytes, numPoints, **kwargs):
        camera = camera_bytes.view(cameraType).reshape(1)
        particles = particles_bytes.view(particleType).reshape(numPoints)
        shift_system_kernel(t, currentTime, deltaTime, camera, particles, numPoints)

    def _tick_emitter_wrapper(self, currentTime, particles_bytes, numPoints, emitters_bytes, emittersCount, **kwargs):
        particles = particles_bytes.view(particleType).reshape(numPoints)
        emitters = emitters_bytes.view(emitterType).reshape(emittersCount)
        tick_emitter_kernel(currentTime, particles, numPoints, emitters, emittersCount)

    def _project_points_wrapper(self, particles_bytes, numParticles, camera_bytes, **kwargs):
        particles = particles_bytes.view(particleType).reshape(numParticles)
        camera = camera_bytes.view(cameraType).reshape(1)
        project_points_kernel(particles, numParticles, camera)

    def _interpolate_colors_wrapper(self, minDist, maxDist, particles_bytes, numPoints, colors_bytes, **kwargs):
        particles = particles_bytes.view(particleType).reshape(numPoints)
        colors = colors_bytes.view(np.uint32).reshape(numPoints)
        interpolate_colors_kernel(minDist, maxDist, particles, numPoints, colors)
