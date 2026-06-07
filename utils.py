import numpy as np
import cv2

def renderSegmentOnCamera(segment, cameraParams, epsilon=1e-6):
    # Извлечение данных из структуры numpy
    cam_pos = np.array([cameraParams[0]['positionX'], 
                        cameraParams[0]['positionY'], 
                        cameraParams[0]['positionZ']], dtype=np.float64)
    cam_dir = np.array([cameraParams[0]['directionX'],
                        cameraParams[0]['directionY'],
                        cameraParams[0]['directionZ']], dtype=np.float64)
    cam_up = np.array([cameraParams[0]['upX'],
                       cameraParams[0]['upY'],
                       cameraParams[0]['upZ']], dtype=np.float64)
    screen_dist = cameraParams[0]['screenDistance']
    W_px = int(cameraParams[0]['screenWidthPx'])
    H_px = int(cameraParams[0]['screenHeightPx'])
    fov = cameraParams[0]['fovHorizontal']  # Изменено с fov_horizontal
    
    cam_dir = cam_dir / np.linalg.norm(cam_dir)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    cam_right = np.cross(cam_up, cam_dir)
    if np.linalg.norm(cam_right) < epsilon:
        if abs(cam_up[0]) > epsilon:
            cam_right = np.array([cam_up[1], -cam_up[0], 0])
        else:
            cam_right = np.array([0, cam_up[2], -cam_up[1]])
    cam_right = cam_right / np.linalg.norm(cam_right)
    
    cam_up = np.cross(cam_dir, cam_right)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    screen_center = cam_pos + cam_dir * screen_dist
    
    screen_width_world = 2 * screen_dist * np.tan(fov / 2)
    screen_height_world = screen_width_world * (H_px / W_px)
    
    def project_point_to_screen(point):
        vec = np.array(point) - cam_pos
        
        dot = np.dot(vec, cam_dir)
        if dot <= epsilon:
            return None
        
        if dot > 1000.0:
            return None
        
        t = screen_dist / dot
        
        if not np.isfinite(t):
            return None
        
        p_screen = cam_pos + t * vec
        
        vec_screen = p_screen - screen_center
        
        x_world = np.dot(vec_screen, cam_right)
        y_world = np.dot(vec_screen, cam_up)
        
        if abs(x_world) > screen_width_world * 10 or abs(y_world) > screen_height_world * 10:
            return None
        
        x_norm = x_world / (screen_width_world / 2) if abs(screen_width_world) > epsilon else 0.0
        y_norm = y_world / (screen_height_world / 2) if abs(screen_height_world) > epsilon else 0.0
        
        x_norm = np.clip(x_norm, -10.0, 10.0)
        y_norm = np.clip(y_norm, -10.0, 10.0)
        
        x_px = int((x_norm + 1.0) * (W_px / 2.0))
        y_px = int((1.0 - y_norm) * (H_px / 2.0))
        
        return [x_px, y_px]
    
    p1_px = project_point_to_screen(segment[0])
    p2_px = project_point_to_screen(segment[1])
    
    if p1_px is None and p2_px is None:
        return False
    
    if p1_px is None or p2_px is None:
        return False
    
    def cohen_sutherland_clip(x1, y1, x2, y2):
        INSIDE = 0
        LEFT = 1
        RIGHT = 2
        BOTTOM = 4
        TOP = 8
        
        def compute_code(x, y):
            code = INSIDE
            if x < 0:
                code |= LEFT
            elif x >= W_px:
                code |= RIGHT
            if y < 0:
                code |= BOTTOM
            elif y >= H_px:
                code |= TOP
            return code
        
        x1_f, y1_f = float(x1), float(y1)
        x2_f, y2_f = float(x2), float(y2)
        
        code1 = compute_code(x1_f, y1_f)
        code2 = compute_code(x2_f, y2_f)
        
        max_iter = 20
        iter_count = 0
        
        while iter_count < max_iter:
            iter_count += 1
            
            if code1 == 0 and code2 == 0:
                return [[int(round(x1_f)), int(round(y1_f))], 
                        [int(round(x2_f)), int(round(y2_f))]]
            
            if code1 & code2:
                return None
            
            if code1 != 0:
                code_out = code1
                x, y = x1_f, y1_f
            else:
                code_out = code2
                x, y = x2_f, y2_f
            
            if code_out & BOTTOM:
                if abs(y2_f - y1_f) > 1e-10:
                    x_new = x1_f + (x2_f - x1_f) * (0 - y1_f) / (y2_f - y1_f)
                else:
                    x_new = x1_f
                y_new = 0.0
            elif code_out & TOP:
                if abs(y2_f - y1_f) > 1e-10:
                    x_new = x1_f + (x2_f - x1_f) * (H_px - 1 - y1_f) / (y2_f - y1_f)
                else:
                    x_new = x1_f
                y_new = H_px - 1.0
            elif code_out & RIGHT:
                if abs(x2_f - x1_f) > 1e-10:
                    y_new = y1_f + (y2_f - y1_f) * (W_px - 1 - x1_f) / (x2_f - x1_f)
                else:
                    y_new = y1_f
                x_new = W_px - 1.0
            elif code_out & LEFT:
                if abs(x2_f - x1_f) > 1e-10:
                    y_new = y1_f + (y2_f - y1_f) * (0 - x1_f) / (x2_f - x1_f)
                else:
                    y_new = y1_f
                x_new = 0.0
            
            if code_out == code1:
                x1_f, y1_f = x_new, y_new
                code1 = compute_code(x1_f, y1_f)
            else:
                x2_f, y2_f = x_new, y_new
                code2 = compute_code(x2_f, y2_f)
        
        return None
    
    x1, y1 = p1_px
    x2, y2 = p2_px
    clipped = cohen_sutherland_clip(x1, y1, x2, y2)
    
    if clipped is None:
        return False
    
    return clipped


