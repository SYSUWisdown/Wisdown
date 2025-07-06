in-development.md
+42
-9

# Plugin Development

Wisdown supports extending both the front-end chat interface and the LLM back end with custom plugins.  This guide outlines the basic workflow for each part of the system.

## ChatBox
### Front‑end (`Home.vue`)

Edit **`chatbox/frontend/src/components/Home.vue`** and introduce your plugin UI elements.

* Add a **new window** inside the `right-section` to display plugin results.
* Implement **data-fetching and watcher hooks** for reactive updates.
* **Adjust the layout ratios** so the plugin view fits neatly with the existing chat window.

### Back‑end (`index.js`)

Edit **`chatbox/backend/index.js`** to expose endpoints for your plugin.

* Add methods for **reading the new data types** or performing other logic required by the plugin.

## LLM

The LLM container executes Python scripts in `llm/` as plugins.  Each script consumes chat history from `chat.db` and outputs a file under `llm/outputs/`.

### Adding a Plugin

1. **Create a Python file** in `llm/`.  Use `plugin-md.py` as a template.  A plugin typically:
   - Reads the chat history from `chat.db`.
   - Accepts an optional output path argument.
   - Writes its result (markdown, image, etc.) to the given path.
2. **Update `Dockerfile`** so your script is copied into the container:
   ```Dockerfile
   COPY my-plugin.py .
   ```
3. **Register the plugin** in `chat.py`.
   - Add a brief description in the `plugin_docs` string.
   - Add a new `elif` block that calls the script with `subprocess` when the plugin name appears in the model reply.
4. **Rebuild the container**:
   ```bash
   cd llm
   ./run.sh
   ```
5. **Test** by sending a request with `action=chat` and verify that your plugin runs and the output appears in `llm/outputs/`.

### Environment Notes

Edit **`chatbox/backend/index.js`**
Ensure an `OPENROUTER_API_KEY` is set in `.env`.  Generated files are stored in `llm/outputs/` and can be served by the chatbox backend.

---

Following these steps you can extend Wisdown with your own custom plugins and tailor the workspace to your needs.