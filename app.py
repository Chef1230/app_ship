from __future__ import annotations

import gradio as gr

from config.model_registry import MODEL_OPTIONS
from config.settings import APP_TITLE, DEFAULT_HOST, DEFAULT_PORT
from config.theme import get_theme
from core.paths import ensure_data_dirs
from services.export_service import ExportService
from services.prediction_service import PredictionService
from services.project_service import ProjectService
from services.table_service import TableService
from ui.css import get_main_css, get_welcome_html


MAX_PROJECT_CARDS = 12
PROJECT_MENU_IDLE = "__menu_idle__"
PROJECT_DELETE_ACTION = "删除项目"

project_service = ProjectService()
table_service = TableService(project_service.project_repo)
prediction_service = PredictionService(project_service.project_repo)
export_service = ExportService(project_service.project_repo)


def _header(meta: dict | None = None) -> str:
    if not meta:
        return "### 当前项目：未选择"
    return f"### 当前项目：{meta.get('project_name', '未命名项目')}"


def _target_update(table_value, current_target: str | None = None):
    columns = table_service.get_target_columns(table_value)
    if current_target in columns:
        value = current_target
    else:
        value = _default_target_column(columns)
    return gr.update(choices=columns, value=value)


def _default_target_column(columns: list[str]) -> str | None:
    if not columns:
        return None

    preferred_names = {"目标值", "目标", "target", "y", "label"}
    for column in columns:
        if column in preferred_names or column.lower() in preferred_names:
            return column

    for column in columns:
        lower_name = column.lower()
        if "目标" in column or "target" in lower_name:
            return column

    return columns[-1]


def _hide_download():
    return gr.update(value=None, visible=False)


def _project_card_label(project: dict, selected_project_id: str | None = None) -> str:
    prefix = "当前 " if project.get("project_id") == selected_project_id else ""
    name = project.get("project_name") or "未命名项目"
    vehicle = project.get("vehicle_name") or "未填写系统名称"
    updated_at = (project.get("updated_at") or "")[:10]
    return f"{prefix}{name} | {vehicle} | {updated_at}"


def _project_card_configs(keyword: str = "", selected_project_id: str | None = None):
    projects = project_service.search_projects(keyword)[:MAX_PROJECT_CARDS]
    slot_ids = [project["project_id"] for project in projects]
    configs = []

    for index in range(MAX_PROJECT_CARDS):
        if index < len(projects):
            configs.append(
                {
                    "label": _project_card_label(projects[index], selected_project_id),
                    "visible": True,
                }
            )
        else:
            configs.append({"label": "", "visible": False})

    return slot_ids, configs


def _project_card_updates(keyword: str = "", selected_project_id: str | None = None):
    slot_ids, configs = _project_card_configs(keyword, selected_project_id)
    updates = [slot_ids]
    for config in configs:
        updates.append(gr.update(visible=config["visible"]))
        updates.append(gr.update(value=config["label"], visible=config["visible"]))
        updates.append(gr.update(value=PROJECT_MENU_IDLE, visible=config["visible"]))
    return tuple(updates)


def _no_main_change(selected_project_id: str | None):
    return (
        selected_project_id,
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
    )


def _empty_project_view(sidebar_message: str, action_message: str = ""):
    return (
        None,
        _header(),
        gr.update(visible=True),
        gr.update(value=table_service.empty_dataframe(), visible=False),
        gr.update(choices=[], value=None),
        sidebar_message,
        action_message,
        "",
        _hide_download(),
    )


def _loaded_project_view(project_id: str, sidebar_message: str, action_message: str = ""):
    meta = project_service.get_project(project_id)
    dataframe = project_service.load_project_table(project_id)
    return (
        project_id,
        _header(meta),
        gr.update(visible=False),
        gr.update(value=dataframe, visible=True),
        _target_update(dataframe),
        sidebar_message,
        action_message,
        "",
        _hide_download(),
    )


def _project_id_from_slot(project_ids: list[str] | None, slot_index: int) -> str | None:
    project_ids = project_ids or []
    if slot_index < 0 or slot_index >= len(project_ids):
        return None
    return project_ids[slot_index]


