import pygame
import socket
import threading
import math
import time

# Initialize pygame
pygame.init()
WIDTH, HEIGHT = 1920, 1080
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Client")
clock = pygame.time.Clock()

# Socket connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))

# Receive player ID
player_id = int(sock.recv(1).decode())
print(f"Connected as Player {player_id}")

# Game state
players = [{"x": 0, "y": 0, "level": 1, "color": (0,0,0), "hp": 100, "size":15, "max_hp":100, "active":0} for _ in range(4)]
boxes = []
bullets = []

def receive_data():
    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                break
                
            parts = data.split('|')
            
            # Parse players
            players_data = parts[0].split(';')
            for i, p_data in enumerate(players_data):
                if p_data and i < 4:
                    fields = p_data.split(',')
                    if len(fields) >= 9:
                        players[i]["x"] = float(fields[1])
                        players[i]["y"] = float(fields[2])
                        players[i]["level"] = int(fields[3])
                        players[i]["color"] = (int(fields[4]), int(fields[5]), int(fields[6]))
                        players[i]["hp"] = float(fields[7])
                        players[i]["size"] = int(fields[8])
                        players[i]["max_hp"] = float(fields[9])
                        players[i]["active"] = int(fields[10])
            
            # Parse boxes
            boxes.clear()
            boxes_data = parts[1].split(';')
            for b_data in boxes_data:
                if b_data:
                    fields = b_data.split(',')
                    if len(fields) >= 4:
                        boxes.append({
                            "id": int(fields[0]),
                            "x": float(fields[1]),
                            "y": float(fields[2]),
                            "hp": int(fields[3])
                        })
            
            # Parse bullets
            bullets.clear()
            bullets_data = parts[2].split(';')
            for b_data in bullets_data:
                if b_data:
                    fields = b_data.split(',')
                    if len(fields) >= 5:
                        bullets.append({
                            "x": float(fields[0]),
                            "y": float(fields[1]),
                            "endx": float(fields[2]),
                            "endy": float(fields[3]),
                            "player_id": int(fields[4])
                        })
            
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

# Start receive thread
recv_thread = threading.Thread(target=receive_data, daemon=True)
recv_thread.start()

# Main game loop
running = True
mouse_pos = (0, 0)
sword_slash_time = 0  
sword_slashing = False

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                sword_slash_time = time.time()
                sword_slashing = True
    
    # Get keyboard state
    keys = pygame.key.get_pressed()
    right = keys[pygame.K_RIGHT]
    left = keys[pygame.K_LEFT]
    up = keys[pygame.K_UP]
    down = keys[pygame.K_DOWN]
    shoot = pygame.mouse.get_pressed()[2]
    slash = pygame.mouse.get_pressed()[0]

    my_player = players[player_id]
    cam_x = max(0, min(int(my_player["x"]) - WIDTH // 2, WORLD_WIDTH - WIDTH))
    cam_y = max(0, min(int(my_player["y"]) - HEIGHT // 2, WORLD_HEIGHT - HEIGHT))
    
    # Scale mouse position to game world
    scaled_mouse_x = mouse_pos[0] + cam_x
    scaled_mouse_y = mouse_pos[1] + cam_y
    
    # Send input to server
    input_data = f"{int(right)},{int(left)},{int(up)},{int(down)},{int(shoot)},{int(slash)},{scaled_mouse_x},{scaled_mouse_y}"
    sock.sendall(input_data.encode())
    
    # Draw everything
    screen.fill((255, 255, 255))

    box_image = pygame.image.load("sprites/box.png")  
    box_image = pygame.transform.scale(box_image, (30, 30))
    
    # Draw boxes
    for box in boxes:
        if box["hp"] > 0:
            screen_x = int(box["x"])-cam_x
            screen_y = int(box["y"])-cam_y
            size = int(15)
            pygame.draw.rect(screen, (100, 0, 0), (screen_x - size, screen_y - size, size*2, size*2))
            image_rect = box_image.get_rect(center=(screen_x, screen_y))
            screen.blit(box_image, image_rect)
    
    # Draw players
    for i, player in enumerate(players):
        if int(player["active"])==1:
            screen_x = int(player["x"])-cam_x
            screen_y = int(player["y"])-cam_y
            size = int(player["size"] + 3*(player["level"]-1))
            
            pygame.draw.circle(screen, player["color"], (screen_x, screen_y), size)
            
            # Draw HP bar
            bar_width = size * 2
            pygame.draw.rect(screen, (0,0,0), (screen_x - size, screen_y - size - 10, bar_width, 5), 1)
            hp_width = int(bar_width * (player["hp"] / player["max_hp"]))
            pygame.draw.rect(screen, (0,255,0), (screen_x - size, screen_y - size - 9, hp_width, 4))

            font = pygame.font.SysFont('Arial', 14)
            text_surface = font.render(f"Lvl {player['level']}", True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(screen_x, screen_y - size - 18))  
            screen.blit(text_surface, text_rect)

            if i == player_id:
                sword_img = pygame.image.load("sprites/sword.png").convert_alpha()
                sword_img = pygame.transform.scale(sword_img, (40+(10*int(player["level"])), 40+(10*int(player["level"]))))

                # Animacja zamachu
                if sword_slashing:
                    elapsed = time.time() - sword_slash_time
                    duration = 1.0 
                    if elapsed <= duration:
                        angle = -15 - (elapsed / duration) * 180
                    else:
                        angle = -135
                        sword_slashing = False
                else:
                    angle = -15

                rotated_sword = pygame.transform.rotate(sword_img, angle)

                # Ustawienie miecza obok gracza
                sword_rect = rotated_sword.get_rect(center=(screen_x + size, screen_y))
                screen.blit(rotated_sword, sword_rect)
    
    # Draw bullets
    for bullet in bullets:
        screen_x = int(bullet["x"])-cam_x
        screen_y = int(bullet["y"])-cam_y
        size = int(3)
        
        # Rysuj pocisk
        color = (255,0,0) if bullet["player_id"] != player_id else (0,0,255)
        pygame.draw.circle(screen, color, (screen_x, screen_y), size)

    border_color = (255, 0, 0)
    border_thickness = 4

    # Top border
    pygame.draw.line(screen, border_color, 
        (0 - cam_x, 0 - cam_y), 
        (WORLD_WIDTH - cam_x, 0 - cam_y), border_thickness)

    # Bottom border
    pygame.draw.line(screen, border_color, 
        (0 - cam_x, WORLD_HEIGHT - cam_y), 
        (WORLD_WIDTH - cam_x, WORLD_HEIGHT - cam_y), border_thickness)

    # Left border
    pygame.draw.line(screen, border_color, 
        (0 - cam_x, 0 - cam_y), 
        (0 - cam_x, WORLD_HEIGHT - cam_y), border_thickness)

    # Right border
    pygame.draw.line(screen, border_color, 
        (WORLD_WIDTH - cam_x, 0 - cam_y), 
        (WORLD_WIDTH - cam_x, WORLD_HEIGHT - cam_y), border_thickness)

    pygame.display.flip()
    clock.tick(60)

sock.close()
pygame.quit()