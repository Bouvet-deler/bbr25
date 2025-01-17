from pprint import pp
import json
import time
import bbr_api, bbr_types

api = bbr_api.Api()


class Gameplay():
    def play(self):
        while True:
            game_state = api.get_game_state()

            if game_state.currentState == 'Registering':
                pp(game_state)
                if input("Start game? [y/N] ").strip() == 'y':
                    api.start_game()
                continue

            if game_state.currentState != 'Playing':
                print("Unhandled state", game_state.currentState)
                pp(game_state)
                exit(1)

            if game_state.currentPlayer != api.player_name:
                print("Wait for", game_state.currentPlayer)
                time.sleep(1)
                continue

            if game_state.currentPhase == 'Planting':
                pp(game_state)
                print("You're ready to plant! Good luck!")
                exit(0)
            else:
                print("Unhandled phase", game_state.currentPhase)
                pp(game_state)
                exit(1)

Gameplay().play()