def handle_create_project(project_name: str, vehicle_name: str, project_file):
    try:
        meta = project_service.create_project(project_name, vehicle_name, project_file)
        dataframe = project_service.load_project_table(meta["project_id"])
        if table_service.has_file(project_file):
            message = f"已创建项目：{meta['project_name']}，已加载 {len(dataframe)} 行数据"
        else:
            message = f"已创建项目：{meta['project_name']}"

        return (
            gr.update(value=""),
            gr.update(value=None),
            *_project_card_updates("", meta["project_id"]),
            *_loaded_project_view(meta["project_id"], message, message),
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def handle_search(keyword: str, selected_project_id: str | None):
    return _project_card_updates(keyword, selected_project_id)


def handle_select_project(project_ids: list[str], slot_index: int, keyword: str):
    try:
        project_id = _project_id_from_slot(project_ids, slot_index)
        if not project_id:
            return (
                *_project_card_updates(keyword, None),
                *_empty_project_view("请选择项目"),
            )

        meta = project_service.get_project(project_id)
        message = f"已加载项目：{meta.get('project_name', '未命名项目')}"
        return (
            *_project_card_updates(keyword, project_id),
            *_loaded_project_view(project_id, message, message),
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def handle_project_action(
    project_ids: list[str],
    slot_index: int,
    action: str | None,
    selected_project_id: str | None,
    keyword: str,
):
    try:
        if action != PROJECT_DELETE_ACTION:
            return (
                *_project_card_updates(keyword, selected_project_id),
                *_no_main_change(selected_project_id),
            )

        project_id = _project_id_from_slot(project_ids, slot_index)
        if not project_id:
            return (
                *_project_card_updates(keyword, selected_project_id),
                *_no_main_change(selected_project_id),
            )

        meta = project_service.get_project(project_id)
        project_name = meta.get("project_name") or "未命名项目"
        project_service.delete_project(project_id)

        if selected_project_id == project_id:
            next_selected_id = None
            main_updates = _empty_project_view(
                f"已删除项目：{project_name}",
                "项目已删除，请选择其他项目。",
            )
        else:
            next_selected_id = selected_project_id
            main_updates = (
                selected_project_id,
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                f"已删除项目：{project_name}",
                gr.update(),
                gr.update(),
                gr.update(),
            )

        return (
            *_project_card_updates(keyword, next_selected_id),
            *main_updates,
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def handle_save(project_id: str, table_value):
    try:
        dataframe = project_service.save_project_table(project_id, table_value)
        return (
            gr.update(value=dataframe, visible=True),
            _target_update(dataframe),
            f"已保存 {len(dataframe)} 行、{len(dataframe.columns)} 列到 current.parquet",
            _hide_download(),
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def handle_table_change(table_value, current_target: str | None):
    return _target_update(table_value, current_target)


def handle_predict(project_id: str, table_value, model_name: str, target_col: str):
    try:
        dataframe, metrics = prediction_service.run_prediction(
            project_id,
            table_value,
            model_name,
            target_col,
        )
        return (
            gr.update(value=dataframe, visible=True),
            _target_update(dataframe, target_col),
            metrics,
            "预测完成，已在表格中新增 Prediction、Error、Relative_Error(%) 列，并保存到 latest_result.parquet",
            _hide_download(),
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def handle_export(project_id: str, table_value):
    try:
        export_path = export_service.export_excel(project_id, table_value)
        return gr.update(value=export_path), f"已导出 Excel：{export_path}"
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def build_app() -> gr.Blocks:
    ensure_data_dirs()
    initial_project_ids, initial_card_configs = _project_card_configs()

    with gr.Blocks(title=APP_TITLE) as demo:
        selected_project_id = gr.State(value=None)
        project_slot_ids = gr.State(value=initial_project_ids)

        with gr.Row(elem_classes=["app-shell"]):
            with gr.Column(scale=1, min_width=280, elem_classes=["panel-card", "sidebar-panel"]):
                gr.Markdown('<div class="panel-title">项目管理</div>')
                project_name = gr.Textbox(label="项目名称", placeholder="未填写时使用上传文件名")
                vehicle_name = gr.Textbox(label="系统名称", placeholder="可选，用于搜索")
                project_file = gr.File(
                    label="项目数据文件",
                    file_types=[".csv", ".xlsx", ".xls"],
                    type="filepath",
                )
                create_btn = gr.Button("新建项目", elem_classes=["primary-btn"])

                gr.Markdown('<div class="section-divider"><span>项目列表</span></div>')
                search_keyword = gr.Textbox(label="搜索项目", placeholder="按项目名 / 系统名称搜索")
                gr.Markdown('<div class="subtle-text">点击项目卡片加载表格，右侧 ... 可删除项目。</div>')

                project_card_buttons = []
                project_action_menus = []
                project_card_rows = []
                with gr.Column(elem_classes=["project-list-shell"]):
                    for index in range(MAX_PROJECT_CARDS):
                        config = initial_card_configs[index]
                        with gr.Row(
                            visible=config["visible"],
                            elem_classes=["project-card-row"],
                        ) as project_row:
                            project_button = gr.Button(
                                config["label"],
                                visible=config["visible"],
                                scale=8,
                                elem_classes=["project-card-btn"],
                            )
                            project_menu = gr.Dropdown(
                                choices=[("...", PROJECT_MENU_IDLE), (PROJECT_DELETE_ACTION, PROJECT_DELETE_ACTION)],
                                value=PROJECT_MENU_IDLE,
                                show_label=False,
                                container=False,
                                visible=config["visible"],
                                scale=1,
                                elem_classes=["project-more-menu"],
                                interactive=True,
                            )
                        project_card_rows.append(project_row)
                        project_card_buttons.append(project_button)
                        project_action_menus.append(project_menu)

                sidebar_status = gr.Markdown("请选择项目，或新建一个项目。")

            with gr.Column(scale=4, min_width=620, elem_classes=["panel-card", "content-panel"]):
                header = gr.Markdown(_header())
                data_table = gr.Dataframe(
                    value=table_service.empty_dataframe(),
                    label="结构化表格",
                    type="pandas",
                    interactive=True,
                    visible=False,
                    row_count=8,
                    column_count=5,
                    max_height=520,
                    show_search="filter",
                    render=False,
                )

                with gr.Row(elem_classes=["toolbar-row"]):
                    save_btn = gr.Button("保存", scale=1)
                    export_btn = gr.DownloadButton(
                        "导出 Excel",
                        scale=1,
                        elem_classes=["primary-btn"],
                    )

                download_file = gr.File(label="下载导出的 Excel", visible=False, interactive=False)
                action_status = gr.Markdown("点击左侧项目加载表格。编辑表格后，点击保存即可持久化到当前项目。")

                welcome = gr.HTML(get_welcome_html(), visible=True)
                data_table.render()

                with gr.Column(elem_classes=["predict-section"]):
                    gr.Markdown('<div class="panel-title">预测</div>')
                    with gr.Row():
                        model_name = gr.Dropdown(
                            label="模型",
                            choices=MODEL_OPTIONS,
                            value="RPT",
                            interactive=True,
                        )
                        target_col = gr.Dropdown(
                            label="目标列",
                            choices=[],
                            value=None,
                            interactive=True,
                        )
                        predict_btn = gr.Button("开始预测", elem_classes=["primary-btn"])

                    metrics = gr.Markdown("")

        card_outputs = [project_slot_ids]
        for row, button, menu in zip(
            project_card_rows,
            project_card_buttons,
            project_action_menus,
        ):
            card_outputs.extend([row, button, menu])

        main_outputs = [
            selected_project_id,
            header,
            welcome,
            data_table,
            target_col,
            sidebar_status,
            action_status,
            metrics,
            download_file,
        ]

        create_btn.click(
            fn=handle_create_project,
            inputs=[project_name, vehicle_name, project_file],
            outputs=[search_keyword, project_file, *card_outputs, *main_outputs],
        )
        search_keyword.change(
            fn=handle_search,
            inputs=[search_keyword, selected_project_id],
            outputs=card_outputs,
        )

        for index, project_button in enumerate(project_card_buttons):
            project_button.click(
                fn=lambda project_ids, keyword, slot_index=index: handle_select_project(
                    project_ids,
                    slot_index,
                    keyword,
                ),
                inputs=[project_slot_ids, search_keyword],
                outputs=[*card_outputs, *main_outputs],
            )

        for index, project_menu in enumerate(project_action_menus):
            project_menu.change(
                fn=lambda project_ids, action, current_id, keyword, slot_index=index: handle_project_action(
                    project_ids,
                    slot_index,
                    action,
                    current_id,
                    keyword,
                ),
                inputs=[project_slot_ids, project_menu, selected_project_id, search_keyword],
                outputs=[*card_outputs, *main_outputs],
            )

        save_btn.click(
            fn=handle_save,
            inputs=[selected_project_id, data_table],
            outputs=[data_table, target_col, action_status, download_file],
        )
        data_table.change(
            fn=handle_table_change,
            inputs=[data_table, target_col],
            outputs=target_col,
        )
        predict_btn.click(
            fn=handle_predict,
            inputs=[selected_project_id, data_table, model_name, target_col],
            outputs=[data_table, target_col, metrics, action_status, download_file],
        )
        export_btn.click(
            fn=handle_export,
            inputs=[selected_project_id, data_table],
            outputs=[export_btn, action_status],
        )
    return demo


def main() -> None:
    demo = build_app()
    demo.launch(
        server_name=DEFAULT_HOST,
        server_port=DEFAULT_PORT,
        theme=get_theme(),
        css=get_main_css(),
    )


if __name__ == "__main__":
    main()
