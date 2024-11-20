# 마피아 게임 프로젝트

## 프로젝트 구조

## 주요 컴포넌트 설명

### 1. 게임 관리 (game_manager.py)
- 게임의 전체적인 흐름 제어
- 낮/밤 페이즈 관리
- 플레이어 역할 분배
- 투표 시스템 구현

### 2. 플레이어 시스템 (player.py)
- 플레이어 기본 정보 관리
- AI 응답 생성 기능
- 역할별 행동 구현

### 3. 역할 시스템 (role.py)
- 게임 내 역할 정의 (마피아, 의사, 경찰, 시민)
- 각 역할별 설명 및 능력 정의

### 4. 채팅 시스템 (chat_system.py)
- 공개 채팅
- 마피아 채팅
- 사망자 채팅
- 채팅 기록 관리

### 5. 프롬프트 관리 (prompt_manager.py)
- AI 응답 생성을 위한 프롬프트 템플릿 관리
- 상황별 맞춤 프롬프트 생성

## 실행 방법

1. 필요한 패키지 설치:
```
bash
pip install openai
```

2. OpenAI API 키 설정:
- main.py 파일에서 OPENAI_API_KEY 환경변수 설정

3. 게임 실행:
```
bash
python main.py
```

## 게임 규칙

1. 최소 4명의 플레이어 필요
2. 역할 분배:
   - 마피아: 플레이어 수의 1/4 (최소 1명)
   - 의사: 1명
   - 경찰: 1명
   - 나머지: 시민

3. 게임 진행:
   - 낮: 토론 및 투표
   - 밤: 직업별 특수 능력 사용

4. 승리 조건:
   - 시민팀: 모든 마피아 제거
   - 마피아팀: 마피아 수가 시민 수 이상이 되는 경우

## 주의사항
- OpenAI API 키가 필요합니다
- Python 3.7 이상 버전이 필요합니다
- 비동기 처리를 위해 asyncio를 사용합니다

## 구현 예정

- 마피아 공격
- 최후의 변론 및 최종 투표
- 의사 능력 파싱 오류
- 죽은 사람에게 투표 X
- 투표로 죽은 이를 LLM이 인지하지 못함
- 마피아가 생각으로 말할 내용을 토론으로 말해버림. 지금 대화의 맥락(자유토론, 마피아 토론 등)을 넣어주자
- LLM 입출력 기록