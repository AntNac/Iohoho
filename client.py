import pygame
import socket
import threading
import math

# Initialize pygame
pygame.init()
WIDTH, HEIGHT = 500, 500
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
players = [{"x": 0, "y": 0, "level": 1, "color": (0,0,0), "hp": 100, "size":15, "max_hp":100} for _ in range(2)]
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
                if p_data and i < 2:
                    fields = p_data.split(',')
                    if len(fields) >= 8:
                        players[i]["x"] = float(fields[1])
                        players[i]["y"] = float(fields[2])
                        players[i]["level"] = int(fields[3])
                        players[i]["color"] = (int(fields[4]), int(fields[5]), int(fields[6]))
                        players[i]["hp"] = float(fields[7])
                        players[i]["size"] = int(fields[8])
                        players[i]["max_hp"] = float(fields[9])
            
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
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
    
    # Get keyboard state
    keys = pygame.key.get_pressed()
    right = keys[pygame.K_RIGHT]
    left = keys[pygame.K_LEFT]
    up = keys[pygame.K_UP]
    down = keys[pygame.K_DOWN]
    shoot = pygame.mouse.get_pressed()[0]
    
    # Scale mouse position to game world
    scaled_mouse_x = mouse_pos[0]
    scaled_mouse_y = mouse_pos[1]
    
    # Send input to server
    input_data = f"{int(right)},{int(left)},{int(up)},{int(down)},{int(shoot)},{scaled_mouse_x},{scaled_mouse_y}"
    sock.sendall(input_data.encode())
    
    # Draw everything
    screen.fill((255, 255, 255))
    
    # Draw boxes
    for box in boxes:
        if box["hp"] > 0:
            screen_x = int(box["x"])
            screen_y = int(box["y"])
            size = int(15)
            pygame.draw.rect(screen, (100, 0, 0), 
                           (screen_x - size, screen_y - size, size*2, size*2))
    
    # Draw players
    for i, player in enumerate(players):
        screen_x = int(player["x"])
        screen_y = int(player["y"])
        size = int(player["size"] + 3*(player["level"]-1))
        
        pygame.draw.circle(screen, player["color"], (screen_x, screen_y), size)
        
        # Draw HP bar
        bar_width = size * 2
        pygame.draw.rect(screen, (0,0,0), (screen_x - size, screen_y - size - 10, bar_width, 5), 1)
        hp_width = int(bar_width * (player["hp"] / player["max_hp"]))
        pygame.draw.rect(screen, (0,255,0), (screen_x - size, screen_y - size - 9, hp_width, 4))
    
    # Draw bullets
    for bullet in bullets:
        screen_x = int(bullet["x"])
        screen_y = int(bullet["y"] )
        size = int(3)
        
        # Rysuj pocisk
        color = (255,0,0) if bullet["player_id"] != player_id else (0,0,255)
        pygame.draw.circle(screen, color, (screen_x, screen_y), size)

    pygame.display.flip()
    clock.tick(60)

sock.close()
pygame.quit()