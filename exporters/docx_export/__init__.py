"""Standalone Markdown-to-Word converter, usable independently of the bot:

    from exporters.docx_export import render_markdown_summary_to_docx
    docx_bytes = render_markdown_summary_to_docx(markdown_text)

Or from the command line:

    python -m exporters.docx_export input.md output.docx
"""
from exporters.docx_export.converter import render_markdown_summary_to_docx

__all__ = ["render_markdown_summary_to_docx"]
