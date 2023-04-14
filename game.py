import pygame
import speech_recognition as sr
import time
import threading
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 640, 480

# Create the game window
screen = pygame.display.set_mode((width, height))

# Set the title
pygame.display.set_caption("Voice Controlled Dots")

# Clock object to control the frame rate
clock = pygame.time.Clock()

# Dot properties
dot_radius = 10
dot_color = (255, 255, 255)
dot_base_y = height - 30

# Movement properties
walk_speed = 20
run_speed = 50

# Distance scale
scale = 20  # 1 meter = 20 pixels
meter_width = 2

# Dots dictionary
dots = {}

# Movements list
movements = []
import random

def generate_sectors():
    num_sectors = random.randint(3, 6)
    sector_names = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"][:num_sectors]
    sectors = {}
    attempts = 0
    for name in sector_names:
        while attempts < 1000:
            x1, y1 = random.randint(0, width - 50), random.randint(0, height - 50)
            x2, y2 = x1 + random.randint(50, width // 2), y1 + random.randint(50, height // 2)
            rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)
            if not any(rect.colliderect(other) for other in sectors.values()):
                sectors[name] = rect
                break
            attempts += 1
    return sectors


sectors = generate_sectors()

def draw_sectors():
    for name, sector in sectors.items():
        pygame.draw.rect(screen, (255, 255, 255), sector, 2)
        font = pygame.font.Font(None, 24)
        text = font.render(name, True, (255, 255, 255))
        screen.blit(text, (sector.x + 5, sector.y + 5))


# Speech recognition
recognizer = sr.Recognizer()

# Command queue
command_queue = []

def recognize_speech():
    while True:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source, phrase_time_limit=5)

        try:
            command = recognizer.recognize_google(audio, show_all=True)
            if command:
                command = command['alternative'][0]['transcript'].lower()
                print("Recognized:", command)
            else:
                command = ""
            print(f"Recognized: {command}")
            command_queue.append(command)
        except Exception as e:
            print(f"Error: {e}")

# Start speech recognition thread
speech_thread = threading.Thread(target=recognize_speech, daemon=True)
speech_thread.start()

def draw_scale():
    for i in range(0, width, scale):
        pygame.draw.rect(screen, (255, 255, 255), (i, height - 20, meter_width, 10))

def update_movements(delta_time):
    new_movements = []
    for movement in movements:
        dot, dx, dy, distance, start_time, speed = movement
        move_distance = speed * delta_time

        if distance > move_distance:
            new_x = dot["x"] + dx * move_distance
            new_y = dot["y"] + dy * move_distance

            if 0 <= new_x <= width and 0 <= new_y <= height:
                dot["x"] = new_x
                dot["y"] = new_y
                remaining_distance = distance - move_distance
                new_movements.append((dot, dx, dy, remaining_distance, start_time, speed))
        else:
            new_x = dot["x"] + dx * distance
            new_y = dot["y"] + dy * distance

            if 0 <= new_x <= width and 0 <= new_y <= height:
                dot["x"] = new_x
                dot["y"] = new_y

    return new_movements


def draw_dot_name(dot_name, x, y, selected):
    font = pygame.font.Font(None, 24)
    text = font.render(dot_name, True, (0, 255, 0) if selected else (0, 0, 255))
    screen.blit(text, (x - text.get_width() // 2, y + dot_radius + 5))

selected_dot = None

running = True

while running:
    screen.fill((0, 0, 0))
    draw_sectors()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if command_queue:
        command = command_queue.pop(0)
    else:
        command = ""

    # Process the command
    words = command.split()
    if words:
        name = words[0]
       
        if name in dots:
            selected_dot = name
            print(f"Dot '{selected_dot}' selected.")
            words = words[1:]

    if "create" in command:
        if len(words) > 1:
            name = words[-1]
            if name not in dots:
                dots[name] = {
                    "x": width // 2,
                    "y": dot_base_y,
                }
                print(f"Dot '{name}' created.")
            else:
                print("Dot with that name already exists.")

    if selected_dot is not None and words:
        speed = walk_speed
        if "run" in command:
            speed = run_speed
        if "stop" in words:
            movements = [m for m in movements if m[0] != dots[selected_dot]]
        if "navigate to" in command:
            words = command.split()
            if len(words) > 2:
                target_sector = words[-1]
                if target_sector in sectors:
                    sector = sectors[target_sector]
                    target_x = sector.left + sector.width // 2
                    target_y = sector.top + sector.height // 2
                    dx = target_x - dots[selected_dot]["x"]
                    dy = target_y - dots[selected_dot]["y"]
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance != 0:
                        dx /= distance
                        dy /= distance
                        movements = [m for m in movements if m[0] != dots[selected_dot]]
                        movements.append((dots[selected_dot], dx, dy, distance, time.time(), speed))
                else:
                    print(f"Unrecognized sector '{target_sector}'.")


        try:
            distance = float(words[-2]) * scale
            if "at" in command:
                bearing = float(words[-1])
                dx = math.cos(math.radians(90 - bearing))
                dy = -math.sin(math.radians(90 - bearing))
            else:
                direction = words[-1]
                dx, dy = 0, 0
                if direction == "north":
                    dy = -1
                elif direction == "south":
                    dy = 1
                elif direction == "east":
                    dx = 1
                elif direction == "west":
                    dx = -1
            movements = [m for m in movements if m[0] != dots[selected_dot]]

            movements.append((dots[selected_dot], dx, dy, distance, time.time(), speed))
        except (ValueError, IndexError):
            pass
    if "quit" in command:
        running = False

    movements = update_movements(clock.tick(30) / 1000)

    draw_scale()

    for dot_name, dot in dots.items():
        pygame.draw.circle(screen, dot_color, (int(dot["x"]), int(dot["y"])), dot_radius)
        draw_dot_name(dot_name, int(dot["x"]), int(dot["y"]), selected_dot == dot_name)

    pygame.display.flip()

pygame.quit()

#TODO: prevent WaitTimeoutError 
#TODO: continually listen but end command when 1 second of no recognisable command words have been said.
#TODO: when run or walk said to a selected dot, the speed should change to the speed said
#TODO: command "fire {direction}" fires a rectangle projectile at a speed of 200 time walk speed
#TODO: help command which displays alist of possible commands
#TODO: refactor