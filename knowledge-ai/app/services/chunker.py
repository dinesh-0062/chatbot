
class TextChunker:

    def __init__(self, chunk_size=500, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, documents):

        chunks = []

        for document in documents:

            text = document["text"]
            start = 0

            while start < len(text):

                end = start + self.chunk_size

                chunks.append({
                    "text": text[start:end],
                    "page": document["page"]
                })

                start += self.chunk_size - self.overlap

        return chunks
