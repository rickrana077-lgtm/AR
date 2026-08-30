# AGI Provider - Markdown Processing
# Markdown টেক্সট প্রসেস করার জন্য ইউটিলিটি ফাংশন

import re
from typing import List, Dict, Optional

class MarkdownProvider:
    """Markdown টেক্সট প্রসেসিং ও ফরম্যাটিং এর জন্য প্রোভাইডার"""
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """Markdown থেকে কোড ব্লক এক্সট্রাক্ট করে"""
        pattern = r"```(\w*)\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [{"language": lang, "code": code} for lang, code in matches]
    
    @staticmethod
    def extract_headers(text: str) -> List[Dict[str, str]]:
        """Markdown থেকে হেডার এক্সট্রাক্ট করে"""
        pattern = r"^(#{1,6})\s+(.+)$"
        matches = re.findall(pattern, text, re.MULTILINE)
        return [{"level": len(level), "text": content} for level, content in matches]
    
    @staticmethod
    def extract_links(text: str) -> List[Dict[str, str]]:
        """Markdown থেকে লিংক এক্সট্রাক্ট করে"""
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(pattern, text)
        return [{"text": text, "url": url} for text, url in matches]
    
    @staticmethod
    def to_html(text: str) -> str:
        """মৌলিক Markdown কে HTML-এ রূপান্তর করে"""
        # বোল্ড
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # ইটালিক
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # কোড
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text
    
    @staticmethod
    def strip_markdown(text: str) -> str:
        """Markdown সিনট্যাক্স বাদ দিয়ে শুধু টেক্সট রিটার্ন করে"""
        # ইমেজ
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        # লিংক
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # হেডার
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # বোল্ড/ইটালিক
        text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
        text = re.sub(r"(\*|_)(.+?)\1", r"\2", text)
        # কোড ব্লক
        text = re.sub(r"```.*?\n(.*?)\n```", r"\1", text, flags=re.DOTALL)
        return text.strip()