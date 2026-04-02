import os
import re
from dotenv import load_dotenv
from llama_index.core import Document, StorageContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_parse import LlamaParse
import io          
import json       
import base64    
import requests   
import fitz       
from pdf2image import convert_from_path 

# .env 로드
load_dotenv()

class CardRAGPipeline:
    def __init__(self):
        self.clova_url = "https://y4j2yxz61k.apigw.ntruss.com/custom/v1/51446/408c1a246b9411b7f26a7263535c075be2fbf8390524b7f1e3fd625dad61d1a9/general"
        self.clova_secret = os.getenv("NAVER_OCR_SECRET")
        
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)
        
        self.vector_store = PGVectorStore.from_params(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            database=os.getenv("DB_NAME", "finance_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "1111"),
            table_name="financial_knowledge",
            embed_dim=1024
        )

    def is_bad_quality(self, file_path):
        # 파라미터를 text 대신 file_path로 받아서 직접 파일을 열어봅니다.
        with fitz.open(file_path) as doc:
            full_text = "".join([page.get_text() for page in doc])
            img_count = sum([len(page.get_images()) for page in doc])
            
            text_len = len(full_text.strip())
            print(f"📄 {os.path.basename(file_path)}: 글자수 {text_len}, 이미지 {img_count}개")

            # [수정 로직]
        
            if text_len < 1000: return True
            
            # 2. 한글 비중이 너무 낮으면(외계어) 탈락
            ko_count = len(re.findall(r'[가-힣]', full_text))
            if text_len > 0 and (ko_count / text_len) < 0.2: return True
            
            # 3. 이미지는 2개 이상인데 글자가적으면'이미지 리플렛'으로 간주
            if img_count >= 2 and text_len < 3000: return True

            return False
        
    def extract_with_clova(self, file_path):
        # 1. 파일을 바이너리로 읽어서 Base64 인코딩
        with open(file_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
        
        headers = {
            'X-OCR-SECRET': self.clova_secret,
            'Content-Type': 'application/json'
        }
        
        # 2. [핵심] 클로바 General OCR이 PDF를 받을 때 딱 좋아하는 포맷입니다.
        payload = {
            "version": "V2",
            "requestId": "guide_sample_id", # 아무 문자열이나 상관없음
            "timestamp": 0,
            "images": [
                {
                    "format": "pdf",  # PNG 대신 반드시 pdf
                    "name": os.path.basename(file_path),
                    "data": pdf_data
                }
            ]
        }

        # 3. 요청 보내기
        res = requests.post(self.clova_url, headers=headers, data=json.dumps(payload))
        
        if res.status_code == 200:
            result = res.json()
            all_texts = []
            
            # 4. [중요] PDF는 결과가 여러 '페이지(이미지)'로 옵니다. 다 합쳐야 해요!
            for image_res in result.get('images', []):
                fields = image_res.get('fields', [])
                # 한 페이지 내의 글자들 합치기
                page_text = " ".join([f.get('inferText', '') for f in fields])
                if page_text.strip():
                    all_texts.append(page_text)
            
            final_text = "\n".join(all_texts)
            print(f"🔍 OCR 성공! 추출된 글자 수: {len(final_text)}")
            return final_text
        else:
            # 에러 나면 이유를 출력해서 범인을 잡읍시다.
            print(f"❌ OCR 에러: {res.status_code}, 내용: {res.text}")
            return ""
    def run(self, data_dir):
        all_docs = []
        pdf_files = [f for f in os.listdir(data_dir) if f.startswith("하나") and f.endswith(".pdf")]
        print(f" 총 {len(pdf_files)}개의 PDF")

        for filename in pdf_files:
            file_path = os.path.join(data_dir, filename)
            
            # 1. 무료 추출 시도 (텍스트만 일단 슥 읽기)
            with fitz.open(file_path) as doc_free:
                raw_text = "".join([p.get_text() for p in doc_free])
            
            # 2. 품질 체크 (이제 raw_text 대신 file_path를 넘깁니다)
            if self.is_bad_quality(file_path): 
                print(f"💰 {filename}: 품질 낮음 -> CLOVA OCR 실행")
                raw_text = self.extract_with_clova(file_path)
            else:
                print(f"✅ {filename}: 무료 추출 성공")
            
            card_name =filename.replace(".pdf", "").replace("_", " ")
            metadata = {"filename": filename, "card_name": card_name}
           
            enriched_text = f"# {card_name}\n\n" + raw_text
            
            all_docs.append(Document(text=enriched_text, metadata=metadata))

        # 3. 인덱싱
        if all_docs:
            nodes = self.splitter.get_nodes_from_documents(all_docs) # 문서를 512자 node로 쪼개기 
            for node in nodes:
                c_name = node.metadata.get("card_name", "unknown")
                node.text=f"[{c_name}] "+node.text # 카드 이름을 텍스트 앞에 붙이기

            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

            VectorStoreIndex(nodes, storage_context=storage_context, embed_model=self.embed_model)
            print(f" 처리 완료 {len(nodes)}개 노드 저장됨.")

if __name__ == "__main__":
    pipeline = CardRAGPipeline()
    pipeline.run("./data/card_pdf")