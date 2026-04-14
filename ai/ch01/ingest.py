import os
import re
from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
import json       
import base64    
from networkx import nodes
import requests   
import fitz         

import pickle

from utils.config import Config

# .env 로드
load_dotenv()
config = Config()
class CardRAGPipeline:
    def __init__(self):
        self.clova_url =os.getenv("NAVER_OCR_URL")
        self.clova_secret = os.getenv("NAVER_OCR_SECRET")
        
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        
        self.vector_store = PGVectorStore.from_params(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            table_name="financial_knowledge",
            embed_dim=1024,
            hybrid_search=True,
            text_search_config="simple",
            perform_setup=True
        )

    def is_bad_quality(self, file_path):
        with fitz.open(file_path) as doc:
            full_text = "".join([page.get_text() for page in doc])
            img_count = sum([len(page.get_images()) for page in doc])
            
            text_len = len(full_text.strip())
            print(f" {os.path.basename(file_path)}: 글자수 {text_len}, 이미지 {img_count}개")
        
            if text_len < 1000: return True
            ko_count = len(re.findall(r'[가-힣]', full_text))
            if text_len > 0 and (ko_count / text_len) < 0.2: return True
            if img_count >= 2 and text_len < 3000: return True

            return False
        
    def extract_with_clova(self, file_path):
        # 파일을 바이너리로 읽어서 Base64 인코딩
        with open(file_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
        
        headers = {'X-OCR-SECRET': self.clova_secret,'Content-Type': 'application/json'}
        
        payload = {
            "version": "V2",
            "requestId": "guide_sample_id", 
            "timestamp": 0,
            "images": [{"format": "pdf","name": os.path.basename(file_path),"data": pdf_data}]
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
            print(f" OCR 성공 -  추출된 글자 수: {len(final_text)}")
            return final_text
        else:
            print(f" OCR 에러: {res.status_code}, 내용: {res.text}")
            return ""


    def run(self, data_dir):
        all_docs = []
        pdf_files = [f for f in os.listdir(data_dir) if f.startswith("") and f.endswith(".pdf")]
        print(f" 총 {len(pdf_files)}개의 PDF")

        for filename in pdf_files:
            file_path = os.path.join(data_dir, filename)
            # 1. 무료 추출 
            with fitz.open(file_path) as doc_free:
                raw_text = "".join([p.get_text() for p in doc_free])  
            # 2. 품질 체크 
            if self.is_bad_quality(file_path): 
                print(f" {filename}: 품질 낮음 -> ✔️ CLOVA OCR 실행")
                raw_text = self.extract_with_clova(file_path)
            else:
                print(f"{filename}: 무료 추출 성공")
            
            card_name =filename.replace(".pdf", "").replace("_", " ")
            metadata = {"filename": filename, "card_name": card_name ,"doc_type": "card_benefits"}
            enriched_text = f"# {card_name}\n\n" + raw_text
            
            all_docs.append(Document(text=enriched_text, metadata=metadata))

        # 3. 인덱싱
        if all_docs:
            nodes = self.splitter.get_nodes_from_documents(all_docs) # 문서를 512자 node로 쪼개기 
            
            for node in nodes:
                c_name = node.metadata.get("card_name", "unknown")
                node.text=f"[{c_name}] "+node.text # 카드명 붙이기

            # 노드 저장 (BM25 전용)
            with open("./ch01/data/nodes.pkl", "wb") as f:
                pickle.dump(nodes, f)
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

            VectorStoreIndex(nodes, storage_context=storage_context, embed_model=self.embed_model)
            print(f" 완료 {len(nodes)}개 노드 저장됨.")

if __name__ == "__main__":
    pipeline = CardRAGPipeline()
    pipeline.run("./ch01/data/card_pdf")