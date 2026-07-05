"""PDF 内容矿工模块

使用 MinerU (magic-pdf) 将 PDF 白皮书转换为 Markdown，作为 SEO 内容生成的深度素材源。
支持降级到 pdfplumber / PyPDF2 等更简单的库，保证无 MinerU 环境下仍可工作。
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ContentMiner:
    """PDF 转 Markdown 转换器（多后端降级）"""

    def __init__(self, output_dir: str = "company/knowledge/defi-whitepapers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._backend = self._detect_backend()
        logger.info("ContentMiner 使用后端: %s", self._backend)

    def _detect_backend(self) -> str:
        """检测可用的 PDF 转换后端，按优先级返回。"""
        # 1. 优先 MinerU（保留表格/公式/版面）
        try:
            import magic_pdf  # noqa: F401
            return "mineru"
        except ImportError:
            pass
        # 2. pdfplumber（文本+段落）
        try:
            import pdfplumber  # noqa: F401
            return "pdfplumber"
        except ImportError:
            pass
        # 3. PyPDF2（最基础文本提取）
        try:
            import PyPDF2  # noqa: F401
            return "pypdf2"
        except ImportError:
            pass
        logger.warning("无可用 PDF 后端，请安装 magic-pdf[full] 或 pdfplumber")
        return "none"

    @property
    def backend(self) -> str:
        """当前使用的后端名称。"""
        return self._backend

    def pdf_to_markdown(self, pdf_path: str, output_name: Optional[str] = None) -> str:
        """将单个 PDF 转换为 Markdown。

        参数:
            pdf_path: PDF 文件路径
            output_name: 输出文件名（不含扩展名），默认用 PDF 文件名

        返回:
            输出 Markdown 文件路径

        异常:
            FileNotFoundError: PDF 不存在
            RuntimeError: 无可用后端或转换失败
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 不存在: {pdf_path}")

        if output_name is None:
            output_name = pdf_path.stem

        output_path = self.output_dir / f"{output_name}.md"

        if self._backend == "mineru":
            try:
                return self._convert_with_mineru(pdf_path, output_path)
            except Exception as e:
                # MinerU 转换失败时，自动降级到 pdfplumber/pypdf2
                logger.warning("MinerU 转换失败，尝试降级: %s", e)
                if self._can_use("pdfplumber"):
                    return self._convert_with_pdfplumber(pdf_path, output_path)
                if self._can_use("pypdf2"):
                    return self._convert_with_pypdf2(pdf_path, output_path)
                raise RuntimeError(f"MinerU 转换失败且无降级后端: {e}") from e
        elif self._backend == "pdfplumber":
            return self._convert_with_pdfplumber(pdf_path, output_path)
        elif self._backend == "pypdf2":
            return self._convert_with_pypdf2(pdf_path, output_path)
        else:
            raise RuntimeError("无可用 PDF 转换后端，请安装 magic-pdf[full] 或 pdfplumber")

    def _can_use(self, name: str) -> bool:
        """检查某个降级后端是否可用（不依赖当前 _backend）。"""
        try:
            if name == "pdfplumber":
                import pdfplumber  # noqa: F401
                return True
            if name == "pypdf2":
                import PyPDF2  # noqa: F401
                return True
        except ImportError:
            return False
        return False

    def _convert_with_mineru(self, pdf_path: Path, output_path: Path) -> str:
        """使用 MinerU 转换（保留表格/公式/版面）。

        兼容 magic-pdf 不同版本的 API：
        - 新版 (>=1.x): ``magic_pdf.pipe.UNIPipe.UNIPipe`` + ``pipe_mk_markdown``
        - 若 API 不匹配则抛出异常，由上层降级处理
        """
        from magic_pdf.pipe.UNIPipe import UNIPipe
        from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter

        # 图片输出目录（MinerU 会把图片抽出，这里不强依赖）
        image_dir = str(self.output_dir / f"{pdf_path.stem}_images")
        Path(image_dir).mkdir(parents=True, exist_ok=True)
        image_writer = DiskReaderWriter(image_dir)

        pdf_bytes = pdf_path.read_bytes()
        # 模型列表留空，走内置规则；_pdf_type 留空让其自动判断
        jso_useful_key = {"_pdf_type": "", "model_list": []}

        pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        # 解析流水线：分类 -> 分析 -> 解析
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()

        # 输出 Markdown
        md_content = pipe.pipe_mk_markdown(image_dir, drop_mode="none")

        if not isinstance(md_content, str):
            # 某些版本返回 list，需拼接
            md_content = "\n".join(md_content) if md_content else ""

        output_path.write_text(md_content or "", encoding="utf-8")
        logger.info("MinerU 转换完成: %s -> %s", pdf_path.name, output_path)
        return str(output_path)

    def _convert_with_pdfplumber(self, pdf_path: Path, output_path: Path) -> str:
        """降级：使用 pdfplumber 转换（提取文本，保留段落）。"""
        import pdfplumber

        lines = [f"# {pdf_path.stem}\n"]
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                lines.append(f"\n## 第 {i} 页\n\n{text}\n")
                # 尝试提取表格（保留结构化数据）
                try:
                    tables = page.extract_tables() or []
                    for t_idx, table in enumerate(tables, 1):
                        if not table:
                            continue
                        lines.append(f"\n### 第 {i} 页 表格 {t_idx}\n")
                        for row in table:
                            cells = [str(c) if c is not None else "" for c in row]
                            lines.append("| " + " | ".join(cells) + " |")
                        # 表头分隔行
                        if table:
                            lines.insert(-len(table), "| " + " | ".join(["---"] * len(table[0])) + " |")
                except Exception as e:
                    logger.debug("表格提取失败（页 %s）: %s", i, e)

        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("pdfplumber 转换完成: %s -> %s", pdf_path.name, output_path)
        return str(output_path)

    def _convert_with_pypdf2(self, pdf_path: Path, output_path: Path) -> str:
        """降级：使用 PyPDF2 转换（最基础文本提取）。"""
        import PyPDF2

        lines = [f"# {pdf_path.stem}\n"]
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.debug("PyPDF2 第 %s 页提取失败: %s", i, e)
                    text = ""
                lines.append(f"\n## 第 {i} 页\n\n{text}\n")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("PyPDF2 转换完成: %s -> %s", pdf_path.name, output_path)
        return str(output_path)

    def batch_convert(self, input_dir: str) -> dict:
        """批量转换目录下所有 PDF。

        参数:
            input_dir: 包含 PDF 的目录

        返回:
            {"success": [str], "failed": [{"file": str, "error": str}], "duration_sec": float}
        """
        start = time.time()
        result = {"success": [], "failed": [], "duration_sec": 0}

        input_dir = Path(input_dir)
        if not input_dir.exists():
            result["duration_sec"] = round(time.time() - start, 2)
            return result

        for pdf in sorted(input_dir.glob("*.pdf")):
            try:
                output = self.pdf_to_markdown(str(pdf))
                result["success"].append(output)
            except Exception as e:
                result["failed"].append({"file": str(pdf), "error": str(e)})

        result["duration_sec"] = round(time.time() - start, 2)
        return result


# CLI 入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF 转 Markdown 转换器")
    parser.add_argument("--batch", help="批量转换目录")
    parser.add_argument("--file", help="转换单个文件")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    miner = ContentMiner()
    print(f"后端: {miner.backend}")
    if args.batch:
        result = miner.batch_convert(args.batch)
        print(f"成功: {len(result['success'])} / 失败: {len(result['failed'])} / 耗时: {result['duration_sec']}s")
        for f in result["failed"]:
            print(f"  失败: {f['file']} - {f['error']}")
    elif args.file:
        output = miner.pdf_to_markdown(args.file)
        print(f"输出: {output}")
    else:
        parser.print_help()
