# llm backend

## Requirements

Docker & Docker-Compose

## Quick Start

```bash
./run.sh
```

or try `docker compose up` `docker compose up`

## Configures

edit in `Dockerfile` and `docker-compose.yml`

- Default Port :8000    
- Default Mount Path
    ```
    - ../ChatBoxDemo/server/chat.db:/app/chat.db:ro
    - ./.env:/app/.env:ro
    - ./outputs:/app/plugin_outputs 
    ```
- REMEMBER to add your key in `.env` as format:
    ```
    OPENROUTER_API_KEY=sk-or-v1-123456YOURKEY
    ```

## Usage

-  `action=chat` Send a request to invoke a plugin once
    ```bash
    curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d '{"action": "chat"}'

    {"reply":"plugin: plugin-md; reason: 聊天内容涉及包饺子的讨论，需要生成食谱或材料准备指南。","output_path":"/app/plugin_outputs/md_1750261384.md"}
    ```

- `action=list` Get the list of files currently generated
    ```bash
    curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d '{"action": "list"}'

    {"files":["md_1750261384.md","md_1750261000.md","md_1750258500.md","md_1750261051.md"]}
    ```