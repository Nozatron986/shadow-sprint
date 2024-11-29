import os
import pygame
import sys
import random
import math
import time
import sqlite3

DB_DIRECTORY = os.path.expanduser("Light-game/game_data")
DB_FILE = os.path.join(DB_DIRECTORY, 'scores.db')

os.makedirs(DB_DIRECTORY, exist_ok=True)

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

font = pygame.font.SysFont(None, 36)

pygame.display.set_caption('Light Game')
SKY_BLUE = (105, 186, 255)
DARK_GREY = (72, 72, 72)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

NUMBER_OF_GRIDS = 20
GRID_SIZE = SCREEN_HEIGHT // NUMBER_OF_GRIDS

NUMBER_OF_BOXES_IN_CENTER = 4   
CENTER_BOX_SIZE = NUMBER_OF_BOXES_IN_CENTER * GRID_SIZE

bad_tiles = [[], []]  # List to hold bad tiles for level 1 and level 2

# Define the boundaries based on the positions of the black tiles
bad_tiles_min_orb = 0  # Minimum x or y coordinate for good tiles
bad_tiles_max = NUMBER_OF_GRIDS - 1  # Maximum x or y coordinate for good tiles

# Update available_good_tiles based on the defined boundaries
available_good_tiles = []

DEFAULT_LIGHT_SIZE = (GRID_SIZE*2, GRID_SIZE*2)

orbs = [pygame.image.load(f'Light-game/sprites/{n+1}Orb.png') for n in range(11)]
orbs = [pygame.transform.scale(orb, DEFAULT_LIGHT_SIZE) for orb in orbs]

coin_image = pygame.image.load(f'Light-game/sprites/coin.png')
coin_image = pygame.transform.scale(coin_image, (GRID_SIZE, GRID_SIZE))

NUM_ORBS = len(orbs)

score = 0
top_score = 0

time_last_moved = time.time()
time_remaining = 30
time_start = 30

immunity_time = 3
is_invincible = True
invincible_start_time = 0

grid = [[DARK_GREY for _ in range(NUMBER_OF_GRIDS)] for _ in range(NUMBER_OF_GRIDS)]

grid_level_1 = [[DARK_GREY for _ in range(NUMBER_OF_GRIDS)] for _ in range(NUMBER_OF_GRIDS)]
grid_level_2 = [[DARK_GREY for _ in range(NUMBER_OF_GRIDS)] for _ in range(NUMBER_OF_GRIDS)]

