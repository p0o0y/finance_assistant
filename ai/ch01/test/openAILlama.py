import os
from dotenv import load_dotenv

# LlamaIndex 핵심 컴포넌트
from llama_parse import LlamaParse
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter

# .env 로드
load_dotenv()

class CardRAGPipeline:
    def __init__(self):
        # 1. 임베딩 모델 설정
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        
       
        self.parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            result_type="markdown", 
            num_workers=4,
            language="ko",
            use_vendor_multimodal_model=True,
            vendor_multimodal_model_name="openai-gpt4o",
            parsing_instruction="""
            이 문서는 카드 상품 안내서입니다. 
    1. 텍스트 추출 시 생략 없이 문서의 모든 정보를 상세히 기술하세요.
    2. 모든 표(Table)는 마크다운 형식을 유지하며 데이터 누락 없이 변환하세요.
    3. 유의사항 및 각주(Footnotes)에 포함된 세부 기호와 텍스트를 모두 포함해 주세요.
    """
        )
        
    
        self.vector_store = PGVectorStore.from_params(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            database=os.getenv("DB_NAME", "finance_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "1111"),
            table_name="financial_knowledge",
            embed_dim=1024
        )
    def run(self, data_dir):
        all_docs = []
        pdf_files = [f for f in os.listdir(data_dir) if f.startswith("신한_SOL") and f.endswith(".pdf")]
        
        if not pdf_files:
            print("❌ 처리할 PDF 파일이 없습니다.")
            return

        print(f"총 {len(pdf_files)}개의 PDF 분석 ")

        for filename in pdf_files:
            file_path = os.path.join(data_dir, filename)
            
            # LlamaParse 실행
            documents = self.parser.load_data(file_path)
            card_name = filename.replace(".pdf", "").replace("_", " ")
            
            for doc in documents:
                doc.metadata.update({
                    "filename": filename,
                    "card_name": card_name,
                    "doc_type": "card_benefits"
                })
                # set_content로 내용 수정 (에러 방지)
                doc.set_content(f"# {card_name}\n\n" + doc.get_content())
                all_docs.append(doc)

        if all_docs:
            print(f" 노드 분할 및 구조화 시작...")
            md_parser = MarkdownNodeParser()
            base_nodes = md_parser.get_nodes_from_documents(all_docs)
            
            recursive_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
            final_nodes = recursive_splitter.get_nodes_from_documents(base_nodes)

            for node in final_nodes:
                c_name = node.metadata.get("card_name", "unknown")
                # 노드별 컨텍스트 주입
                node.set_content("⚠️⚠️"+f"[{c_name}] " + node.get_content())

            print(f" DB 저장...")
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            VectorStoreIndex(
                final_nodes, 
                storage_context=storage_context, 
                embed_model=self.embed_model,
                show_progress=True
            )
            print(f" 총 {len(final_nodes)}개의 노드가 저장.")

if __name__ == "__main__":
    DATA_PATH = "./data/card_pdf"
    pipeline = CardRAGPipeline()
    pipeline.run(DATA_PATH)