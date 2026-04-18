from __future__ import annotations

import base64
from pathlib import Path

PRIMARY_BLUE = "#2563eb"
PRIMARY_BLUE_HOVER = "#1d4ed8"
PRIMARY_BLUE_LIGHT = "#dbeafe"
PRIMARY_BORDER = "#bfdbfe"
BACKGROUND = "#f8fbff"
SURFACE = "#ffffff"
TEXT_MAIN = "#1e293b"
TEXT_SECONDARY = "#64748b"
SUCCESS = "#16a34a"
WARNING = "#d97706"
DANGER = "#dc2626"


def _icon_data_uri(icon_name: str) -> str:
    icon_path = Path(__file__).resolve().parents[1] / "assets" / "icons" / icon_name
    if not icon_path.exists():
        return ""

    encoded = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def get_main_css() -> str:
    more_icon = _icon_data_uri("more.png")
    return f"""
    :root {{
        --primary-blue: {PRIMARY_BLUE};
        --primary-blue-hover: {PRIMARY_BLUE_HOVER};
        --primary-blue-light: {PRIMARY_BLUE_LIGHT};
        --primary-border: {PRIMARY_BORDER};
        --bg-main: {BACKGROUND};
        --bg-surface: {SURFACE};
        --text-main: {TEXT_MAIN};
        --text-secondary: {TEXT_SECONDARY};
        --success: {SUCCESS};
        --warning: {WARNING};
        --danger: {DANGER};
        --radius-md: 10px;
        --radius-lg: 14px;
        --shadow-soft: 0 4px 18px rgba(37, 99, 235, 0.08);
    }}

    .gradio-container {{
        background: var(--bg-main);
        color: var(--text-main);
    }}

    .app-shell {{
        padding: 8px 12px;
        background: var(--bg-main);
    }}

    .panel-card {{
        background: var(--bg-surface);
        border: 1px solid var(--primary-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-soft);
        padding: 12px;
    }}

    .panel-title {{
        font-size: 18px;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 8px;
    }}

    .subtle-text {{
        font-size: 12px;
        color: var(--text-secondary);
    }}

    .primary-btn button {{
        background: var(--primary-blue) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
    }}

    .primary-btn button:hover {{
        background: var(--primary-blue-hover) !important;
    }}

    .toolbar-row {{
        gap: 8px;
        margin-bottom: 8px;
    }}

    .sidebar-card {{
        background: white;
        border: 1px solid var(--primary-border);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
    }}

    .project-card-title {{
        font-size: 14px;
        font-weight: 600;
        color: var(--text-main);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .project-card-meta {{
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
    }}

    .project-card-row {{
        width: 100%;
        background: white;
        border: 1px solid var(--primary-border);
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.05);
        align-items: stretch;
        gap: 0;
        margin-bottom: 8px;
        padding: 4px;
    }}

    .project-card-btn,
    .project-card-btn button {{
        width: 100% !important;
    }}

    .project-card-btn button {{
        min-height: 36px;
        justify-content: flex-start !important;
        text-align: left !important;
        background: transparent !important;
        color: var(--text-main) !important;
        border: none !important;
        border-radius: 8px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        box-shadow: none !important;
        padding: 6px 8px !important;
        font-size: 12px !important;
        line-height: 1.2 !important;
        display: block !important;
    }}

    .project-card-btn button:hover {{
        background: var(--primary-blue-light) !important;
    }}

    .project-more-menu {{
        min-width: 42px !important;
        max-width: 46px !important;
    }}

    .project-more-menu .wrap {{
        height: 100%;
    }}

    .project-more-menu input,
    .project-more-menu .wrap,
    .project-more-menu [data-testid="textbox"],
    .project-more-menu .container {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    .project-more-menu input {{
        background-image: url("{more_icon}") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 18px 18px !important;
        color: transparent !important;
        caret-color: transparent !important;
        cursor: pointer !important;
        min-height: 36px !important;
        padding: 0 !important;
    }}

    .project-more-menu input::selection {{
        color: transparent !important;
        background: transparent !important;
    }}

    .empty-state {{
        min-height: 420px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: var(--text-secondary);
        text-align: center;
    }}

    .predict-section {{
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--primary-border);
    }}
    """


def get_welcome_html() -> str:
    return """
    <div class="empty-state">
        <h2 style="margin-bottom: 10px;">欢迎使用预估系统</h2>
        <p style="max-width: 420px;">
            请选择左侧项目，或先新建一个项目。后续这里可扩展为 chatbot、日志摘要、预测说明区。
        </p>
    </div>
    """
