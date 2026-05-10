import gradio as gr
import pandas as pd

from config.settings import APP_TITLE
from config.model_registry import MODEL_OPTIONS
from services.project_service import ProjectService
from services.table_service import TableService
from services.prediction_service import PredictionService
from services.export_service import ExportService

project_service = ProjectService()
table_service = TableService()
prediction_service = PredictionService()
export_service = ExportService()

def format_project_choices(projects):
    return [(f"{p['project_name']} | {p['created_at']}", p["project_id"]) for p in projects]

def create_project(name):
    if not name or not name.strip():
        return gr.update(), gr.update(), "请输入项目名称"
    meta = project_service.create_project(name.strip())
    projects = project_service.list_projects()
    df = table_service.load_project_table(meta["project_id"])
    return (
        gr.update(choices=format_project_choices(projects), value=meta["project_id"]),
        df,
        f"已创建项目：{meta['project_name']}"
    )

def search_projects(keyword):
    projects = project_service.search_projects(keyword)
    return gr.update(choices=format_project_choices(projects))

def load_project(project_id):
    if not project_id:
        return pd.DataFrame(), "未选择项目", gr.update(choices=[])
    df = table_service.load_project_table(project_id)
    target_choices = list(df.columns)
    return df, f"当前项目：{project_id}", gr.update(choices=target_choices)

def import_file(project_id, file):
    if not project_id:
        return pd.DataFrame(), "请先选择项目", gr.update()
    if file is None:
        return pd.DataFrame(), "请上传文件", gr.update()

    df = table_service.import_table(project_id, file.name)
    return df, "导入成功", gr.update(choices=list(df.columns))

def save_table(project_id, df):
    if not project_id:
        return "请先选择项目"
    if df is None:
        return "当前没有表格可保存"
    df = pd.DataFrame(df)
    table_service.save_project_table(project_id, df)
    return "保存成功"

def add_row(df):
    df = pd.DataFrame(df)
    return table_service.add_row(df)

def add_column(df):
    df = pd.DataFrame(df)
    return table_service.add_column(df), gr.update(choices=list(pd.DataFrame(df).columns))

def predict(project_id, df, model_name, target_col):
    if not project_id:
        return pd.DataFrame(), "请先选择项目", None
    if df is None or len(df) == 0:
        return pd.DataFrame(), "表格为空", None
    if not target_col:
        return pd.DataFrame(df), "请选择目标列", None

    df = pd.DataFrame(df)
    result_df = prediction_service.run_prediction(project_id, df, model_name, target_col)
    export_path = export_service.export_excel(project_id, result_df)
    return result_df, "预测完成", export_path

def export_current(project_id, df):
    if not project_id:
        raise gr.Error("请先选择项目")
    if df is None:
        raise gr.Error("当前没有表格可导出")
    df = pd.DataFrame(df)
    export_path = export_service.export_excel(project_id, df)
    return gr.update(value=export_path), "导出成功"

def build_app():
    projects = project_service.list_projects()

    with gr.Blocks(title=APP_TITLE, css="""
    .app-header {font-size: 24px; font-weight: 700; color: #1d4ed8; margin-bottom: 8px;}
    .panel-title {font-size: 16px; font-weight: 600; color: #1e40af;}
    .sidebar-wrap {border-right: 1px solid #dbeafe; padding-right: 10px;}
    .workspace-wrap {padding-left: 10px;}
    """) as demo:
        current_project_id = gr.State(value=None)

        with gr.Row():
            with gr.Column(scale=1, min_width=280, elem_classes="sidebar-wrap"):
                gr.Markdown("## 🚢 项目管理")
                project_name_input = gr.Textbox(label="新建项目名称", placeholder="输入项目名")
                create_btn = gr.Button("新建项目", variant="primary")
                search_box = gr.Textbox(label="搜索项目", placeholder="按名称 / 创建时间搜索")
                project_list = gr.Radio(
                    choices=format_project_choices(projects),
                    label="项目列表",
                    value=None
                )

            with gr.Column(scale=4, elem_classes="workspace-wrap"):
                header_text = gr.Markdown(f"<div class='app-header'>{APP_TITLE}</div>")
                data_table = gr.Dataframe(
                    label="表格数据",
                    interactive=True,
                    wrap=True,
                    row_count=(10, "dynamic"),
                    col_count=(5, "dynamic"),
                    render=False,
                )

                with gr.Row():
                    file_input = gr.File(label="导入 Excel/CSV", file_types=[".csv", ".xlsx", ".xls"])
                    import_btn = gr.Button("导入", variant="secondary")
                    save_btn = gr.Button("保存表格")
                    add_row_btn = gr.Button("新增行")
                    add_col_btn = gr.Button("新增列")
                    export_btn = gr.DownloadButton(
                        "导出 Excel",
                    )

                data_table.render()

                with gr.Row():
                    model_dropdown = gr.Dropdown(
                        choices=MODEL_OPTIONS,
                        value="RPT",
                        label="预测模型"
                    )
                    target_col_dropdown = gr.Dropdown(
                        choices=[],
                        label="目标列"
                    )
                    predict_btn = gr.Button("开始预测", variant="primary")

                status_text = gr.Textbox(label="状态", interactive=False)
                download_file = gr.File(label="下载导出文件")

        create_btn.click(
            fn=create_project,
            inputs=[project_name_input],
            outputs=[project_list, data_table, status_text]
        )

        search_box.change(
            fn=search_projects,
            inputs=[search_box],
            outputs=[project_list]
        )

        project_list.change(
            fn=load_project,
            inputs=[project_list],
            outputs=[data_table, status_text, target_col_dropdown]
        )

        import_btn.click(
            fn=import_file,
            inputs=[project_list, file_input],
            outputs=[data_table, status_text, target_col_dropdown]
        )

        save_btn.click(
            fn=save_table,
            inputs=[project_list, data_table],
            outputs=[status_text]
        )

        add_row_btn.click(
            fn=add_row,
            inputs=[data_table],
            outputs=[data_table]
        )

        add_col_btn.click(
            fn=add_column,
            inputs=[data_table],
            outputs=[data_table, target_col_dropdown]
        )

        predict_btn.click(
            fn=predict,
            inputs=[project_list, data_table, model_dropdown, target_col_dropdown],
            outputs=[data_table, status_text, download_file]
        )
        export_btn.click(
            fn=export_current,
            inputs=[project_list, data_table],
            outputs=[export_btn, status_text]
        )

    return demo
