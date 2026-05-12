import os
import re
import json
import base64
import requests
import fitz
from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()

class CardRAGPipeline:
    def __init__(self):
        self.clova_url = os.getenv("NAVER_OCR_URL")
        self.clova_secret = os.getenv("NAVER_OCR_SECRET")

        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        self.splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)

        # Qdrant 클라이언트
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )

        # Dense + Sparse 동시 저장
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name="card_benefits",
            enable_hybrid=True,
            fastembed_sparse_model="Qdrant/bm25"  # BM25 내장
        )

    def is_bad_quality(self, file_path):
        with fitz.open(file_path) as doc:
            full_text = "".join([page.get_text() for page in doc])
            img_count = sum([len(page.get_images()) for page in doc])
            text_len = len(full_text.strip())

            print(f"{os.path.basename(file_path)}: 글자수 {text_len}, 이미지 {img_count}개")

            if text_len < 3000: return True
            ko_count = len(re.findall(r'[가-힣]', full_text))
            if text_len > 0 and (ko_count / text_len) < 0.4: return True
            if img_count >= 5 and text_len < 3000: return True
            return False

    def extract_with_clova(self, file_path):
        with open(file_path, "rb") as f:
            # 파일을 바이너리로 읽어서 Base64 인코딩
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
        headers = {
            'X-OCR-SECRET': self.clova_secret,
            'Content-Type': 'application/json'
        }
        payload = {
            "version": "V2",
            "requestId": "guide_sample_id",
            "timestamp": 0,
            "images": [{"format": "pdf", "name": os.path.basename(file_path), "data": pdf_data}]
        }
        res = requests.post(self.clova_url, headers=headers, data=json.dumps(payload))
        if res.status_code == 200:
            result = res.json()
            all_texts = []
            for image_res in result.get('images', []):
                fields = image_res.get('fields', [])
                page_text = " ".join([f.get('inferText', '') for f in fields])
                if page_text.strip():
                    all_texts.append(page_text)
            final_text = "\n".join(all_texts)
            print(f"OCR 성공 - 추출된 글자 수: {len(final_text)}")
            return final_text
        else:
            print(f"OCR 에러: {res.status_code}")
            return ""

    def run(self, data_dir):
        all_docs = []
        pdf_files = [f for f in os.listdir(data_dir) if f.startswith("하나") and f.endswith(".pdf")]
        print(f" {len(pdf_files)}개의 PDF")

        for filename in pdf_files:
            file_path = os.path.join(data_dir, filename)
            with fitz.open(file_path) as doc:
                raw_text = "".join([p.get_text() for p in doc])

            if self.is_bad_quality(file_path):
                print(f"{filename}: 품질 낮음 -> CLOVA OCR 실행")
                raw_text = self.extract_with_clova(file_path)
            else:
                print(f"{filename}: 텍스트 추출 성공")

            card_name = filename.replace(".pdf", "").replace("_", " ")

            if "신용카드" in card_name:
                card_type = "신용카드"
            elif "체크카드" in card_name:
                card_type = "체크카드"
            else:
                card_type = "기타"
            
            metadata = {
                "card_name": card_name,
                "doc_type": "card_benefits",
                "card_type": card_type
            }
            enriched_text = f"# {card_name}\n\n" + raw_text
            all_docs.append(Document(text=enriched_text, metadata=metadata))

        if all_docs:
            nodes = self.splitter.get_nodes_from_documents(all_docs)
            for node in nodes:
                c_name = node.metadata.get("card_name", "unknown")
                node.text = f"[{c_name}] " + node.text

            #  Qdrant에 Dense + BM25 동시 저장
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=self.embed_model
            )
            print(f"완료: {len(nodes)}개 노드 저장 (Dense + BM25)")

if __name__ == "__main__":
    pipeline = CardRAGPipeline()
    pipeline.run("./data/card_pdf")