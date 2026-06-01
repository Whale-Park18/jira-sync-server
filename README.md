# jira-sync-server

[jira-sync](https://github.com/Whale-Park18/jira-sync) CLI를 웹 버튼 하나로 실행할 수 있는 트리거 서버입니다.

## 동작 방식

```
브라우저 → 동기화 버튼 클릭
    → POST /api/sync
        → sync --config /config/sync_config.yaml (subprocess)
            → Jira → Notion 동기화
```

jira-sync는 Docker 이미지 빌드 시 `pip install git+...`으로 설치됩니다.  
자격증명(`.env`)과 설정(`sync_config.yaml`)은 jira-sync 디렉토리를 볼륨 마운트해서 주입합니다.

### 자격증명 흐름

```
jira-sync/.env (볼륨 마운트 → /config/.env)
    → runner.py에서 dotenv_values()로 읽기
    → subprocess 환경변수로 주입
    → jira-sync가 사용
```

jira-sync-server의 `.env`에는 서버 설정만 있고, Jira/Notion 자격증명은 jira-sync의 `.env`에서만 관리합니다.

## 사전 요구사항

- Docker, Docker Compose
- lm2 호스트에 [jira-sync](https://github.com/Whale-Park18/jira-sync) 클론 및 설정 완료

### jira-sync 설정 (lm2에서)

```bash
git clone https://github.com/Whale-Park18/jira-sync.git
cd jira-sync

cp .env.example .env
vi .env                          # Jira/Notion 자격증명 입력

cp sync_config.example.yaml sync_config.yaml
vi sync_config.yaml              # JQL, 필드 매핑 설정
```

## 파일 구조

```
jira-sync-server/
├── app/
│   ├── config.py        # 환경변수 → 설정 객체
│   ├── auth.py          # 비밀번호 인증, 세션 쿠키
│   ├── runner.py        # jira-sync subprocess 실행 및 상태 관리
│   ├── main.py          # FastAPI 앱
│   ├── routers/
│   │   ├── api.py       # POST /api/sync, GET /api/status
│   │   └── pages.py     # /, /login, /logout
│   └── templates/       # Jinja2 HTML 템플릿
├── data/                # 동기화 상태 파일 저장 (볼륨 마운트)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 설정

`.env.example`을 복사해서 `.env`를 만듭니다.

```bash
cp .env.example .env
```

`.env` 작성:

```dotenv
# 서버 설정
SERVER_PASSWORD=your-secure-password
SECRET_KEY=your-random-64-char-string
PORT=8000

# lm2 호스트에서 jira-sync 디렉토리의 절대 경로
# .env와 sync_config.yaml이 이 안에 있어야 합니다
JIRA_SYNC_DIR=/home/user/jira-sync
```

> `SECRET_KEY`는 아래 명령으로 생성할 수 있습니다.
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

## 배포

```bash
docker compose up --build -d
```

브라우저에서 `http://lm2-ip:8000` 접속 후 비밀번호 입력.

### 로그 확인

```bash
docker compose logs -f
```

### 컨테이너 상태 확인

```bash
docker compose ps
```

### jira-sync 업데이트 반영

jira-sync 코드가 변경된 경우 이미지를 다시 빌드해야 합니다.

```bash
docker compose build --no-cache
docker compose up -d
```

## 볼륨 구조

| 호스트 경로 | 컨테이너 경로 | 용도 |
|------------|--------------|------|
| `$JIRA_SYNC_DIR` | `/config` (읽기 전용) | jira-sync `.env` 및 `sync_config.yaml` |
| `./data` | `/data` | 동기화 상태 파일 영속 |

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 메인 페이지 |
| `GET` | `/login` | 로그인 페이지 |
| `POST` | `/login` | 로그인 |
| `POST` | `/logout` | 로그아웃 |
| `POST` | `/api/sync` | 동기화 실행 (202: 시작됨, 409: 이미 실행 중) |
| `GET` | `/api/status` | 현재 동기화 상태 조회 |
