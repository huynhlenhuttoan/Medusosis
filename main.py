import pygame, random

WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 768
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Medusosis")
clock = pygame.time.Clock()
is_fullscreen = False

#Load Resources
Blue75 = pygame.image.load("Resources/Images/Map/Blue75.png").convert_alpha()
Blue25 = pygame.image.load("Resources/Images/Map/Blue25.png").convert_alpha()
Red75 = pygame.image.load("Resources/Images/Map/Red75.png").convert_alpha()
Red25 = pygame.image.load("Resources/Images/Map/Red25.png").convert_alpha()
Avaiable = pygame.image.load("Resources/Images/Map/Avaiable.png").convert_alpha()
Not_Avaiable = pygame.image.load("Resources/Images/Map/Not_Avaiable.png").convert_alpha()
Found25 = pygame.image.load("Resources/Images/Map/Found25.png").convert_alpha()
Found75 = pygame.image.load("Resources/Images/Map/Found75.png").convert_alpha()
Missed25 = pygame.image.load("Resources/Images/Map/Missed25.png").convert_alpha()
Missed75 = pygame.image.load("Resources/Images/Map/Missed75.png").convert_alpha()
test = pygame.image.load("Resources/Images/Operator/B_Baphomet_1.png").convert_alpha()
test_2 = pygame.image.load("Resources/Images/Operator/R_Guminho_1.png").convert_alpha()

#Map settings
TILE_SIZE = 75
OVERLAP = 3
EFFECTIVE_TILE_SIZE = TILE_SIZE - OVERLAP
MAP_SIZE = 10
MAP_PIXEL_SIZE = MAP_SIZE * EFFECTIVE_TILE_SIZE

SMALL_TILE_SIZE = 25
SMALL_OVERLAP = 1
EFFECTIVE_SMALL_TILE_SIZE = SMALL_TILE_SIZE - SMALL_OVERLAP
SMALL_MAP_PIXEL_SIZE = MAP_SIZE * EFFECTIVE_SMALL_TILE_SIZE
MAP_GAP = 20

# Initialize matrices
player_blue_matrix = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]  # 0 = Blue tile
player_red_matrix = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]   # 0 = Red tile

#Defining variables
phase = "Ready"
edit_mode = False
selected_weakness = None
temp_matrix = None
temp_relative_positions = None # Temporary matrix after rotation
temp_image = None #Temporary image path used for hightlighted block until the edit mode ends
weakness_shape = None  # Selected weakness shape (relative_positions matrix)
mouse_clicked = False
right_mouse_clicked = False
selected_offset = None  # (y, x) relative position of the block in clicked unit
enemy_weakness = []
enemy_targets = {}
last_shot_time = 0 # (ms)
waiting_for_turn = False
think = False
start_thinking = 0 # (ms)
thinking_time = 0
game_over = False
game_over_time = 0
font_large = pygame.font.SysFont("arial", 80)
font_small = pygame.font.SysFont("arial", 40)

deity_data = [
    {
        "id": 1,
        "name": "deity",
        "weakness": [ #If change rotation, relative_positions must be recalculated
            {"id": 1, "image": "Resources/Images/Units/BT_2.png", "relative_positions": [[1, 1]], "rotation": 0},
            #{"id": 2, "image": "Resources/Images/Units/BT_2.png", "relative_positions": [[1, 1]], "rotation": 1},
            {"id": 2, "image": "Resources/Images/Units/BT_6.png", "relative_positions": [[1, 0],
                                                                                         [1, 1]], "rotation": 0},
            {"id": 3, "image": "Resources/Images/Units/BT_3.png", "relative_positions": [[1, 1, 1]], "rotation": 0},
            {"id": 4, "image": "Resources/Images/Units/BT_4.png", "relative_positions": [[1, 1, 1, 1]], "rotation": 0},
            {"id": 5, "image": "Resources/Images/Units/BT_7.png", "relative_positions": [[1, 1],
                                                                                         [1, 1]], "rotation": 0},
        ]
    }
]

