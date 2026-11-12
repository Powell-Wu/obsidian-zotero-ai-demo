# demo-data：新建的 Zotero 示例，不是个人库导出

## 文件说明

| 文件 | 用途 | 导入边界 |
|---|---|---|
| `zotero-item.json` | 单篇公开论文的 CSL JSON 题录 | 可用于演示 CSL JSON 字段映射；不同 Zotero 版本的导入菜单可能不同 |
| `zotero-item.bib` | 同一条目的 BibTeX 表达 | citekey 固定为 `tunnermann2026DataModel` |
| `zotero-annotations.json` | 六条新建高亮及虚构读者评论 | 教学用简化结构，不是官方 Zotero API 导出或直接导入备份 |
| `zotero-annotations-import.md` | 带页码和原文引句的 Obsidian 导入文本 | 可手工复制；不会自动写入任何 Vault |
| `verify_demo.py` | 离线检查链接、JSON、隐私路径与网页内容 | 报告写回本目录的 `99附件/验证报告.md` |
| `browser_smoke.cjs` | 用本机 Edge/Chrome 实测离线加载、交互和响应式布局 | 使用本地 CDP；临时配置写入被 `.gitignore` 排除的 `.tools/`，结果写入 `99附件/浏览器验证.json` |

## 为什么既有“真实”又有“虚构”

- **真实部分**：论文题名、作者、DOI、期刊、日期、许可、PDF 页码和引句均来自公开论文。
- **新建 / 虚构部分**：条目键 `DEMO001`、批注 ID `DEMO-A01` 至 `DEMO-A06`、颜色选择、批注时间以及 `Demo Reader (fictional)` 的评论，均为本案例创建。
- **没有的部分**：没有真实个人库、同步账号、本地数据库路径、真实阅读历史或未公开实验数据。

## 简化批注结构

每条记录包含：

- `annotationID`：演示专用 ID；
- `citekey`：与文献笔记一致；
- `type`：这里均为 `highlight`；
- `pageIndex`：从 0 开始，供程序化定位；
- `pageLabel`：从 1 开始，供人阅读；
- `exactText`：公开 PDF 原文引句；
- `comment`：虚构读者的评论，不是论文证据；
- `evidenceCandidate`：建议映射到哪个 ER 编号；
- `demoNotice`：新建数据声明。

这里不伪造 `rects` 坐标。若接入真实 Zotero PDF 阅读器，需要在客户端中重新建立高亮位置，或使用官方 API 的真实位置数据。

## 手工演示

1. 在 Zotero 新建期刊论文条目，按 `zotero-item.json` 填入公开题录。
2. 附加根目录 `99附件/` 中的公开 PDF，并打开到相应页。
3. 根据 `zotero-annotations-import.md` 新建高亮与评论。
4. 将批注文本放入 Obsidian 后，从 `01文献笔记/` 的“AI 整理前”版本继续演示。

这个流程是格式与证据链演示，不声称已自动连接 Zotero 客户端。
