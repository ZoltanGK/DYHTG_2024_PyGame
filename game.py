import pygame
import pygame_menu as pm
import random as rand
import winsound
import os
import sys
from enum import Enum
from numpy import zeros, int8, sin
from math import e, pi, sqrt, log

# Idea: Game where you hold a button down for a given amount of time
# Add modifiers:
#   Select possible values [square roots and famous numbers; integers]
#   Enable/Disable visual aids?
#   Get as close as possible?
WIDTH = 1280
HEIGHT = 720
FPS = 60

SCORE_OUT_OF = 5000

FAMOUS_NUMBERS = {
    "e": {"full_name": "Euler's number", "value": e},
    "π": {"full_name": "Pi", "value": pi},
    "φ": {"full_name": "the golden ratio", "value": (sqrt(5) + 1) / 2},
    "g": {"full_name": "the standard acceleration of gravity", "value": 9.80665},
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
    ("Random Float", "Random Float"),
]

NUMBER_POOLS = {
    "Integers": lambda: rand.randint(1, 10),
    "Square Roots": lambda: rand.randint(1, 100),
    "Cube Roots": lambda: rand.randint(1, 1000),
    "Base-2 Logarithm": lambda: rand.randint(1, 9),
    "Famous Constants": lambda: list(FAMOUS_NUMBERS.keys()),
    "Random Float": lambda: rand.uniform(1, 10),
}


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def main():
    pygame.init()
    pygame.mixer.pre_init(channels=2, size=-8)
    game_font = pygame.font.Font(None, 32)
    num_to_show = 4
    num_shown = 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    timer = pygame.time.Clock()
    running = True
    curr_state = GameState.INTRO
    prev_state = GameState.INTRO
    frame_counter = 1
    number_chosen = None
    indiv_score = 0
    total_score = 0
    doing_action = False
    restart = False
    number_option_choice = "Integers"

    settings = {
        "Show Exact Time in Seconds": False,
        "Show Exact Time in Frames": False,
        "Visual Aid Circle": False,
        "Play Audio Aid": False,
    }

    def update_state(new_state):
        nonlocal prev_state, curr_state, doing_action
        prev_state = curr_state
        curr_state = new_state
        doing_action = False

    def change_setting(option, val):
        nonlocal settings
        settings[option] = val

    def update_num_to_show(val):
        nonlocal num_to_show
        num_to_show = round(val)

    def select_number_option(choice):
        nonlocal number_option_choice
        number_option_choice = choice

    def settings_loop(screen):

        settings_menu = pm.Menu(
            title="Customisation",
            width=WIDTH,
            height=HEIGHT,
            theme=pm.themes.THEME_DARK,
        )

        def start_game():
            update_state(GameState.NUMBER_SHOW)
            settings_menu.disable()

        for option in settings:
            settings_menu.add.toggle_switch(
                title=option,
                default=settings[option],
                onchange=lambda val, opt=option: change_setting(opt, val),
            )

        settings_menu.add.dropselect(
            "Number Pool",
            items=NUMBER_OPTIONS,
            default=0,
            onchange=lambda selection_tuple, value: select_number_option(
                selection_tuple[0][0]
            ),
        )

        settings_menu.add.range_slider(
            "Amount of Numbers to Estimate",
            range_values=(1, 4),
            increment=1,
            default=num_to_show,
            value_format=lambda x: str(round(x)),
            onchange=update_num_to_show,
        )

        settings_menu.add.button("Start", start_game)
        settings_menu.mainloop(screen)

    while running:
        text_list = []
        other_drawables = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                doing_action = False
                running = False
            elif event.type == pygame.KEYDOWN:
                doing_action = True
            elif event.type == pygame.KEYUP:
                doing_action = False
        if (
            num_to_show <= num_shown
            and curr_state == GameState.NUMBER_RESULT
            and doing_action
        ):
            update_state(GameState.GAME_END)
        if curr_state == GameState.INTRO:
            text_list = [
                "You will be playing a timing game",
                "Your goal will be to hold down any key for as long as a given number",
                "Press any key to start customisation",
                "Pressing Escape will exit except in the customisation menu",
            ]
            if doing_action:
                update_state(GameState.SETTINGS)
        elif curr_state == GameState.SETTINGS:
            settings_loop(screen)
        elif curr_state == GameState.NUMBER_SHOW:
            if (
                prev_state == GameState.NUMBER_RESULT
                or prev_state == GameState.SETTINGS
            ):
                number_chosen = NUMBER_POOLS[number_option_choice]()
                if number_option_choice == "Famous Constants":
                    number_chosen = number_chosen[num_shown]
                    number_val = FAMOUS_NUMBERS[number_chosen]["value"]
                    number_text = f"{number_chosen} ({FAMOUS_NUMBERS[number_chosen]['full_name']})"
                elif number_option_choice == "Square Roots":
                    number_val = sqrt(number_chosen)
                    number_text = f"the square root of {number_chosen}"
                elif number_option_choice == "Cube Roots":
                    number_val = number_chosen ** (1 / 3)
                    number_text = f"the cube root of {number_chosen}"
                elif number_option_choice == "Base-2 Logarithm":
                    # Some silly maths to make it so it's not a 50% chance of getting a target time between 9 and 10
                    number_chosen = rand.randint(
                        2**number_chosen, 2 ** (number_chosen + 1)
                    )
                    number_val = log(number_chosen, 2)
                    number_text = f"log2 of {number_chosen}"
                else:
                    number_val = round(number_chosen, 3)
                    number_text = f"{number_val}"
                number_val = round(number_val, 3)
                target = int(number_val * 60)
                num_shown += 1
                update_state(curr_state)
            text_list.append(f"You need to hold any key for {number_text} seconds")
            if settings["Show Exact Time in Seconds"]:
                text_list.append(
                    f"(Exactly: {number_val} seconds [rounded to {target/60:.3f}])"
                )
            if settings["Show Exact Time in Frames"]:
                text_list.append(f"({target} frames)")
            text_list.append(
                "The timer will start as soon as you start pressing any key"
            )
            if settings["Visual Aid Circle"]:
                text_list.append(
                    "You will see a circle fade in and out over a total period of 2 seconds"
                )
            if settings["Play Audio Aid"]:
                text_list.append("You will hear a tone that moves up and down an octave over a period of 2 seconds")
            if doing_action:
                curr_state = GameState.NUMBER_ESTIMATE
        elif curr_state == GameState.NUMBER_ESTIMATE:
            text_list.append("Let go if you think the right time has passed")
            text_list.append(f"Target: {number_text}")
            if settings["Play Audio Aid"] or settings["Visual Aid Circle"]:
                t_in_half_period = frame_counter % FPS
                # below might be off by one, idk
                # if in second half of the 2 second period
                if (frame_counter % (FPS * 2)) > FPS:
                    t_in_half_period = FPS - t_in_half_period
            if settings["Visual Aid Circle"]:
                # now convert this to a value out of 255
                # round() and int() should lead to similar results, I think
                # it's not meant to be a perfect aid anyway
                alpha = round((t_in_half_period / FPS) * 255)
                other_drawables.append(
                    (
                        pygame.draw.circle,
                        [
                            screen,
                            (alpha, alpha, alpha),
                            vec_sub(screen.get_rect().center, (0, -1 * WIDTH / 8)),
                            WIDTH / 16,
                        ],
                    )
                )
            if settings["Play Audio Aid"] and (
                frame_counter == 1 or (frame_counter % FPS) % 8 == 0
            ):
                # Left as backup
                # # Frequency doubling is fine
                # base_frequency = 440
                # frequency = int(base_frequency * 2 ** (t_in_half_period / FPS))
                # # So winsound actually blocks execution until the sound plays I believe
                # # which is lovely and very helpful
                # winsound.Beep(frequency, int(1000 / FPS / 2))

                # thanks to https://stackoverflow.com/questions/7816294/simple-pygame-audio-at-a-frequency
                # for help with figuring out this sndarray stuff
                n_samples = int(round(pygame.mixer.get_init()[0] / FPS * 8))
                bits = zeros((n_samples, 2), dtype=int8)
                max_sample = 2**7 - 1
                max_sample /= 2
                base_frequency = 440
                frequency = int(base_frequency * 2 ** (t_in_half_period / FPS))
                for s in range(n_samples):
                    t = s / pygame.mixer.get_init()[0]

                    bits[s][0] = int(round(max_sample * sin(2 * pi * frequency * t)))
                    bits[s][1] = int(round(max_sample * sin(2 * pi * frequency * t)))
                beep = pygame.sndarray.make_sound(bits)
                beep.play()
            if doing_action:
                frame_counter += 1
            else:
                print(frame_counter, target)
                indiv_score = -1 * abs((target - frame_counter) / target) + 1
                indiv_score = round(indiv_score * SCORE_OUT_OF)
                total_score += indiv_score
                update_state(GameState.NUMBER_RESULT)
        elif curr_state == GameState.NUMBER_RESULT:
            text_list.append(
                f"You scored {indiv_score} out of a possible {SCORE_OUT_OF}"
            )
            text_list.append(
                f"You held the button for {frame_counter / 60:.3f} seconds"
            )
            text_list.append(f"Your target was {target / 60:.3f} seconds")
            text_list.append("Press any key to continue")
            if doing_action:
                update_state(GameState.NUMBER_SHOW)
                frame_counter = 1
                indiv_score = 0
        elif curr_state == GameState.GAME_END:
            text_list.append(
                f"You achieved a total score of {total_score} from a maximum of {num_to_show * SCORE_OUT_OF}"
            )
            text_list.append("Press any key to restart")
            if doing_action:
                running = False
                restart = True
        else:
            # Ruh roh, Raggy
            text_list.append("ERROR: Unknown Game State")
            text_list.append("Please report to dev")
            text_list.append("Your only option now is to close the window")

        screen.fill("black")
        for i in range(len(text_list)):
            offset = (i - len(text_list) / 2 - (len(text_list) % 2)) * 48
            text = text_list[i]
            text_surf = game_font.render(text, True, "white")
            text_rect = text_surf.get_rect(
                center=vec_sub(screen.get_rect().center, (0, -offset))
            )
            screen.blit(text_surf, text_rect)
        for i in other_drawables:
            i[0](*i[1])

        pygame.display.flip()
        timer.tick(FPS)
    pygame.quit()
    if restart:
        # Awful way to do this, but hey, it works!
        os.startfile(__file__)
        sys.exit()


if __name__ == "__main__":
    main()