def renderLineFast(screen, p1, p2, color):
    pt1 = (int(round(p1[0])), int(round(p1[1])))
    pt2 = (int(round(p2[0])), int(round(p2[1])))

    cv2.line(screen, pt1, pt2, color, thickness=1)

def rotateCameraEuler(cam_dir, cam_up, dx, dy, mouse_sensitivity=0.002):
    cam_dir = np.array(cam_dir, dtype=np.float64)
    cam_up = np.array(cam_up, dtype=np.float64)
    
    cam_dir = cam_dir.flatten()
    cam_up = cam_up.flatten()
    
    if cam_dir.shape[0] != 3 or cam_up.shape[0] != 3:
        return [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]
    
    cam_dir = cam_dir / np.linalg.norm(cam_dir)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    x, y, z = cam_dir
    yaw = np.arctan2(x, z)
    pitch = np.arcsin(y)
    
    yaw += dx * mouse_sensitivity
    pitch -= dy * mouse_sensitivity
    
    max_pitch = np.pi/2 - 0.1
    pitch = np.clip(pitch, -max_pitch, max_pitch)
    
    new_cam_dir = np.array([
        np.sin(yaw) * np.cos(pitch),
        np.sin(pitch),
        np.cos(yaw) * np.cos(pitch)
    ], dtype=np.float64).flatten()
    
    global_up = np.array([0.0, 1.0, 0.0], dtype=np.float64).flatten()
    
    # Убеждаемся, что векторы одномерные
    new_cam_dir = new_cam_dir.reshape(3)
    global_up = global_up.reshape(3)
    
    try:
        right = np.cross(global_up, new_cam_dir)
    except ValueError as e:
        return [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]
    
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-10:
        right = np.array([1.0, 0.0, 0.0], dtype=np.float64).flatten()
    else:
        right = right / right_norm
    
    new_cam_up = np.cross(new_cam_dir, right)
    new_cam_up = new_cam_up / np.linalg.norm(new_cam_up)
    
    return new_cam_dir, new_cam_up

def rotateCameraQuaternion(cam_dir, cam_up, dx, dy, mouse_sensitivity=0.002):
    cam_dir = np.array(cam_dir, dtype=np.float64)
    cam_up = np.array(cam_up, dtype=np.float64)
    cam_dir = cam_dir / np.linalg.norm(cam_dir)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    yaw = dx * mouse_sensitivity
    pitch = -dy * mouse_sensitivity
    
    def quaternion_from_axis_angle(axis, angle):
        axis = axis / np.linalg.norm(axis)
        half_angle = angle / 2.0
        w = np.cos(half_angle)
        x, y, z = axis * np.sin(half_angle)
        return np.array([w, x, y, z])
    
    def apply_quaternion_to_vector(q, v):
        w, x, y, z = q
        vx, vy, vz = v
        
        t = 2.0 * np.cross([x, y, z], v)
        result = v + w * t + np.cross([x, y, z], t)
        return result
    
    if abs(yaw) > 1e-10:
        global_up = np.array([0.0, 1.0, 0.0])
        q_yaw = quaternion_from_axis_angle(global_up, yaw)
        cam_dir = apply_quaternion_to_vector(q_yaw, cam_dir)
        cam_up = apply_quaternion_to_vector(q_yaw, cam_up)
    
    if abs(pitch) > 1e-10:
        right = np.cross(cam_dir, cam_up)
        if np.linalg.norm(right) < 1e-10:
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        
        current_pitch_angle = np.arcsin(np.dot(cam_dir, np.array([0.0, 1.0, 0.0])))
        max_pitch = np.pi/2 - 0.1
        
        if abs(current_pitch_angle + pitch) > max_pitch:
            pitch = np.sign(pitch) * max_pitch - current_pitch_angle
        
        q_pitch = quaternion_from_axis_angle(right, pitch)
        cam_dir = apply_quaternion_to_vector(q_pitch, cam_dir)
        
        global_up = np.array([0.0, 1.0, 0.0])
        
        right = np.cross(cam_dir, global_up)
        if np.linalg.norm(right) < 1e-10:
            right = np.array([0.0, 0.0, 1.0])
        else:
            right = right / np.linalg.norm(right)
        
        cam_up = np.cross(right, cam_dir)
        cam_up = cam_up / np.linalg.norm(cam_up)
        
        cam_dir = cam_dir / np.linalg.norm(cam_dir)
    
    return cam_dir, cam_up

