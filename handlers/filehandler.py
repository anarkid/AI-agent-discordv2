import os
from docx import Document
import fitz  # PyMuPDF
from pptx import Presentation  # Add this to the top of the file

class FileHandler:
    def __init__(self):
        os.makedirs("temp", exist_ok=True)

    async def process_attachments(self, attachments):
        file_contexts = []
        for attachment in attachments:
            filename = attachment.filename.lower()
            if filename.endswith('.pdf'):
                content = await self.extract_pdf(attachment)
                if content:
                    file_contexts.append(f"[PDF: {attachment.filename}]\n{content}")
            elif filename.endswith('.docx'):
                content = await self.extract_docx(attachment)
                if content:
                    file_contexts.append(f"[DOCX: {attachment.filename}]\n{content}")
            elif filename.endswith('.pptx'):
                content = await self.extract_pptx(attachment)
                if content:
                    file_contexts.append(f"[PPTX: {attachment.filename}]\n{content}")
            elif filename.endswith('.txt'):
                content = await self.extract_txt(attachment)
                if content:
                    file_contexts.append(f"[TXT: {attachment.filename}]\n{content}")
        return "\n".join(file_contexts)

    async def extract_pdf(self, attachment):
        try:
            file_path = f"temp/{attachment.filename}"
            await attachment.save(file_path)
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            os.remove(file_path)  # Delete the file after reading
            return text.strip() if text else None
        except Exception as e:
            return f"[Error reading PDF: {e}]"

    async def extract_docx(self, attachment):
        try:
            file_path = f"temp/{attachment.filename}"
            await attachment.save(file_path)
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            os.remove(file_path)  # Delete the file after reading
            return text.strip() if text else None
        except Exception as e:
            return f"[Error reading DOCX: {e}]"

    async def extract_txt(self, attachment):
        try:
            file_path = f"temp/{attachment.filename}"
            await attachment.save(file_path)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            os.remove(file_path)  # Delete the file after reading
            return text.strip() if text else None
        except Exception as e:
            return f"[Error reading TXT: {e}]"

    async def extract_pptx(self, attachment):
        try:
            file_path = f"temp/{attachment.filename}"
            await attachment.save(file_path)
            prs = Presentation(file_path)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            os.remove(file_path)  # Delete the file after reading
            return text.strip() if text else None
        except Exception as e:
            return f"[Error reading PPTX: {e}]"
