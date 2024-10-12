import pygame
import pygame_menu as pm
import random as rand
from enum import Enum
from math import e, pi, sqrt, log

# Idea: Game where you hold a button down for a given amount of time
# Add modifiers:
#   Select possible values [square roots and famous numbers; integers]
#   Enable/Disable visual aids?
#   Get as close as possible? 

FAMOUS_NUMBERS = {
    "e" : { "full_name": "Euler's number",
           "value": e
    },
    "π" : { "full_name": "Pi",
           "value": pi},
    "φ" : {"full_name": "the golden ratio",
           "value": (sqrt(5) + 1) / 2},
    "g" : {"full_name": "the standard acceleration of gravity",
           "value": 9.80665}
}

class GameState(Enum):
    INTRO = 0
    NUMBER_SHOW = 1
    NUMBER_ESTIMATE = 2
    NUMBER_RESULT = 3
    SETTINGS = 4
    GAME_END = 5

NUMBER_OPTIONS = [
    ("Integers", "Integers"),
    ("Square Roots", "Square Roots"),
    ("Cube Roots", "Cube Roots"),
    ("Base-2 Logarithm", "Base-2 Logarithm"),
    ("Famous Constants", "Famous Constants"),
    ("Random Float", "Random Float")
]

NUMBER_POOLS = {
    "Integers" : lambda : rand.randint(1,10),
    "Square Roots" : lambda : rand.randint(1,100),
    "Cube Roots" : lambda : rand.randint(1,1000),
    "Base-2 Logarithm": lambda : rand.randint(2,1024),
    "Famous Constants": lambda : rand.choice(FAMOUS_NUMBERS),
    "Random Float": lambda : rand.uniform(1,10)
}

pygame.init()

WIDTH = 1280
HEIGHT = 720
FPS = 60
GAME_FONT = pygame.font.Font(None, 32)

def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def main():
    num_to_show = 3
    num_shown = 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    timer = pygame.time.Clock()
    running = True
    curr_state = GameState.INTRO
    prev_state = GameState.INTRO
    frame_counter =  1
    number_chosen = None
    indiv_score = 0
    total_score = 0
    doing_action = False
    number_option_choice = "Integers"

    settings = {
        "Show Exact Time in Seconds": False,
        "Show Exact Time in Frames": False
    } 

    def start_game():
        nonlocal curr_state
        curr_state = GameState.NUMBER_SHOW

    def change_setting(option, val):
            settings[option] = val
            pygame.event.post(pm.events.CLOSE)
    
    def select_number_option(choice):
        nonlocal number_option_choice
        number_option_choice = choice

    def settings_loop(screen):
        settings_menu = pm.Menu(title="Customisation",
                                width=WIDTH,
                                height=HEIGHT,
                                theme = pm.themes.THEME_BLACK)
        
        for option in settings:
            settings_menu.add.toggle_switch(title = option,
                                            default=settings[option],
                                            onchange=lambda val, opt=option: change_setting(opt, val))
            
        settings_menu.add.dropselect("Number Pool",
                                    items=NUMBER_OPTIONS, 
                                    default=0,
                                    onchange=lambda selection_tuple, 
                                    value: select_number_option(selection_tuple[0]))

        settings_menu.add.range_slider("Amount of Numbers to Estimate",
                                    range_values=(1,3),
                                    increment=1,
                                    value_format=lambda x : round(x))

        settings_menu.add.button("Start", start_game)
        settings_menu.mainloop(screen)

    while running:
        text_list = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                doing_action = False
                running = False
            elif event.type == pygame.KEYDOWN:
                doing_action = True
            elif event.type == pygame.KEYUP:
                doing_action = False
        while doing_action and not (curr_state == GameState.NUMBER_ESTIMATE or curr_state == GameState.SETTINGS):
            continue
        if num_to_show <= num_shown and GameState.NUMBER_RESULT:
            curr_state = GameState.GAME_END
        if curr_state == GameState.INTRO:
            text_list = ["You will be playing a customisable timing game",
                            "Your goal will be to hold down the Enter key for as long as a given number",
                            "Press Enter to start customisation"]
            if doing_action:
                curr_state = GameState.SETTINGS
        elif curr_state == GameState.SETTINGS:
                settings_loop(screen)
                curr_state = GameState.NUMBER_SHOW
        elif curr_state == GameState.NUMBER_SHOW:
            if prev_state == GameState.NUMBER_RESULT or prev_state == GameState.SETTINGS:
                number_chosen = NUMBER_POOLS[number_option_choice]
                if number_option_choice == "Famous Constants":
                    number_val = FAMOUS_NUMBERS[number_chosen]["value"]
                    number_text = f"{number_chosen} ({FAMOUS_NUMBERS[number_chosen]['full_name']})"
                elif number_option_choice == "Square Roots":
                    number_val = sqrt(number_chosen)
                    number_text = f"the square root of {number_chosen}"
                elif number_option_choice == "Cube Roots":
                    number_val = number_chosen**(1/3)
                    number_text = f"the cube root of {number_chosen}"
                elif number_option_choice == "Base-2 Logarithm":
                    number_val = log(number_chosen, 2)
                    number_text = f"log2 of {number_chosen}"
                else:
                    number_val = round(number_chosen,3)
                    number_text = f"{number_val}"
                number_val = round(number_val, 3)
                target = int(number_val*60)
                num_shown += 1      
            text_list = [f"You need to hold the Enter key for {number_text} {'seconds' if not settings['Show Time in Frames'] else 'frames'}"]
            if settings["Show Exact Time in Seconds"]:
                text_list.append(f"(Exactly: {number_val} seconds)")
            if settings["Show Exact Time in Frames"]:
                text_list.append(f"({target} frames)")
            text_list.append("The timer will start as soon as you start pressing the Enter key")
        elif curr_state == GameState.NUMBER_ESTIMATE:
            text_list.append("Let go if you think the right time has passed")
            if doing_action:
                frame_counter += 1
            else:
                indiv_score = round(abs(1 - frame_counter / target) * 100, 1) * 10
                total_score += indiv_score
                frame_counter = 1
                curr_state = GameState.NUMBER_RESULT
        elif curr_state == GameState.NUMBER_RESULT:
            text_list.append(f"You scored {indiv_score} out of a possible 1000")
            text_list.append("Press Enter to continue")
            if doing_action:
                curr_state = GameState.NUMBER_SHOW
                indiv_score = 0
        elif curr_state == GameState.GAME_END:
            text_list.append(f"You achieved a total score of {total_score} from a maximum of {num_to_show * 1000}")
        else:
            # Ruh roh, Raggy
            text_list.append("ERROR: Unknown Game State")
            text_list.append("Please report to dev")
            text_list.append("Your only option now is to close the window")

        screen.fill("black")
        for i in range(len(text_list)):
            offset = round(i - len(text_list)/2) * 48
            text = text_list[i]
            text_surf = GAME_FONT.render(text, True, "white")
            text_rect = text_surf.get_rect(center = vec_sub(screen.get_rect().center,(0, offset)))
            screen.blit(text_surf, text_rect)

        pygame.display.flip()

        timer.tick(FPS)

if __name__ == "__main__":
    main()

pygame.quit()