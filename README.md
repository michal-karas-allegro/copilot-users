1. Install uv (if not already installed):
   ```bash
   brew install uv
   ```

2. Create and activate virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Set the AUTH_TOKEN in the `copilot_users.py` file.

5. Run the script:
   ```bash
   python src/copilot_users/copilot_users.py
   ```