def draw_particle_fast(screen, x, y, color, radius=1):
    H, W = screen.shape[:2]
    
    x0 = max(0, x - radius)
    x1 = min(W - 1, x + radius)
    y0 = max(0, y - radius)
    y1 = min(H - 1, y + radius)
    
    screen[y0:y1+1, x0:x1+1] = color

def project_point_to_screen(point, cameraParams, epsilon=1e-6):
    cam_pos = np.array([cameraParams[0]['positionX'], 
                        cameraParams[0]['positionY'], 
                        cameraParams[0]['positionZ']], dtype=np.float64)
    cam_dir = np.array([cameraParams[0]['directionX'],
                        cameraParams[0]['directionY'],
                        cameraParams[0]['directionZ']], dtype=np.float64)
    cam_up = np.array([cameraParams[0]['upX'],
                       cameraParams[0]['upY'],
                       cameraParams[0]['upZ']], dtype=np.float64)
    screen_dist = cameraParams[0]['screenDistance']
    W_px = int(cameraParams[0]['screenWidthPx'])
    H_px = int(cameraParams[0]['screenHeightPx'])
    fov = cameraParams[0]['fovHorizontal']
    
    cam_dir = cam_dir / np.linalg.norm(cam_dir)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    cam_right = np.cross(cam_up, cam_dir)
    if np.linalg.norm(cam_right) < epsilon:
        if abs(cam_up[0]) > epsilon:
            cam_right = np.array([cam_up[1], -cam_up[0], 0])
        else:
            cam_right = np.array([0, cam_up[2], -cam_up[1]])
    cam_right = cam_right / np.linalg.norm(cam_right)
    
    cam_up = np.cross(cam_dir, cam_right)
    cam_up = cam_up / np.linalg.norm(cam_up)
    
    screen_center = cam_pos + cam_dir * screen_dist
    
    screen_width_world = 2 * screen_dist * np.tan(fov / 2)
    screen_height_world = screen_width_world * (H_px / W_px)
    
    vec = np.array(point) - cam_pos
    
    dot = np.dot(vec, cam_dir)
    if dot <= epsilon:
        return None
    
    t = screen_dist / dot
    
    if not np.isfinite(t):
        return None
    
    p_screen = cam_pos + t * vec
    
    vec_screen = p_screen - screen_center
    
    x_world = np.dot(vec_screen, cam_right)
    y_world = np.dot(vec_screen, cam_up)
    
    x_norm = x_world / (screen_width_world / 2)
    y_norm = y_world / (screen_height_world / 2)
    
    if abs(x_norm) > 1.0 or abs(y_norm) > 1.0:
        return None
    
    x_px = int((x_norm + 1.0) * (W_px / 2.0))
    y_px = int((1.0 - y_norm) * (H_px / 2.0))
    
    if x_px < 0 or x_px >= W_px or y_px < 0 or y_px >= H_px:
        return None
    
    return [x_px, y_px]


def renderTextBillboard(screen, text, position_3d, cameraParams, color=(255, 255, 255), base_scale=1.0):
    coords_2d = project_point_to_screen(position_3d, cameraParams)

    if coords_2d is None:
        return

    cam_pos = np.array([cameraParams[0]['positionX'],
                        cameraParams[0]['positionY'],
                        cameraParams[0]['positionZ']])
    vec = np.array(position_3d) - cam_pos

    distance = np.linalg.norm(vec)

    if distance < 0.1:
        distance = 0.1

    screen_dist = cameraParams[0]['screenDistance']

    current_scale = (base_scale * screen_dist) / distance

    if current_scale < 0.2:
        return

    x_px, y_px = coords_2d

    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, int(current_scale * 2))

    cv2.putText(screen, text, (x_px, y_px), font,
                current_scale, color, thickness, cv2.LINE_AA)
