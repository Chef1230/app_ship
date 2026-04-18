# 船舶管材预估系统

本项目是一个本地可运行的 Python + Gradio 最小版系统，用于项目管理、表格导入编辑、Leave-One-Out 预测和 Excel 导出。

## 运行方式

```bash
cd app_ship
pip install -r requirements.txt
python app.py
```

默认访问地址：

```text
http://127.0.0.1:7870
```

## 功能

- 上传 CSV / Excel 并新建项目
- 项目名为空时，自动使用上传文件名作为项目名
- 搜索、切换项目，点击项目卡片后加载对应表格
- 在项目卡片右侧 `...` 菜单中删除项目
- 使用 Gradio Dataframe 直接编辑表格
- 保存当前表格到本地 `current.parquet`
- 使用 RPT 或 TabPFN v2.5 占位模型执行 Leave-One-Out 预测
- 输出 `y_predict`、`abs_error`、`rel_error_pct`
- 展示 MAE、RMSE、MAPE
- 导出项目目录下的 `export.xlsx` 并在界面下载

## 数据目录

每个项目保存在：

```text
data/projects/{project_id}/
├── meta.json
├── current.parquet
├── latest_result.parquet
└── export.xlsx
```

其中 `meta.json` 包含 `project_id`、`project_name`、`vehicle_name`、`created_at`、`updated_at`。
