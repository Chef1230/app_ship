from __future__ import annotations

import gradio as gr


def get_theme() -> gr.Theme:
    return gr.themes.Soft(primary_hue="blue", neutral_hue="slate")


def get_app_theme() -> gr.Theme:
    return get_theme()