# Initialize the grids with obstacles
def initialize_grids():
    global bad_tiles  # Use the global bad_tiles variable

    # Clear previous bad tiles
    bad_tiles = [[], []]

    # Level 1: Define a 4x4 grid in the center
    center_x = NUMBER_OF_GRIDS // 2
    center_y = NUMBER_OF_GRIDS // 2
    for x in range(center_x - 2, center_x + 2):  # 4 tiles wide
        for y in range(center_y - 2, center_y + 2):  # 4 tiles tall
            grid_level_1[x][y] = BLACK  # Set black squares for Level 1
            bad_tiles[0].append((x, y))  # Add to bad tiles for Level 1

    # Level 2: Define a vertical line in the center, only 6 tiles long
    line_x = NUMBER_OF_GRIDS // 2
    for y in range(NUMBER_OF_GRIDS // 2 - 3, NUMBER_OF_GRIDS // 2 + 3):  # 6 tiles long
        grid_level_2[line_x][y] = BLACK  # Set black squares for Level 2
        bad_tiles[1].append((line_x, y))  # Add to bad tiles for Level 2

    # Avoid modifying the list while iterating over it
    for k in range(2):
        new_bad_tiles = []  # Create a new list to hold additional bad tiles
        for x, y in bad_tiles[k]:
            if (x - 1, y) not in bad_tiles[k]:  # Check both sides
                new_bad_tiles.append((x - 1, y))
            if (x, y - 1) not in bad_tiles[k]:  # Check both sides
                new_bad_tiles.append((x, y - 1))
            if (x - 1, y - 1) not in bad_tiles[k]:  # Check both sides
                new_bad_tiles.append((x - 1, y - 1))
        bad_tiles[k].extend(new_bad_tiles)  # Add new bad tiles to the list

    return

def update_available_good_tiles():
    global available_good_tiles
    available_good_tiles = [[(x, y) for x in range(NUMBER_OF_GRIDS) for y in range(NUMBER_OF_GRIDS) if (x, y) not in bad_tiles[0] and (x, y) not in bad_tiles[0]], 
                            [(x, y) for x in range(NUMBER_OF_GRIDS) for y in range(NUMBER_OF_GRIDS) if (x, y) not in bad_tiles[1] and (x, y) not in bad_tiles[1]]]
    return

def can_see(orb_center, square_center, current_grid):
    x1, y1 = orb_center
    x2, y2 = square_center

    dx = x2 - x1
    dy = y2 - y1
    distance = math.hypot(dx, dy)

    steps = int(distance / GRID_SIZE * 2)  # Finer steps for accuracy
    for step in range(1, steps):
        px = x1 + dx * step / steps
        py = y1 + dy * step / steps

        # Check if this point falls inside any black square
        grid_x = int(px // GRID_SIZE)
        grid_y = int(py // GRID_SIZE)
        if 0 <= grid_x < NUMBER_OF_GRIDS and 0 <= grid_y < NUMBER_OF_GRIDS:
            if current_grid[grid_x][grid_y] == BLACK:
                return False  # If the orb's light hits a black tile, it cannot see through

    return True

def draw_screen(orb_pos, level=1):
    orb_center = (orb_pos[0] + 0.5) * GRID_SIZE, (orb_pos[1] + 0.5) * GRID_SIZE
    
    # Select the appropriate grid based on the level
    current_grid = grid_level_1 if level == 1 else grid_level_2

    for x in range(NUMBER_OF_GRIDS):
        for y in range(NUMBER_OF_GRIDS):
            square_center = (x + 0.5) * GRID_SIZE, (y + 0.5) * GRID_SIZE
            
            # Check if the orb can see the square
            if can_see(orb_center, square_center, current_grid):
                grid[x][y] = WHITE  # Set color to white if visible
            else:
                grid[x][y] = current_grid[x][y]  # Use the current grid's color
            
            # Ensure that black tiles remain black
            if current_grid[x][y] == BLACK:
                grid[x][y] = BLACK

            pygame.draw.rect(screen, grid[x][y], (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, BLACK, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)

def advance_timer():
	global top_score, score, time_remaining

	timer_txt = font.render(f"Time left: {time_remaining:.1f}s", True, BLACK)
	screen.blit(timer_txt, (10, 60))

	# Display score in the top right corner
	score_txt = font.render(f"Score: {score}", True, BLACK)
	screen.blit(score_txt, (SCREEN_WIDTH - score_txt.get_width() - 10, 10))  # Adjust position

	if time_remaining <= 0:
		if score > top_score:
			top_score = score
		game_over_display()

def game_over_display():
    global score
    user_text = ''  # Initialize user text for input
    active = False  # Input box active state
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 50, 140, 32)  # Input box rectangle
    color_active = pygame.Color('lightskyblue3')  # Active color
    color_passive = pygame.Color('chartreuse4')  # Passive color
    color = color_passive  # Initial color

    while True:  # Loop until name is entered
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    active = True
                else:
                    active = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                elif event.key == pygame.K_RETURN:  # Save name on Enter
                    if len(user_text) <= 20:  # Check if username is within the limit
                        insert_score(score, user_text)  # Insert the score and player name into the database
                        display_leaderboard()  # Display the leaderboard after saving the score
                        return  # Exit the loop and function
                else:
                    if len(user_text) < 20:  # Limit the length of the username
                        user_text += event.unicode

        # Draw the game over screen
        screen.fill(BLACK)  # Clear the screen with the background color
        game_over_txt = font.render("Game Over", True, WHITE)
        score_txt = font.render(f"Your score was: {score}", True, WHITE)
        continue_txt = font.render("Enter your name:", True, WHITE)

        # Draw the above text onto the screens
        screen.blit(game_over_txt, (SCREEN_WIDTH // 2 - game_over_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(continue_txt, (SCREEN_WIDTH // 2 - continue_txt.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        # Draw input box
        if active:
            color = color_active
        else:
            color = color_passive
        pygame.draw.rect(screen, color, input_rect)

        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        input_rect.w = max(100, text_surface.get_width() + 10)

        pygame.display.flip()

def display_leaderboard():
    scores = get_all_scores()  # Retrieve scores from the database
    screen.fill(BLACK)  # Clear the screen

    skip_text = font.render("Press SPACE to go to the menu", True, WHITE)
    screen.blit(skip_text, (SCREEN_WIDTH // 2 - skip_text.get_width() // 2, SCREEN_HEIGHT // 2 - 300))

    leaderboard_txt = font.render("Leaderboard:", True, WHITE)
    screen.blit(leaderboard_txt, (SCREEN_WIDTH // 2 - leaderboard_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 150))

    # Limit to top 10 scores
    top_scores = scores[:10]  # Get only the top 10 scores

    for i, (_, score, player_name) in enumerate(top_scores):
        score_txt = font.render(f"{i + 1}. {player_name}: {score}", True, WHITE)
        screen.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 100 + (i * 30)))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False

    screen.fill(BLACK)
    main_menu()

def closest(position, targets):
    smallest_dif = 100
    smallest_target = ()

    for target in targets:
        dist = (target[0] - position[0])**2 + (target[1] - position[1])**2
        if dist < smallest_dif:
            smallest_dif = dist
            smallest_target = target
    
    return smallest_target

def main_music():
    pygame.mixer.init()
    pygame.mixer.music.load('Light-game/sprites/Pure Darkness.mp3')
    pygame.mixer.music.play()
    pygame.mixer.music.load('Light-game/sprites/Intro.mp3')
    pygame.mixer.music.play()

def coin_pos(level):
    while True:
        ret = (random.randint(0, NUMBER_OF_GRIDS-1), random.randint(0, NUMBER_OF_GRIDS-1))

        if ret not in bad_tiles[level-1]:
            return ret

def game_loop(level=1):
    global time_last_moved, score, time_remaining, is_invincible, invincible_start_time

    prev_time = time.time()
    coin = coin_pos(level)
    screen.fill(BLACK)
    orb_number = 0
    running = True

    # Character setup
    character_pos = [0, 0]  # Starting at the top-left corner
    character_sprite = pygame.image.load("Light-game/sprites/Character Right.png")
    character_sprite = pygame.transform.scale(character_sprite, (GRID_SIZE, GRID_SIZE))  # Scale to grid size

    # Main game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        # Get the keys currently pressed down
        keys = pygame.key.get_pressed()

        # Update character position based on keys
        if time.time() - time_last_moved >= 0.15:  # Check if enough time has passed
            prev_pos = character_pos[:]
            if keys[pygame.K_w] and character_pos[1] > 0:
                character_pos[1] -= 1
                time_last_moved = time.time()
            elif keys[pygame.K_s] and character_pos[1] < NUMBER_OF_GRIDS - 1:
                character_pos[1] += 1
                time_last_moved = time.time()
            elif keys[pygame.K_a] and character_pos[0] > 0:
                character_pos[0] -= 1
                time_last_moved = time.time()
            elif keys[pygame.K_d] and character_pos[0] < NUMBER_OF_GRIDS - 1:
                character_pos[0] += 1
                time_last_moved = time.time()
            
            if grid[character_pos[0]][character_pos[1]] == BLACK:
                character_pos = prev_pos

            if grid[character_pos[0]][character_pos[1]] == WHITE and not is_invincible:
                game_over_display()
                running = False

        time_current = time.time()
        time_split = time_current - prev_time
        time_remaining -= time_split
        prev_time = time_current

        if time_start - immunity_time >= time_remaining:
            is_invincible = False

        # Get orb position based on mouse
        mx, my = pygame.mouse.get_pos()
        mx, my = mx // GRID_SIZE, my // GRID_SIZE

        # Avoid the center blocking region for the orb
        if (mx, my) in bad_tiles[level-1]:
            mx, my = closest((mx, my), available_good_tiles[level-1])

        # Clear the screen
        screen.fill(DARK_GREY)

        # Draw the grid and center blocking region
        draw_screen((mx, my), level)

        # Draw the orb
        if mx == NUMBER_OF_GRIDS-1:
            mx -= 1
        if my == NUMBER_OF_GRIDS-1:
            my -= 1
        
        screen.blit(orbs[round(orb_number % (NUM_ORBS - 1))], (mx * GRID_SIZE, my * GRID_SIZE))

        # Check if the character is on the same square as the coin
        if character_pos[0] == coin[0] and character_pos[1] == coin[1]:
            score += 1
            coin = coin_pos(level)

        # Draw the character sprite (locked to grid)
        screen.blit(
            character_sprite,
            (character_pos[0] * GRID_SIZE, character_pos[1] * GRID_SIZE),
        )

        # Draw the coin
        screen.blit(coin_image, (coin[0] * GRID_SIZE, coin[1] * GRID_SIZE))

        # Update timer and screen
        advance_timer()
        if time_remaining <= 0:
            game_over_display()
            running = False

        pygame.display.flip()

        # Update orb animation frame
        orb_number += 0.001


#--------------------------------------------------#
#--------------------------------------------------#
#--------------------------------------------------#

class Button():
	def __init__(self, image, pos, text_input, font, base_color, hovering_color):
		self.image = image
		self.x_pos = pos[0]
		self.y_pos = pos[1]
		self.font = font
		self.base_color, self.hovering_color = base_color, hovering_color
		self.text_input = text_input
		self.text = self.font.render(self.text_input, True, self.base_color)
		if self.image is None:
			self.image = self.text
		self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
		self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

	def update(self, screen):
		if self.image is not None:
			screen.blit(self.image, self.rect)
		screen.blit(self.text, self.text_rect)

	def checkForInput(self, position):
		if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
			return True
		return False

	def changeColor(self, position):
		if self.checkForInput(position):
			self.text = self.font.render(self.text_input, True, self.hovering_color)
		else:
			self.text = self.font.render(self.text_input, True, self.base_color)

button_surface = pygame.image.load("Light-game/sprites/grey box.png")
button_surface = pygame.transform.scale(button_surface, (SCREEN_WIDTH/2,SCREEN_HEIGHT/2))

button = Button(button_surface, (SCREEN_WIDTH/2, SCREEN_HEIGHT/2), "Button", font, WHITE, BLACK)
pygame.display.set_caption("Menu")

BG = pygame.image.load("Light-game/sprites/Black.png")

def tutorial():
    tutorial_text = "You can control the orb with your mouse"
    ORB_RECT = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT * 0.1)  # Create a rect for positioning
    index = 0  # Initialize index for the text

    while index <= len(tutorial_text):  # Loop until the entire text is displayed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)  # Clear the screen
        ORB_TEXT = get_font(SCREEN_HEIGHT // 50).render(tutorial_text[:index], True, GREEN)  # Render text up to the current index
        
        # Center the text both horizontally and vertically
        ORB_RECT.center = (SCREEN_WIDTH / 2 + 50, SCREEN_HEIGHT / 2)  # Updated to center vertically

        # Get mouse position for orb movement
        mx, my = pygame.mouse.get_pos()
        mx //= GRID_SIZE
        my //= GRID_SIZE

        # Ensure the orb stays within the grid bounds
        mx = max(0, min(mx, NUMBER_OF_GRIDS - 1))
        my = max(0, min(my, NUMBER_OF_GRIDS - 1))

        # Draw the orb at the mouse position
        screen.blit(orbs[0], (mx * GRID_SIZE, my * GRID_SIZE))  # Assuming orbs[0] is the default orb image

        screen.blit(ORB_TEXT, ORB_RECT)  # Draw the text on the screen
        pygame.display.flip()  # Update the display

        index += 1  # Move to the next character
        time.sleep(0.1)  # Pause for a short duration to create the typewriter effect

    pygame.quit()
    sys.exit()

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("Light-game/sprites/font.ttf", size)

def main_menu():
    main_music()
    global button_surface  # Declare button_surface as global if it's defined outside this function
    button_surface = pygame.image.load("Light-game/sprites/grey box.png")  # Ensure it's loaded here
    button_surface = pygame.transform.scale(button_surface, (SCREEN_WIDTH *0.7, SCREEN_HEIGHT / 10))  # Scale it here

    while True:
        screen.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        MENU_TEXT = get_font(SCREEN_HEIGHT // 15).render("MAIN MENU", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1))

        LEVEL_SELECT_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.4), 
                                      text_input="LEVEL SELECT", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")
        TUTORIAL_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.6), 
                                 text_input="TUTORIAL", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8), 
                             text_input="QUIT", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")

        screen.blit(MENU_TEXT, MENU_RECT)

        for button in [LEVEL_SELECT_BUTTON, TUTORIAL_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if LEVEL_SELECT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    level_select()  # Go to level selection
                if TUTORIAL_BUTTON.checkForInput(MENU_MOUSE_POS):
                    # Call the tutorial function here (assuming you have one)
                    tutorial()  # Replace with your tutorial function
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

def reset_game_state():
    global score, time_remaining, is_invincible, invincible_start_time, character_pos

    score = 0
    time_remaining = 30
    is_invincible = True
    invincible_start_time = 0
    character_pos = [0, 0]  # Reset character position to the starting point

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                player_name TEXT NOT NULL
            )
        ''')
        conn.commit()

def insert_score(score, player_name):
    scores = get_all_scores()  # Retrieve current scores from the database

    # Check if the new score qualifies for the top 10
    if len(scores) < 10 or score > scores[-1][1]:  # If there are less than 10 scores or the new score is higher than the lowest score
        # If we have 10 scores, remove the lowest one
        if len(scores) == 10:
            lowest_score_id = scores[-1][0]  # Get the ID of the lowest score
            remove_score(lowest_score_id)  # Remove the lowest score from the database

        # Insert the new score
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO scores (score, player_name) VALUES (?, ?)', (score, player_name))
            conn.commit()
    return

def get_all_scores():
    with sqlite3.connect(DB_FILE) as conn:  # Use 'with' to manage the connection
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM scores ORDER BY score DESC')
        scores = cursor.fetchall()
    return scores

def reset_game_state():
    global score, time_remaining, is_invincible, invincible_start_time, character_pos

    score = 0
    time_remaining = 30
    is_invincible = True
    invincible_start_time = 0
    character_pos = [0, 0]  # Reset character position to the starting point

def remove_score(score_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
        conn.commit()

def level_select():
    while True:
        screen.fill(BLACK)
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        LEVEL_TEXT = get_font(SCREEN_HEIGHT // 15).render("SELECT LEVEL", True, "#b68f40")
        LEVEL_RECT = LEVEL_TEXT.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1))

        LEVEL_1_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.4), 
                                text_input="LEVEL 1", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")
        LEVEL_2_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.6), 
                                text_input="LEVEL 2", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")
        BACK_BUTTON = Button(image=button_surface, pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.8), 
                             text_input="BACK", font=get_font(SCREEN_HEIGHT // 20), base_color="#d7fcd4", hovering_color="White")

        screen.blit(LEVEL_TEXT, LEVEL_RECT)

        for button in [LEVEL_1_BUTTON, LEVEL_2_BUTTON, BACK_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if LEVEL_1_BUTTON.checkForInput(MENU_MOUSE_POS):
                    reset_game_state()
                    game_loop(level=1)  # Start level 1
                if LEVEL_2_BUTTON.checkForInput(MENU_MOUSE_POS):
                    reset_game_state()
                    game_loop(level=2)  # Start level 2
                if BACK_BUTTON.checkForInput(MENU_MOUSE_POS):
                    main_menu()  # Go back to main menu

        pygame.display.update()

initialize_grids()
update_available_good_tiles()

main_menu()