# Function to convert relative_positions to matrix
def positions_to_matrix(positions):
    if not positions:
        return [[]]
    max_x = max(x for x, _ in positions)
    max_y = max(y for _, y in positions)
    matrix = [[0 for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    for x, y in positions:
        matrix[y][x] = 1
    return matrix

def rotate_matrix(matrix, rotation):
    if rotation == 0:
        return matrix
    rows = len(matrix)
    cols = len(matrix[0])
    
    if rotation == 1:  # 90 degrees clockwise
        new_matrix = [[0 for _ in range(rows)] for _ in range(cols)]
        for i in range(rows):
            for j in range(cols):
                new_matrix[j][rows - 1 - i] = matrix[i][j]
        return new_matrix
    elif rotation == 2:  # 180 degrees
        new_matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                new_matrix[rows - 1 - i][cols - 1 - j] = matrix[i][j]
        return new_matrix
    elif rotation == 3:  # 270 degrees clockwise
        new_matrix = [[0 for _ in range(rows)] for _ in range(cols)]
        for i in range(rows):
            for j in range(cols):
                new_matrix[cols - 1 - j][i] = matrix[i][j]
        return new_matrix
    return matrix

def edit_rotate(matrix):# Rotate matrix 90 degrees clockwise (in edit mode)
    return [list(row) for row in zip(*matrix[::-1])]

def rotate_offset_90_clockwise(offset, shape_height, shape_width):
    y, x = offset
    return (x, shape_height - 1 - y)

# Function to place weaknesses randomly
def place_weaknesses_random(deity_id):
    deity = deity_data[0]  # Only one deity for now
    weakness = deity["weakness"]
    placed_weakness = []
    
    for child in weakness:
        max_attempts = 100  # Limit attempts to avoid infinite loop
        while max_attempts > 0:
            start_row = random.randint(0, MAP_SIZE - 1)
            start_col = random.randint(0, MAP_SIZE - 1)

            # Rotate matrix base on rotation
            matrix = rotate_matrix(child["relative_positions"], child["rotation"])
            # Convert matrix into (x,y) list
            positions = []
            for y in range(len(matrix)):
                for x in range(len(matrix[0])):
                    if matrix[y][x] == 1:
                        positions.append((x, y))

            is_valid = True
            
            for x, y in positions:
                row = start_row + y
                col = start_col + x
                if (row >= MAP_SIZE or col >= MAP_SIZE or row < 0 or col < 0 or 
                    player_blue_matrix[row][col] == 1):
                    is_valid = False
                    break
            
            if is_valid:
                for x, y in positions:
                    row = start_row + y
                    col = start_col + x
                    player_blue_matrix[row][col] = 1
                placed_weakness.append({
                    "weakness_id": child["id"],
                    "start_row": start_row,
                    "start_col": start_col,
                    "relative_positions": matrix, # Save rotated matrix
                    "rotation": child["rotation"]
                })
                break
            max_attempts -= 1
    
    return placed_weakness

# Place all weaknesses randomly at start
placed_weakness = place_weaknesses_random(1)
print("Placed Weaknesses Data:")
for weakness in placed_weakness:
    print(weakness)

def place_enemy_weaknesses_random(deity_id):
    deity = deity_data[0]
    weakness = deity["weakness"]
    placed_weakness = []
    
    for child in weakness:
        max_attempts = 100
        while max_attempts > 0:
            rotation = random.randint(0, 3)
            matrix = rotate_matrix(child["relative_positions"], rotation)
            positions = []
            for y in range(len(matrix)):
                for x in range(len(matrix[0])):
                    if matrix[y][x] == 1:
                        positions.append((x, y))

            #Random position
            start_row = random.randint(0, MAP_SIZE - 1)
            start_col = random.randint(0, MAP_SIZE - 1)

            is_valid = True
            for x, y in positions:
                row = start_row + y
                col = start_col + x
                if (row >= MAP_SIZE or col >= MAP_SIZE or row < 0 or col < 0 or player_red_matrix[row][col] == 1):
                    is_valid = False
                    break

            if is_valid:
                for x, y in positions:
                    row = start_row + y
                    col = start_col + x
                    player_red_matrix[row][col] = 1
                placed_weakness.append({
                    "weakness_id": child["id"],
                    "start_row": start_row,
                    "start_col": start_col,
                    "relative_positions": matrix,
                    "rotation": rotation
                })
                break
            max_attempts -= 1
    
    return placed_weakness

def is_weakness_destroyed(weakness, matrix):
    start_row = weakness["start_row"]
    start_col = weakness["start_col"]
    relative_positions = weakness["relative_positions"]
    for y in range(len(relative_positions)):
        for x in range(len(relative_positions[0])):
            if relative_positions[y][x] == 1:
                row = start_row + y
                col = start_col + x
                if 0 <= row < MAP_SIZE and 0 <= col < MAP_SIZE:
                    if matrix[row][col] != 2: 
                        return False
    return True

def enemy_attack():
    global enemy_targets
    # If there are existing targets, prioritize them
    if enemy_targets:
        origin = next(iter(enemy_targets))
        target = enemy_targets[origin]
        # Get the next cell to attack from the queue
        row, col = target["queue"].pop(0)

        # Attack the cell
        if player_blue_matrix[row][col] == 1:
            player_blue_matrix[row][col] = 2  # Hit
            # Add new target, with origin is a found cell
            new_queue = []
            # Expand queue with adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = row + dr, col + dc
                if 0 <= r < MAP_SIZE and 0 <= c < MAP_SIZE and player_blue_matrix[r][c] in [0, 1] and (r, c) not in target["queue"]:
                    new_queue.append((r, c))

            # Add new target to enemy_targets
            enemy_targets[(row, col)] = {"queue": new_queue}

        elif player_blue_matrix[row][col] == 0:
            player_blue_matrix[row][col] = 3  # Miss

        # If the target's queue is empty, remove it
        if not target["queue"]:
            del enemy_targets[origin]

        clean_enemy_targets()

    else:
        # No targets, attack randomly
        available_cells = [(r, c) for r in range(MAP_SIZE) for c in range(MAP_SIZE) if player_blue_matrix[r][c] in [0, 1]]
        if available_cells:
            row, col = random.choice(available_cells)

            # Attack the cell
            if player_blue_matrix[row][col] == 1:
                player_blue_matrix[row][col] = 2  # Hit
                # Create a new target
                queue = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r, c = row + dr, col + dc
                    if 0 <= r < MAP_SIZE and 0 <= c < MAP_SIZE and player_blue_matrix[r][c] in [0, 1]:
                        queue.append((r, c))

                # Add new target, with origin is a found cell
                enemy_targets[(row, col)] = {"queue": queue}

            elif player_blue_matrix[row][col] == 0:
                player_blue_matrix[row][col] = 3  # Miss

            clean_enemy_targets()
            print(enemy_targets)
            print("")
            return True
    
    print("")
    print(enemy_targets)

    return False

def clean_enemy_targets():
    global enemy_targets
    surviving_targets = {}
    
    # Collect all cells positions (matrix) of dead weaknesses
    dead_cells = set()

    for weakness in placed_weakness:
        if is_weakness_destroyed(weakness, player_blue_matrix):
            start_row = weakness["start_row"]
            start_col = weakness["start_col"]
            matrix = weakness["relative_positions"]
            for y in range(len(matrix)):
                for x in range(len(matrix[0])):
                    if matrix[y][x] == 1:
                        cell = (start_row + y, start_col + x)
                        dead_cells.add(cell)

    for origin in list(enemy_targets.keys()):
        # If orgin is a cell of dead unit, remove it
        if origin in dead_cells:
            continue
        # If not, keep the target
        surviving_targets[origin] = enemy_targets[origin]

    enemy_targets = surviving_targets

#Draw Map Before Battle (My Map - Blue 75x75)
def draw_my_map(screen_width, screen_height, mouse_clicked, right_mouse_clicked):
    global edit_mode, selected_weakness, temp_matrix, weakness_shape, temp_relative_positions, temp_rotation, temp_image, selected_offset
    # Calculate map position to center it
    map_x = (screen_width - MAP_PIXEL_SIZE) // 2
    map_y = (screen_height - MAP_PIXEL_SIZE) // 2

    # Draw the 10x10 map
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            # Calculate position for each tile, accounting for overlap
            tile_x = map_x + col * EFFECTIVE_TILE_SIZE
            tile_y = map_y + row * EFFECTIVE_TILE_SIZE
            if player_blue_matrix[row][col] == 0:
                screen.blit(Blue75, (tile_x, tile_y))

    # Get current mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()

    drawn_weaknesses = set()
    hovered_weakness = None  # Store the weakness that is being hovered
    hovered_offset = None
    if not edit_mode:
        if map_x <= mouse_x < map_x + MAP_PIXEL_SIZE and map_y <= mouse_y < map_y + MAP_PIXEL_SIZE:
            grid_col = (mouse_x - map_x) // EFFECTIVE_TILE_SIZE
            grid_row = (mouse_y - map_y) // EFFECTIVE_TILE_SIZE
            for weakness in placed_weakness:
                start_row = weakness["start_row"]
                start_col = weakness["start_col"]
                matrix = weakness["relative_positions"]
                rel_row = grid_row - start_row
                rel_col = grid_col - start_col
                if (0 <= rel_row < len(matrix) and 0 <= rel_col < len(matrix[0]) and matrix[rel_row][rel_col] == 1):
                    hovered_weakness = weakness
                    hovered_offset = (rel_row, rel_col)
                    break

    if mouse_clicked:
        if hovered_weakness and not edit_mode:
            # Start edit_mode
            edit_mode = True
            selected_weakness = hovered_weakness
            selected_offset = hovered_offset
            temp_matrix = [row[:] for row in player_blue_matrix]  # Copy the map matrix

            # Remove selected block's position in the temp matrix
            weakness_matrix = selected_weakness["relative_positions"]
            for y in range(len(weakness_matrix)):
                for x in range(len(weakness_matrix[0])):
                    if weakness_matrix[y][x] == 1:
                        temp_row = selected_weakness["start_row"] + y
                        temp_col = selected_weakness["start_col"] + x
                        if (0 <= temp_row < MAP_SIZE and 0 <= temp_col < MAP_SIZE):
                            temp_matrix[temp_row][temp_col] = 0

            weakness_shape = selected_weakness["relative_positions"]
            temp_relative_positions = [row[:] for row in weakness_matrix]  # Deep copy
            temp_rotation = selected_weakness["rotation"]  # Initialize temp_rotation

             # Set temp_image to highlighted image path
            try:
                child = next(c for c in deity_data[0]["weakness"] if c["id"] == selected_weakness["weakness_id"])
                temp_image = child["image"].replace("BT_", "H_BT_")
            except StopIteration:
                temp_image = None

        elif edit_mode and selected_weakness is not None and temp_relative_positions is not None:
            # Check and apply new position
            cursor_row = (mouse_y - map_y) // EFFECTIVE_TILE_SIZE
            cursor_col = (mouse_x - map_x) // EFFECTIVE_TILE_SIZE
            new_start_row = cursor_row - selected_offset[0]
            new_start_col = cursor_col - selected_offset[1]
            is_valid = True
            for y in range(len(temp_relative_positions)):
                for x in range(len(temp_relative_positions[0])):
                    if temp_relative_positions[y][x] == 1:
                        temp_row = new_start_row + y
                        temp_col = new_start_col + x
                        if (temp_row >= MAP_SIZE or temp_col >= MAP_SIZE or temp_row < 0 or temp_col < 0 or temp_matrix[temp_row][temp_col] == 1):
                            is_valid = False
                            break
                        
                if not is_valid:
                    break

            if is_valid:
                # Clear old position in player_blue_matrix
                old_matrix = selected_weakness["relative_positions"]
                for y in range(len(old_matrix)):
                    for x in range(len(old_matrix[0])):
                        if old_matrix[y][x] == 1:
                            old_row = selected_weakness["start_row"] + y
                            old_col = selected_weakness["start_col"] + x
                            if (0 <= old_row < MAP_SIZE and 0 <= old_col < MAP_SIZE):
                                player_blue_matrix[old_row][old_col] = 0

                # Apply new position
                for y in range(len(temp_relative_positions)):
                    for x in range(len(temp_relative_positions[0])):
                        if temp_relative_positions[y][x] == 1:
                            new_row = new_start_row + y
                            new_col = new_start_col + x
                            if 0 <= new_row < MAP_SIZE and 0 <= new_col < MAP_SIZE:
                                player_blue_matrix[new_row][new_col] = 1            

                selected_weakness["start_row"] = new_start_row
                selected_weakness["start_col"] = new_start_col
                selected_weakness["relative_positions"] = [row[:] for row in temp_relative_positions]
                selected_weakness["rotation"] = temp_rotation

            # Stop edit_mode
            edit_mode = False
            selected_weakness = None
            temp_matrix = None
            weakness_shape = None
            temp_relative_positions = None
            temp_rotation = 0
            temp_image = None
    
    # Handle right-click to rotate in edit_mode
    if right_mouse_clicked and edit_mode and selected_weakness is not None and temp_relative_positions is not None:
        old_offset_y, old_offset_x = selected_offset
        old_height = len(temp_relative_positions)
        old_width = len(temp_relative_positions[0])

        temp_relative_positions = edit_rotate(temp_relative_positions)
        weakness_shape = [row[:] for row in temp_relative_positions]  # Sync weakness_shape for display
        temp_rotation = (temp_rotation + 1) % 4  # Update temp rotation

        # Rotate offset
        selected_offset = rotate_offset_90_clockwise((old_offset_y, old_offset_x), old_height, old_width)

    # Stop edit_mode if the cursor get out of the map
    if edit_mode and not (map_x <= mouse_x < map_x + MAP_PIXEL_SIZE and map_y <= mouse_y < map_y + MAP_PIXEL_SIZE):
        edit_mode = False
        selected_weakness = None
        temp_matrix = None
        weakness_shape = None
        temp_relative_positions = None
        temp_rotation = 0
        temp_image = None

    # First pass: Check for hover and draw non-hovered weaknesses
    for weakness in placed_weakness:
        if weakness["weakness_id"] not in drawn_weaknesses:
            if weakness != hovered_weakness:
                try:
                    child = next(c for c in deity_data[0]["weakness"] if c["id"] == weakness["weakness_id"])

                    # Base image path
                    base_image_path = child["image"]
                    weakness_image = pygame.image.load(base_image_path).convert_alpha()

                    # Calculate the bounding box of the weakness based on its rotated matrix
                    matrix = weakness["relative_positions"]

                    # Base starting position
                    start_row = weakness["start_row"]
                    start_col = weakness["start_col"]

                    # Draw at the adjusted starting position
                    tile_x = map_x + start_col * EFFECTIVE_TILE_SIZE
                    tile_y = map_y + start_row * EFFECTIVE_TILE_SIZE

                    # Rotate the image based on rotation (clockwise)
                    rotation_angle = weakness["rotation"] * 90
                    rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)

                    screen.blit(rotated_image, (tile_x, tile_y))
                    drawn_weaknesses.add(weakness["weakness_id"])

                except (pygame.error, StopIteration) as error:
                    print(f"Error: {error}")

    # Second pass: Draw the hovered weakness on top (if any) (outside edit_mode)
    if hovered_weakness and not edit_mode:
        for weakness in placed_weakness:
            if weakness["weakness_id"] not in drawn_weaknesses:
                try:
                    child = next(c for c in deity_data[0]["weakness"] if c["id"] == hovered_weakness["weakness_id"])
                    base_image_path = child["image"]
                    highlighted_image_path = base_image_path.replace("BT_", "H_BT_")
                    weakness_image = pygame.image.load(highlighted_image_path).convert_alpha()
                    rotation_angle = weakness["rotation"] * 90
                    rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
                    tile_x = map_x + hovered_weakness["start_col"] * EFFECTIVE_TILE_SIZE
                    tile_y = map_y + hovered_weakness["start_row"] * EFFECTIVE_TILE_SIZE
                    screen.blit(rotated_image, (tile_x, tile_y))
                    drawn_weaknesses.add(weakness["weakness_id"])

                except (pygame.error, StopIteration) as error:
                    print(f"Error: {error}")

    # Third pass: Draw hovered weakness (inside edit_mode)
    if edit_mode and selected_weakness is not None and temp_image is not None:
        try:
            weakness_image = pygame.image.load(temp_image).convert_alpha()
            rotation_angle = selected_weakness["rotation"] * 90
            rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
            tile_x = map_x + selected_weakness["start_col"] * EFFECTIVE_TILE_SIZE
            tile_y = map_y + selected_weakness["start_row"] * EFFECTIVE_TILE_SIZE
            screen.blit(rotated_image, (tile_x, tile_y))
            drawn_weaknesses.add(selected_weakness["weakness_id"])
        except (pygame.error, StopIteration) as error:
            print(f"Error: {error}")

    # Draw temp blocks in edit_mode
    if edit_mode and map_x <= mouse_x < map_x + MAP_PIXEL_SIZE and map_y <= mouse_y < map_y + MAP_PIXEL_SIZE:
        cursor_row = (mouse_y - map_y) // EFFECTIVE_TILE_SIZE
        cursor_col = (mouse_x - map_x) // EFFECTIVE_TILE_SIZE
        new_start_row = cursor_row - selected_offset[0]
        new_start_col = cursor_col - selected_offset[1]
        is_valid = True
        # Draw Avaiable
        for y in range(len(temp_relative_positions)):
            for x in range(len(temp_relative_positions[0])):
                if temp_relative_positions[y][x] == 1:
                    temp_row = new_start_row + y
                    temp_col = new_start_col + x
                    if (temp_row >= MAP_SIZE or temp_col >= MAP_SIZE or temp_row < 0 or temp_col < 0 or temp_matrix[temp_row][temp_col] == 1):
                        is_valid = False
                        break
            
            if not is_valid:
                break

        # Draw Avaiable for valid positions
        for y in range(len(temp_relative_positions)):
            for x in range(len(temp_relative_positions[0])):
                if temp_relative_positions[y][x] == 1:
                    temp_row = new_start_row + y
                    temp_col = new_start_col + x
                    tile_x = map_x + temp_col * EFFECTIVE_TILE_SIZE
                    tile_y = map_y + temp_row * EFFECTIVE_TILE_SIZE
                    if (0 <= temp_row < MAP_SIZE and 0 <= temp_col < MAP_SIZE and temp_matrix[temp_row][temp_col] == 0):
                        screen.blit(Avaiable, (tile_x, tile_y))

        # Draw Not_Avaiable for invalid positions
        if not is_valid:
            for y in range(len(temp_relative_positions)):
                for x in range(len(temp_relative_positions[0])):
                    if temp_relative_positions[y][x] == 1:
                        temp_row = new_start_row + y
                        temp_col = new_start_col + x
                        tile_x = map_x + temp_col * EFFECTIVE_TILE_SIZE
                        tile_y = map_y + temp_row * EFFECTIVE_TILE_SIZE
                        if 0 <= temp_row < MAP_SIZE and 0 <= temp_col < MAP_SIZE:
                            screen.blit(Not_Avaiable, (tile_x, tile_y))

# Draw Battle Blue Phase (Blue 75x75 map on left, Red 25x25 map on right)
def draw_battle_blue(screen_width, screen_height):
    # Calculate total width of both maps + gap
    total_width = MAP_PIXEL_SIZE + MAP_GAP + SMALL_MAP_PIXEL_SIZE
    # Center the entire block horizontally
    start_x = (screen_width - total_width) // 2
    # Center the blue map vertically
    blue_map_y = (screen_height - MAP_PIXEL_SIZE) // 2
    # Blue map (75x75 tiles) positioned on the left
    blue_map_x = start_x

    # Draw blue map
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = blue_map_x + col * EFFECTIVE_TILE_SIZE
            tile_y = blue_map_y + row * EFFECTIVE_TILE_SIZE
            if player_blue_matrix[row][col] in [0, 1, 2, 3]:
                screen.blit(Blue75, (tile_x, tile_y))

    # Red map (25x25 tiles) positioned 100px to the right of blue map
    red_map_x = blue_map_x + MAP_PIXEL_SIZE + MAP_GAP
    red_map_y = blue_map_y  # Align top of red map with blue map

    # Draw red map (10x10 with 25x25 tiles)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = red_map_x + col * EFFECTIVE_SMALL_TILE_SIZE
            tile_y = red_map_y + row * EFFECTIVE_SMALL_TILE_SIZE
            if player_red_matrix[row][col] in [0, 1, 2, 3]:
                screen.blit(Red25, (tile_x, tile_y))

    # Draw player's weaknesses (75x75)
    drawn_weaknesses = set()
    for weakness in placed_weakness:
        if weakness["weakness_id"] not in drawn_weaknesses:
            try:
                child = next(c for c in deity_data[0]["weakness"] if c["id"] == weakness["weakness_id"])
                weakness_image = pygame.image.load(child["image"]).convert_alpha()
                rotation_angle = weakness["rotation"] * 90
                rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
                tile_x = blue_map_x + weakness["start_col"] * EFFECTIVE_TILE_SIZE
                tile_y = blue_map_y + weakness["start_row"] * EFFECTIVE_TILE_SIZE
                screen.blit(rotated_image, (tile_x, tile_y))
                drawn_weaknesses.add(weakness["weakness_id"])
            except (pygame.error, StopIteration) as error:
                print(f"Error: {error}")

    # Draw weaknesses on red map (25x25, enemy, only if destroyed)
    drawn_weaknesses = set()
    for weakness in enemy_weakness:    
        if weakness["weakness_id"] not in drawn_weaknesses and is_weakness_destroyed(weakness, player_red_matrix):
            try:
                child = next(c for c in deity_data[0]["weakness"] if c["id"] == weakness["weakness_id"])
                small_image = child["image"].replace("BT_", "S_RT_")
                weakness_image = pygame.image.load(small_image).convert_alpha()
                rotation_angle = weakness["rotation"] * 90
                rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
                tile_x = red_map_x + weakness["start_col"] * EFFECTIVE_SMALL_TILE_SIZE
                tile_y = red_map_y + weakness["start_row"] * EFFECTIVE_SMALL_TILE_SIZE
                screen.blit(rotated_image, (tile_x, tile_y))
                drawn_weaknesses.add(weakness["weakness_id"])
            except (pygame.error, StopIteration) as error:
                print(f"Error: {error}")

    # Draw Found/Missed on blue map (75x75)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = blue_map_x + col * EFFECTIVE_TILE_SIZE
            tile_y = blue_map_y + row * EFFECTIVE_TILE_SIZE
            if player_blue_matrix[row][col] == 2:
                screen.blit(Found75, (tile_x, tile_y))
            elif player_blue_matrix[row][col] == 3:
                screen.blit(Missed75, (tile_x, tile_y))

    # Draw Found/Missed on red map (25x25)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = red_map_x + col * EFFECTIVE_SMALL_TILE_SIZE
            tile_y = red_map_y + row * EFFECTIVE_SMALL_TILE_SIZE
            # Do not draw Found for dead weaknesses
            is_destroyed = False
            for weakness in enemy_weakness:
                start_row = weakness["start_row"]
                start_col = weakness["start_col"]
                rel_y = row - start_row
                rel_x = col - start_col
                matrix = weakness["relative_positions"]
                if (0 <= rel_y < len(matrix) and 0 <= rel_x < len(matrix[0]) and 
                    matrix[rel_y][rel_x] == 1 and is_weakness_destroyed(weakness, player_red_matrix)):
                    is_destroyed = True
                    break

            if not is_destroyed:
                if player_red_matrix[row][col] == 2:
                    screen.blit(Found25, (tile_x, tile_y))
                elif player_red_matrix[row][col] == 3:
                    screen.blit(Missed25, (tile_x, tile_y))

    screen.blit(test, (((((screen_width - total_width) // 2) - test.get_width()) // 2), 0))
    screen.blit(test_2, ((screen_width - (((screen_width - total_width) // 2) + test_2.get_width()) // 2), 0))

# Draw Battle Red Phase (Blue 25x25 map on left, Red 75x75 map on right)
def draw_battle_red(screen_width, screen_height):
    # Calculate total width of both maps + gap
    total_width = SMALL_MAP_PIXEL_SIZE + MAP_GAP + MAP_PIXEL_SIZE
    # Center the entire block
    start_x = (screen_width - total_width) // 2
    red_map_y = (screen_height - MAP_PIXEL_SIZE) // 2

    # Blue map (25x25 tiles) positioned on the left
    blue_map_x = start_x
    blue_map_y = red_map_y

    # Draw blue map (10x10 with 25x25 tiles)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = blue_map_x + col * EFFECTIVE_SMALL_TILE_SIZE
            tile_y = blue_map_y + row * EFFECTIVE_SMALL_TILE_SIZE
            if player_red_matrix[row][col] in [0, 1, 2, 3]:
                screen.blit(Blue25, (tile_x, tile_y))

    # Red map (75x75 tiles) positioned right of blue map
    red_map_x = blue_map_x + SMALL_MAP_PIXEL_SIZE + MAP_GAP

    # Draw red map (10x10 with 75x75 tiles)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = red_map_x + col * EFFECTIVE_TILE_SIZE
            tile_y = red_map_y + row * EFFECTIVE_TILE_SIZE
            if player_blue_matrix[row][col] in [0, 1, 2, 3]:
                screen.blit(Red75, (tile_x, tile_y))

    # Draw weaknesses on blue map (25x25, player's side)
    drawn_weaknesses = set()
    for weakness in placed_weakness:
        if weakness["weakness_id"] not in drawn_weaknesses:
            try:
                child = next(c for c in deity_data[0]["weakness"] if c["id"] == weakness["weakness_id"])
                small_image = child["image"].replace("BT_", "S_BT_")
                weakness_image = pygame.image.load(small_image).convert_alpha()
                rotation_angle = weakness["rotation"] * 90
                rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
                tile_x = blue_map_x + weakness["start_col"] * EFFECTIVE_SMALL_TILE_SIZE
                tile_y = blue_map_y + weakness["start_row"] * EFFECTIVE_SMALL_TILE_SIZE
                screen.blit(rotated_image, (tile_x, tile_y))
                drawn_weaknesses.add(weakness["weakness_id"])
            except (pygame.error, StopIteration) as error:
                print(f"Error: {error}")

    # Draw weaknesses on red map (75x75, enemy, only if destroyed)
    drawn_weaknesses = set()
    for weakness in enemy_weakness:
        if weakness["weakness_id"] not in drawn_weaknesses and is_weakness_destroyed(weakness, player_red_matrix):
            try:
                child = next(c for c in deity_data[0]["weakness"] if c["id"] == weakness["weakness_id"])
                enemy_image = child["image"].replace("BT_", "RT_")
                weakness_image = pygame.image.load(enemy_image).convert_alpha()
                rotation_angle = weakness["rotation"] * 90
                rotated_image = pygame.transform.rotate(weakness_image, -rotation_angle)
                tile_x = red_map_x + weakness["start_col"] * EFFECTIVE_TILE_SIZE
                tile_y = red_map_y + weakness["start_row"] * EFFECTIVE_TILE_SIZE
                screen.blit(rotated_image, (tile_x, tile_y))
                drawn_weaknesses.add(weakness["weakness_id"])
            except (pygame.error, StopIteration) as error:
                print(f"Error: {error}")

    # Draw Found/Missed on blue map (25x25)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = blue_map_x + col * EFFECTIVE_SMALL_TILE_SIZE
            tile_y = blue_map_y + row * EFFECTIVE_SMALL_TILE_SIZE
            if player_blue_matrix[row][col] == 2:
                screen.blit(Found25, (tile_x, tile_y))
            elif player_blue_matrix[row][col] == 3:
                screen.blit(Missed25, (tile_x, tile_y))

    # Draw Found/Missed on red map (75x75)
    for row in range(MAP_SIZE):
        for col in range(MAP_SIZE):
            tile_x = red_map_x + col * EFFECTIVE_TILE_SIZE
            tile_y = red_map_y + row * EFFECTIVE_TILE_SIZE

            # Do not draw Found for dead weaknesses
            is_destroyed = False
            for weakness in enemy_weakness:
                start_row = weakness["start_row"]
                start_col = weakness["start_col"]
                rel_y = row - start_row
                rel_x = col - start_col
                matrix = weakness["relative_positions"]
                if (0 <= rel_y < len(matrix) and 0 <= rel_x < len(matrix[0]) and 
                    matrix[rel_y][rel_x] == 1 and is_weakness_destroyed(weakness, player_red_matrix)):
                    is_destroyed = True
                    break
            if not is_destroyed:
                if player_red_matrix[row][col] == 2:
                    screen.blit(Found75, (tile_x, tile_y))
                elif player_red_matrix[row][col] == 3:
                    screen.blit(Missed75, (tile_x, tile_y))

    screen.blit(test, (((((screen_width - total_width) // 2) - test.get_width()) // 2), 0))
    screen.blit(test_2, ((screen_width - (((screen_width - total_width) // 2) + test_2.get_width()) // 2), 0))

def check_game_over():
    global game_over, winner, game_over_time
    # Check player's weaknesses
    player_alive = False
    for weakness in placed_weakness:
        if not is_weakness_destroyed(weakness, player_blue_matrix):
            player_alive = True
            break

    # Check enemy's weaknesses
    enemy_alive = False
    for weakness in enemy_weakness:
        if not is_weakness_destroyed(weakness, player_red_matrix):
            enemy_alive = True
            break

    # Determine the result
    if not player_alive:
        game_over = True
        winner = "enemy"
        game_over_time = pygame.time.get_ticks()
    elif not enemy_alive:
        game_over = True
        winner = "player"
        game_over_time = pygame.time.get_ticks()

def reset_game():
    global player_blue_matrix, player_red_matrix, placed_weakness, enemy_weakness, phase, game_over, winner, waiting_for_turn, last_shot_time, think, start_thinking, thinking_time, enemy_targets
    # Reset matrix
    player_blue_matrix = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    player_red_matrix = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

    # Reset weaknesses
    placed_weakness = place_weaknesses_random(1)
    enemy_weakness = []

    # Reset states
    phase = "Ready"
    game_over = False
    winner = None
    waiting_for_turn = False
    last_shot_time = 0
    think = True
    start_thinking = 0
    thinking_time = 0
    enemy_targets = {}

running = True
while running:
    mouse_clicked = False
    right_mouse_clicked = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            if not is_fullscreen:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if phase == "Ready":
                    enemy_weakness = place_enemy_weaknesses_random(1)
                    print("Enemy Weakness Data:")
                    for weakness in enemy_weakness:
                        print(weakness)
                    phase = "Battle_Blue"
                    waiting_for_turn = False
                    last_shot_time = 0
                elif game_over:
                    reset_game()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left mouse
            mouse_clicked = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and edit_mode: # Right mouse
            right_mouse_clicked = True

    #Current window size
    screen_width, screen_height = screen.get_size()
    screen.fill((0, 0, 0))
    current_time = pygame.time.get_ticks()
    
    if game_over:
        # Vẽ màn hình hiện tại
        if phase == "Battle_Blue":
            draw_battle_blue(screen_width, screen_height)
        elif phase == "Battle_Red":
            draw_battle_red(screen_width, screen_height)

        # Show ending notification
        if current_time - game_over_time >= 1500:
            # Calculate ending frame
            if phase == "Battle_Blue":
                total_width = MAP_PIXEL_SIZE + MAP_GAP + SMALL_MAP_PIXEL_SIZE
                frame_left_x = screen_width - ((screen_width - total_width) // 2) - SMALL_MAP_PIXEL_SIZE - MAP_GAP
                frame_right_x = screen_width
                frame_top_y = SMALL_MAP_PIXEL_SIZE + ((screen_height - MAP_PIXEL_SIZE) // 2)
                frame_bottom_y = screen_height - ((screen_height - MAP_PIXEL_SIZE) // 2)

            else:  # Battle_Red
                total_width = MAP_PIXEL_SIZE + MAP_GAP + SMALL_MAP_PIXEL_SIZE
                frame_left_x = 0
                frame_right_x = screen_width - ((screen_width - total_width) // 2) - MAP_PIXEL_SIZE
                frame_top_y = SMALL_MAP_PIXEL_SIZE + ((screen_height - MAP_PIXEL_SIZE) // 2)
                frame_bottom_y = screen_height - ((screen_height - MAP_PIXEL_SIZE) // 2)

            # Calculate frame center
            frame_center_x = (frame_left_x + frame_right_x) // 2
            frame_center_y = (frame_top_y + frame_bottom_y) // 2

            # Display ending notification
            if winner == "player":
                text = font_large.render("You won!", True, (0, 105, 148))
            else:
                text = font_large.render("You Lost!", True, (255, 0, 0))
            text_rect = text.get_rect(center=(frame_center_x, frame_center_y))
            screen.blit(text, text_rect)
            
            prompt = font_small.render("Press Space to play again", True, (255, 255, 255))
            prompt_rect = prompt.get_rect(center=(frame_center_x, frame_center_y + 60))
            screen.blit(prompt, prompt_rect)
    
    else:
        if phase == "Ready":
            draw_my_map(screen_width, screen_height, mouse_clicked, right_mouse_clicked)
        elif phase == "Battle_Blue":
            draw_battle_blue(screen_width, screen_height)
            if not waiting_for_turn:
                if think:
                    thinking_time = random.randint(750, 1500)
                    start_thinking = pygame.time.get_ticks()
                    think = False
                elif current_time - start_thinking >= thinking_time and not think:
                    enemy_attack()
                    waiting_for_turn = True
                    last_shot_time = current_time
                    check_game_over()

            if waiting_for_turn and current_time - last_shot_time >= 1500:
                phase = "Battle_Red"
                waiting_for_turn = False

        elif phase == "Battle_Red":
            draw_battle_red(screen_width, screen_height)
            if not waiting_for_turn and mouse_clicked:
                total_width = SMALL_MAP_PIXEL_SIZE + MAP_GAP + MAP_PIXEL_SIZE
                start_x = (screen_width - total_width) // 2
                red_map_x = start_x + SMALL_MAP_PIXEL_SIZE + MAP_GAP
                red_map_y = (screen_height - MAP_PIXEL_SIZE) // 2
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if (red_map_x <= mouse_x < red_map_x + MAP_PIXEL_SIZE and red_map_y <= mouse_y < red_map_y + MAP_PIXEL_SIZE):
                    col = (mouse_x - red_map_x) // EFFECTIVE_TILE_SIZE
                    row = (mouse_y - red_map_y) // EFFECTIVE_TILE_SIZE
                    if 0 <= row < MAP_SIZE and 0 <= col < MAP_SIZE:
                        if player_red_matrix[row][col] in [0, 1]:
                            if player_red_matrix[row][col] == 1:
                                player_red_matrix[row][col] = 2
                            else:
                                player_red_matrix[row][col] = 3
                            waiting_for_turn = True
                            last_shot_time = current_time
                            check_game_over()

            if waiting_for_turn and current_time - last_shot_time >= 1500:
                phase = "Battle_Blue"
                waiting_for_turn = False
                think = True
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

    