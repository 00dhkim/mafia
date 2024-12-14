import asyncio
from src.game.game_manager import GameManager

async def main():
    game = GameManager()
    game.initialize_game()
    await game.run_game()

if __name__ == "__main__":
    asyncio.run(main()) 