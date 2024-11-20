import asyncio
import os
from game.game_manager import GameManager

# 코드 시작 부분에 API 키 설정
os.environ["OPENAI_API_KEY"] = "sk-proj-67890123456789012345678901234567"

async def main():
    print("\n=== 게임 시작 ===")
    # 게임 설정
    player_count = 6
    print(f"플레이어 수: {player_count}")
    game = GameManager(player_count)
    
    # 게임 실행
    print("\n=== 게임 진행 시작 ===")
    await game.run_game()
    
    # 게임 결과 출력
    winner = "마피아" if game.is_mafia_win() else "시민"
    print(f"\n=== 게임 종료 ===")
    print(f"승리: {winner} 팀")

if __name__ == "__main__":
    asyncio.run(main()) 