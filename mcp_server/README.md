# FocusLearn MCP

把个人时间管理系统的 REST API 暴露给 Cursor / Claude 等 AI，方便在对话中直接写入计划、学习记录与重要日期。

## 已实现工具（Phase 1）

| 工具 | 作用 |
|------|------|
| `ping_focuslearn` | 检查登录与连通性 |
| `list_subjects` | 列出项目 |
| `list_chapters` | 列出某项目子任务 |
| `list_subject_chapter_tree` | 项目→子任务树 |
| `list_tasks` | 查周历计划 / 待安排 |
| `create_calendar_task` | 创建计划或待安排 |
| `update_calendar_task` | 更新计划 |
| `toggle_task_complete` | 切换完成状态 |
| `plan_execution_record` | 按计划记执行并可选标完成 |
| `create_study_record` | 手动插入投入记录（对话要点落库） |
| `search_study_records` | 搜索记录 |
| `list_important_dates` | 重要日期列表 |
| `create_important_date` | 创建截止提醒（同步周历） |

## 前置条件

1. FocusLearn 本地或线上已启动（例如 `http://127.0.0.1:8001`）
2. 有可用的登录账号

```bash
cd E:/focuslearn
# 建议使用项目 venv
pip install -r requirements-mcp.txt
```

## Cursor 配置

1. 复制 `mcp_server/cursor-mcp.json.example` 中的片段到 Cursor MCP 配置（Settings → MCP）
2. 修改：
   - `cwd` 为仓库绝对路径
   - `FOCUSLEARN_BASE_URL`
   - `FOCUSLEARN_USERNAME` / `FOCUSLEARN_PASSWORD`
3. 重启 MCP 或 Cursor 后，对助手说：先 `ping_focuslearn`，再按项目写入记录

示例对话：

> 把下面这段沟通要点记入 FocusLearn：……  
> 请先 list_subject_chapter_tree 选项目，再用 create_study_record 写入。

## 推荐写入流程

1. `list_subject_chapter_tree` 或 `list_subjects` → `list_chapters`
2. 落内容：`create_study_record`（内容进日历红点记录）
3. 需要排期：`create_calendar_task`（可 `is_unscheduled=true` 先收进待安排）
4. 有截止日期：`create_important_date`

## 安全说明

- 凭据只放在本地 MCP 配置 / 环境变量，勿提交到 Git
- MCP 通过 Session 登录调用现有 API，不直连数据库
- 线上请使用 HTTPS，并限制账号权限

## 后续可扩展（Phase 2）

- 移动任务 `move`、重复系列 scope
- 项目计划总结 plan-summary
- 知识点搜索 / 文章摘要写入
- Token 鉴权（避免依赖 Session）
