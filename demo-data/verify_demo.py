#!/usr/bin/env python3
"""离线复核公开示例的链接、证据引句、网页内容与隐私路径。"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "99附件" / "验证报告.md"
PDF = ROOT / "99附件" / "tunnermann2026-data-model-guided-emittance.pdf"
FULLTEXT = PDF.with_suffix(".txt")
OUTLINE = ROOT / "03综述草稿" / "组会大纲" / "数据与模型引导的发射度优化-组会大纲.md"
HTML = ROOT / "showcase.html"
BROWSER_RESULT = ROOT / "99附件" / "浏览器验证.json"
EXPECTED_SHA256 = "307b6577e44082faaefa8f4156a4f9a2dd65dba054545428e1235ffcd058ef89"
EXPECTED_SIZE = 4_204_750
CITEKEY = "tunnermann2026DataModel"
DOI = "10.1103/kk2s-s43l"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def source_normalize(text: str) -> str:
    """合并 PDF 提取换行，并修复已回查的少量字形空格损失。"""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    replacements = {
        "0 :4 μma t": "0.4 μm at",
        "about0.36": "about 0.36",
        "1.6 inx": "1.6 in x",
        "1.1 iny": "1.1 in y",
        "approxi-\nmately": "approximately",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return normalize(text)


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def clean_md_inline(text: str) -> str:
    text = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    return normalize(text.replace("**", "").replace("`", ""))


class ShowcaseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.text: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if values.get("href"):
            self.hrefs.append(values["href"] or "")
        if values.get("src"):
            self.srcs.append(values["src"] or "")
        if tag in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.text.append(data)


def local_target(raw: str) -> tuple[str, str] | None:
    raw = raw.strip().strip("<>")
    if not raw or raw.startswith("#"):
        return None
    parts = urlsplit(raw)
    if parts.scheme or parts.netloc or raw.startswith(("mailto:", "data:", "javascript:")):
        return None
    return unquote(parts.path), unquote(parts.fragment)


def resolve_markdown_target(source: Path, target: str) -> Path | None:
    candidates = [ROOT / target, source.parent / target]
    expanded: list[Path] = []
    for candidate in candidates:
        expanded.append(candidate)
        if not candidate.suffix:
            expanded.append(candidate.with_suffix(".md"))
    for candidate in expanded:
        if candidate.is_file():
            return candidate
    if "/" not in target and "\\" not in target:
        stem = Path(target).stem
        matches = [p for p in ROOT.rglob("*") if p.is_file() and p.stem == stem]
        if len(matches) == 1:
            return matches[0]
    return None


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []
    results: list[tuple[str, str, str]] = []
    if not REPORT.exists():
        REPORT.write_text("# 验证报告\n\n检查运行中；完成后本文件会被结果覆盖。\n", encoding="utf-8")

    required = [
        ROOT / "README.md", HTML, PDF, FULLTEXT, OUTLINE, BROWSER_RESULT,
        ROOT / "demo-data" / "browser_smoke.cjs", ROOT / ".gitignore",
        ROOT / "00开始", ROOT / "01文献笔记", ROOT / "02概念笔记",
        ROOT / "03综述草稿" / "组会大纲", ROOT / "04导航页",
        ROOT / "98模板", ROOT / "99附件", ROOT / "demo-data",
    ]
    missing = [rel(p) for p in required if not p.exists()]
    if missing:
        failures.append("缺少必需文件或目录：" + "、".join(missing))
    results.append(("必需结构", "PASS" if not missing else "FAIL", f"{len(required) - len(missing)}/{len(required)} 项存在"))

    try:
        item = json.loads((ROOT / "demo-data" / "zotero-item.json").read_text(encoding="utf-8"))
        annotations_doc = json.loads((ROOT / "demo-data" / "zotero-annotations.json").read_text(encoding="utf-8"))
        annotations = annotations_doc["annotations"]
        metadata_ok = (
            len(item) == 1
            and item[0]["id"] == CITEKEY
            and item[0]["DOI"] == DOI
            and item[0]["issued"]["date-parts"] == [[2026, 5, 8]]
            and item[0]["volume"] == "29"
            and item[0]["issue"] == "5"
            and item[0]["page"] == "050701"
            and len(item[0]["author"]) == 19
            and item[0]["rights"] == "Creative Commons Attribution 4.0 International"
            and len(annotations) == 6
            and annotations_doc["citekey"] == CITEKEY
            and annotations_doc["doi"] == DOI
            and annotations_doc["reader"] == "Demo Reader (fictional)"
            and "not an official Zotero export" in annotations_doc["demoNotice"]
        )
        if not metadata_ok:
            failures.append("CSL JSON 或批注 JSON 的元数据、数量、许可或演示声明不符合预期")
        results.append(("JSON 与题录", "PASS" if metadata_ok else "FAIL", "19 位作者；6 条新建批注；citekey、DOI、许可一致"))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        failures.append(f"JSON 解析或字段检查失败：{exc}")
        results.append(("JSON 与题录", "FAIL", str(exc)))
        annotations = []

    pdf_ok = PDF.is_file() and PDF.stat().st_size == EXPECTED_SIZE
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest() if PDF.is_file() else "missing"
    pdf_ok = pdf_ok and digest == EXPECTED_SHA256 and PDF.read_bytes()[:5] == b"%PDF-"
    fulltext = FULLTEXT.read_text(encoding="utf-8") if FULLTEXT.is_file() else ""
    page_markers = re.findall(r"^===== PDF PAGE (\d+) =====$", fulltext, flags=re.M)
    pdf_ok = pdf_ok and page_markers == [str(i) for i in range(1, 10)]
    if not pdf_ok:
        failures.append("PDF 大小、SHA-256、文件头或 9 页文本锚点不匹配")
    results.append(("公开 PDF", "PASS" if pdf_ok else "FAIL", f"9 页锚点；{EXPECTED_SIZE:,} bytes；SHA-256 {digest[:12]}…"))

    quote_misses: list[str] = []
    normalized_source = source_normalize(fulltext)
    for annotation in annotations:
        quote = normalize(annotation.get("exactText", ""))
        if quote not in normalized_source:
            quote_misses.append(annotation.get("annotationID", "unknown"))
    if quote_misses:
        failures.append("以下批注引句未能回查公开全文：" + "、".join(quote_misses))
    results.append(("原文引句", "PASS" if not quote_misses and len(annotations) == 6 else "FAIL", f"{len(annotations) - len(quote_misses)}/{len(annotations)} 条批注引句回查成功；PDF 为最终依据"))

    markdown_files = sorted(p for p in ROOT.rglob("*.md") if ".tools" not in p.parts)
    wikilink_count = 0
    markdown_link_count = 0
    broken_links: list[str] = []
    wikilink_re = re.compile(r"(?<!!)\[\[([^\]]+)\]\]|!\[\[([^\]]+)\]\]")
    md_link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for md in markdown_files:
        text = strip_fenced_code(md.read_text(encoding="utf-8"))
        for match in wikilink_re.finditer(text):
            raw = match.group(1) or match.group(2) or ""
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            wikilink_count += 1
            if resolve_markdown_target(md, unquote(target)) is None:
                broken_links.append(f"{rel(md)} → wikilink {target}")
        for match in md_link_re.finditer(text):
            parsed = local_target(match.group(1).split(" ", 1)[0])
            if not parsed:
                continue
            target, _fragment = parsed
            if not target:
                continue
            markdown_link_count += 1
            if resolve_markdown_target(md, target) is None:
                broken_links.append(f"{rel(md)} → Markdown link {target}")
    if broken_links:
        failures.extend("断链：" + item for item in broken_links)
    results.append(("Vault 链接", "PASS" if not broken_links else "FAIL", f"{wikilink_count} 个 wikilink；{markdown_link_count} 个 Markdown 本地链接；0 个断链" if not broken_links else f"{len(broken_links)} 个断链"))

    html = HTML.read_text(encoding="utf-8")
    parser = ShowcaseParser()
    parser.feed(html)
    html_broken: list[str] = []
    html_local_count = 0
    for href in parser.hrefs:
        if href.startswith("#"):
            if href[1:] not in parser.ids:
                html_broken.append(f"缺失锚点 {href}")
            continue
        parsed = local_target(href)
        if not parsed:
            continue
        target, fragment = parsed
        if not target:
            continue
        html_local_count += 1
        destination = ROOT / target
        if not destination.is_file():
            html_broken.append(f"showcase.html → {target}")
        elif fragment and destination.suffix.lower() == ".html":
            fragment_parser = ShowcaseParser()
            fragment_parser.feed(destination.read_text(encoding="utf-8"))
            if fragment not in fragment_parser.ids:
                html_broken.append(f"{target} 缺失锚点 #{fragment}")
    duplicate_ids = [key for key, count in Counter(parser.ids).items() if count > 1]
    if duplicate_ids:
        html_broken.append("重复 HTML id：" + "、".join(duplicate_ids))
    if html_broken:
        failures.extend(html_broken)
    results.append(("HTML 链接与 id", "PASS" if not html_broken else "FAIL", f"{html_local_count} 个本地文件链接；{len(parser.ids)} 个唯一 id；0 个断链" if not html_broken else f"{len(html_broken)} 项异常"))

    required_ids = {"demo-main", "step-1", "step-2", "step-3", "step-4", "step-5", "step-6", "evidence-filter", "print-outline"}
    structure_ok = (
        required_ids.issubset(set(parser.ids))
        and html.count('class="step-panel"') == 6
        and html.count('class="annotation-card"') == 6
        and html.count('class="evidence-row"') == 6
        and html.count('class="outline-slide"') == 8
        and html.count("data-stage-panel=") == 3
        and "connect-src 'none'" in html
        and not re.search(r"(?:src|href)=[\"']https?://[^\"']+\.(?:js|css|png|jpe?g|svg|woff2?)", html, flags=re.I)
    )
    if not structure_ok:
        failures.append("HTML 步骤、批注、证据、大纲数量、必需 id 或离线资源约束不符合预期")
    results.append(("HTML 结构", "PASS" if structure_ok else "FAIL", "6 步；6 批注；3 阶段；6 证据；8 页大纲；无外部静态资源"))

    html_text = normalize("".join(parser.text))
    outline_lines = []
    in_slides = False
    for line in OUTLINE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 第 "):
            in_slides = True
        elif line.startswith("## 参考文献"):
            in_slides = False
        if in_slides and line.startswith("- "):
            outline_lines.append(clean_md_inline(line[2:]))
    outline_misses = [line for line in outline_lines if line not in html_text]
    quote_html_misses = [a["annotationID"] for a in annotations if normalize(a["exactText"]) not in html_text]
    if outline_misses:
        failures.append(f"组会大纲有 {len(outline_misses)} 条要点未同步到 HTML")
    if quote_html_misses:
        failures.append("HTML 缺少批注原文：" + "、".join(quote_html_misses))
    content_ok = not outline_misses and not quote_html_misses
    results.append(("网页—Vault 内容一致", "PASS" if content_ok else "FAIL", f"{len(outline_lines) - len(outline_misses)}/{len(outline_lines)} 条大纲要点；{len(annotations) - len(quote_html_misses)}/{len(annotations)} 条原文引句"))

    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S)
    node = shutil.which("node")
    js_ok = False
    js_detail = "未找到 Node.js"
    if node:
        proc = subprocess.run([node, "--check", "-"], input="\n".join(scripts), text=True, capture_output=True, check=False)
        js_ok = proc.returncode == 0
        js_detail = "Node.js --check 通过" if js_ok else normalize(proc.stderr)
    if not js_ok:
        failures.append("JavaScript 语法检查未通过：" + js_detail)
    results.append(("JavaScript 语法", "PASS" if js_ok else "FAIL", js_detail))

    try:
        browser_result = json.loads(BROWSER_RESULT.read_text(encoding="utf-8"))
        browser_checks = browser_result.get("checks", [])
        browser_ok = (
            browser_result.get("status") == "PASS"
            and len(browser_checks) == 8
            and all(check.get("pass") is True for check in browser_checks)
            and not browser_result.get("consoleErrors")
        )
        browser_detail = f"{len(browser_checks)}/8 项无头浏览器交互检查；file:// 离线加载；桌面与 390px 移动布局；0 个控制台错误"
    except (OSError, json.JSONDecodeError) as exc:
        browser_ok = False
        browser_detail = str(exc)
    if not browser_ok:
        failures.append("浏览器实测记录缺失或未通过：" + browser_detail)
    results.append(("浏览器交互记录", "PASS" if browser_ok else "FAIL", browser_detail))

    scan_suffixes = {".md", ".json", ".bib", ".html", ".py", ".cjs", ".txt"}
    private_hits: list[str] = []
    absolute_pattern = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|home)[\\/]")
    users_pattern = re.compile(r"/" + "Users" + r"/")
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in scan_suffixes and ".tools" not in p.parts):
        if path == FULLTEXT:
            continue  # 公开论文原文含公开机构地址，不是本地私人路径；仍单独保留来源。
        text = path.read_text(encoding="utf-8", errors="replace")
        if absolute_pattern.search(text) or users_pattern.search(text):
            private_hits.append(rel(path))
    if private_hits:
        failures.append("发现个人绝对路径模式：" + "、".join(private_hits))
    results.append(("隐私路径扫描", "PASS" if not private_hits else "FAIL", "Markdown、JSON、BibTeX、HTML、Python、CJS 中未发现个人绝对路径模式；公开 PDF 原文不参与误报扫描"))

    git_absent = not (ROOT / ".git").exists()
    results.append(("远端与 Git 边界", "PASS" if git_absent else "INFO", "示例目录无 .git；检查脚本不执行网络、Git 或远端操作" if git_absent else "发现 .git；本脚本未执行 Git 操作"))

    status = "PASS" if not failures else "FAIL"
    generated = date.today().isoformat()
    report_lines = [
        "# 验证报告",
        "",
        f"> 运行日期：{generated}  ",
        f"> 总体结果：**{status}**  ",
        "> 方式：`python demo-data/verify_demo.py`，仅使用 Python 标准库；JavaScript 语法复用本机 Node.js。浏览器交互记录由 `node demo-data/browser_smoke.cjs` 生成。",
        "",
        "## 结果汇总",
        "",
        "| 检查项 | 结果 | 明细 |",
        "|---|---|---|",
    ]
    report_lines.extend(f"| {name} | {state} | {detail} |" for name, state, detail in results)
    report_lines.extend([
        "",
        "## 证据来源",
        "",
        "- 公开论文：H. Tünnermann et al. (2026), *Physical Review Accelerators and Beams* 29(5), 050701。",
        "- DOI：https://doi.org/10.1103/kk2s-s43l",
        "- 许可：https://creativecommons.org/licenses/by/4.0/",
        "- 本地依据：[[99附件/tunnermann2026-data-model-guided-emittance.pdf|出版社 PDF]]、[[99附件/tunnermann2026-data-model-guided-emittance.txt|带页码全文文本]]。",
        "- 六条批注的引句与页码回查公开全文；`DEMO001`、批注 ID、时间、颜色和 Demo Reader 评论均为新建演示数据。",
        "",
        "## 检查边界",
        "",
        "本检查验证本地文件存在性、wikilink/Markdown/HTML 链接、HTML 锚点与结构、网页关键内容同步、JSON 字段、PDF 校验值、原文引句、JavaScript 语法和个人绝对路径模式。另附 8 项无头浏览器实测，覆盖 file:// 加载、步骤切换、AI 对照、证据筛选、大纲展开、桌面/移动布局和控制台。它不等于驱动真实 Zotero 或 Obsidian 客户端，也不替代人工科学审读。公式提取可能有排版损失，因此科学内容仍以 PDF 页面为最终依据。",
        "",
        "未创建远端仓库，未 push，未访问真实订单、未公开工程资料或任何私人 Vault 正文。网页不包含外部静态资源；CSP 禁止脚本发起网络连接。",
        "",
        "## 异常明细",
        "",
    ])
    if failures:
        report_lines.extend(f"- {item}" for item in failures)
    else:
        report_lines.append("- 无。所有自动检查通过。")
    if notes:
        report_lines.extend(["", "## 备注", ""] + [f"- {item}" for item in notes])
    report_lines.extend([
        "",
        "## 公开仓库适配结论",
        "",
        "当总体结果为 PASS 时，本目录在来源署名、隐私边界和本地链接方面适合作为新公开 GitHub 仓库的内容基础。正式发布前仍应由仓库所有者选择原创文本与代码的仓库级许可证，并保留论文 CC BY 4.0 署名信息。",
        "",
    ])
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"{status}: {len(results)} 组检查；{wikilink_count} 个 wikilink；{html_local_count} 个 HTML 本地链接；报告 {rel(REPORT)}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
