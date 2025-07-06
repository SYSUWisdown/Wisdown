# == Wisdown ==

## Introduction 💡

Wisdown is an **AI-powered, multi-plugin web workspace** that blends a **real-time chatroom** with an **LLM back end**. Built for rapid, **text-centric collaboration** and **brainstorming**, it streamlines online teamwork and becomes a powerful ally for every stage of your workflow.

## Server Deployment ⏬

### Software Dependencies

* **Docker & Docker Compose**
* **Node.js 16+**
* **Python 3.10+**

### Deploying the LLM Backend

1. Open **`docker-compose.yml`** and set:

   * the LLM **API key**
   * the **port mapping** (host **8000 → 8000** in the container by default)
   * the **database path** (default: `chat.db`)
2. From the `llm/` directory, run:

   ```bash
   ./run.sh
   ```

### Deploying the Chatbox Backend

1. In **`chatbox/ipconfig.js`**, replace the placeholder IP with your server’s IP.
2. From the `chatbox/backend` directory, run:

   ```bash
   rm -rf node_modules package-lock.json
   npm install
   node index.js
   ```

   The backend listens on **SERVER\_IP:3000** by default.

### Building the Front-end

From the `chatbox/frontend` directory, run:

```bash
rm -rf node_modules package-lock.json
npm install
npm run serve
```

The front-end is served at **SERVER\_IP:8080** by default.
