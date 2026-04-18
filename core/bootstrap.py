from config.settings import PROJECTS_DIR

def bootstrap_app():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)