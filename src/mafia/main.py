from dotenv import load_dotenv
from src.game.game_manager import GameManager

def main():
    load_dotenv()

    game = GameManager()
    game.initialize_game()
    game.spin()

if __name__ == "__main__":
    main() 