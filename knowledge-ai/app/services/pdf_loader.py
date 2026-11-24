
import pymupdf


class PDFLoader:

    def load(self, file_path: str):

        documents = []

        with pymupdf.open(file_path) as pdf:

            for page_number, page in enumerate(pdf):

                text = page.get_text("text").strip()

                if text:
                    documents.append({
                        "text": text,
                        "page": page_number + 1
                    })

        return documents
