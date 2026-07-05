"""ContentMiner 单元测试。

覆盖：
- 初始化时创建输出目录
- 缺失 PDF 文件抛 FileNotFoundError
- batch_convert 返回标准结果字典
- _detect_backend 返回可用后端名称
- pdfplumber 后端实际转换（生成真实 PDF）
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# 让 tests 包可导入 engine 包（上级目录）
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.content_miner import ContentMiner  # noqa: E402


class ContentMinerInitTest(unittest.TestCase):
    """SubTask 4.7: test_content_miner_init_creates_output_dir"""

    def test_content_miner_init_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "nested" / "out"
            self.assertFalse(out_dir.exists())
            miner = ContentMiner(output_dir=str(out_dir))
            self.assertTrue(out_dir.exists())
            self.assertIn(miner.backend, {"mineru", "pdfplumber", "pypdf2", "none"})


class DetectBackendTest(unittest.TestCase):
    """SubTask 4.7: test_detect_backend_returns_available"""

    def test_detect_backend_returns_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            miner = ContentMiner(output_dir=tmp)
            backend = miner.backend
            # 至少应返回一个合法后端名（含 none）
            self.assertIn(backend, {"mineru", "pdfplumber", "pypdf2", "none"})
            # 若返回 none，说明环境无任何 PDF 库
            if backend == "none":
                self.skipTest("环境无可用 PDF 后端库")

    def test_detect_backend_priority_mineru(self):
        # 若 magic_pdf 可导入，后端应为 mineru
        try:
            import magic_pdf  # noqa: F401
        except ImportError:
            self.skipTest("magic_pdf 未安装，跳过优先级断言")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ContentMiner(output_dir=tmp).backend, "mineru")


class PdfToMarkdownMissingFileTest(unittest.TestCase):
    """SubTask 4.7: test_pdf_to_markdown_raises_on_missing_file"""

    def test_pdf_to_markdown_raises_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            miner = ContentMiner(output_dir=tmp)
            with self.assertRaises(FileNotFoundError):
                miner.pdf_to_markdown(str(Path(tmp) / "not_exist.pdf"))

    def test_pdf_to_markdown_raises_runtime_error_when_no_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            miner = ContentMiner(output_dir=tmp)
            if miner.backend != "none":
                self.skipTest("存在可用后端，跳过 none 分支测试")
            with self.assertRaises(RuntimeError):
                miner.pdf_to_markdown(__file__)  # 传一个存在但非 PDF 的文件


class BatchConvertTest(unittest.TestCase):
    """SubTask 4.7: test_batch_convert_returns_result_dict"""

    def test_batch_convert_returns_result_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            miner = ContentMiner(output_dir=str(out_dir))
            # 空目录
            empty_input = Path(tmp) / "input"
            empty_input.mkdir()
            result = miner.batch_convert(str(empty_input))
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            self.assertIn("failed", result)
            self.assertIn("duration_sec", result)
            self.assertEqual(result["success"], [])
            self.assertEqual(result["failed"], [])
            self.assertIsInstance(result["duration_sec"], float)

    def test_batch_convert_nonexistent_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            miner = ContentMiner(output_dir=tmp)
            result = miner.batch_convert(str(Path(tmp) / "no_such_dir"))
            self.assertEqual(result["success"], [])
            self.assertEqual(result["failed"], [])

    def test_batch_convert_handles_corrupt_pdf(self):
        # 构造一个“伪 PDF”文件，后端应记录失败而非崩溃
        try:
            import pdfplumber  # noqa: F401
        except ImportError:
            self.skipTest("pdfplumber 未安装，跳过损坏 PDF 测试")
        with tempfile.TemporaryDirectory() as tmp:
            in_dir = Path(tmp) / "in"
            in_dir.mkdir()
            bad_pdf = in_dir / "bad.pdf"
            bad_pdf.write_bytes(b"%PDF-1.4 broken content not a real pdf")
            miner = ContentMiner(output_dir=str(Path(tmp) / "out"))
            result = miner.batch_convert(str(in_dir))
            self.assertEqual(len(result["failed"]), 1)
            self.assertEqual(result["failed"][0]["file"], str(bad_pdf))


class PdfplumberConversionTest(unittest.TestCase):
    """验证 pdfplumber 后端能完成真实 PDF → Markdown 转换。"""

    def _make_simple_pdf(self, path: Path) -> None:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            self.skipTest("reportlab 未安装，无法构造测试 PDF")
        c = canvas.Canvas(str(path), pagesize=letter)
        c.drawString(100, 700, "Hello DeFi Whitepaper")
        c.showPage()
        c.drawString(100, 700, "Second page content")
        c.showPage()
        c.save()

    def test_pdfplumber_convert_real_pdf(self):
        try:
            import pdfplumber  # noqa: F401
        except ImportError:
            self.skipTest("pdfplumber 未安装")
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            self._make_simple_pdf(pdf_path)
            out_dir = Path(tmp) / "out"
            miner = ContentMiner(output_dir=str(out_dir))
            # 强制走 pdfplumber 以避免依赖 mineru
            miner._backend = "pdfplumber"
            md_path = miner.pdf_to_markdown(str(pdf_path))
            self.assertTrue(Path(md_path).exists())
            content = Path(md_path).read_text(encoding="utf-8")
            self.assertIn("Hello DeFi Whitepaper", content)
            self.assertIn("Second page content", content)
            self.assertIn("第 1 页", content)
            self.assertIn("第 2 页", content)


if __name__ == "__main__":
    unittest.main()
