import os
import re
from llama_index.core import Document, StorageContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_parse import LlamaParse
from config import vector_store
# 모델 선정 BGE-M3
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")

parser = LlamaParse(
    result_type="markdown",
    num_workers=4,
    language="ko",
    use_vendor_multimodal_model=True,
    vendor_multimodal_model_name="openai-gpt4o",
    parsing_instruction="""
   Korean financial credit card benefit guide. Critical requirements:
    1. Extract ALL text including:
       - Table contents (preserve column/row structure in markdown tables)
       - Fine print and footnotes (유의사항)
       - Image-embedded text (OCR required)
    2. Structure:
       - Use # for main card name
       - Use ## for benefit categories (할인/적립/부가서비스)
       - Use ### for subcategories
    3. Preserve:
       - Percentage values (5%, 10% 등)
       - Merchant names (스타벅스, GS25 등)
       - Conditions (전월실적, 할인한도 등)
    4. Clean output:
       - Remove decorative elements
       - Convert non-UTF8 symbols to Korean equivalents
       - Maintain semantic paragraph breaks
    """,
    verbose=True
)

md_parser = MarkdownNodeParser.from_defaults(
    include_metadata=True,
    include_prev_next_rel=True
)
from llama_index.core.node_parser import SentenceSplitter
sentence_splitter = SentenceSplitter(
    chunk_size=512,  # 토큰 기준 (BGE-M3 최적)
    chunk_overlap=128,  # 문맥 보존
    separator=" ",
    paragraph_separator="\n\n"
)

def extract_card_metadata(filename):
    base = filename.replace(".pdf", "")
    parts = base.split("_")
    
    return {
        "card_company": parts[0] if len(parts) > 0 else "Unknown",
        "card_name": parts[1] if len(parts) > 1 else "Unknown",
        "card_type": parts[2] if len(parts) > 2 else "일반",
        "source_file": filename
    }

def clean_text(text):
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ0-9%.,!?()[\]{}:;""''·※\-/]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_perfect_nodes(data_dir):
    all_documents = []
    
    for filename in os.listdir(data_dir):
        if not filename.endswith(".pdf"):
            continue
            
        file_path = os.path.join(data_dir, filename)
        metadata = extract_card_metadata(filename)
        
        print(f"📄 Processing: {filename}")
        
        try:
            #LlamaParse → Markdown
            parsed_docs = parser.load_data(file_path)
            
            for doc in parsed_docs:
                raw_text = doc.get_content()
                
                # Step 2: 텍스트 정제
                clean_content = clean_text(raw_text)
                
                if len(clean_content) < 50:  # 너무 짧은 노드 스킵
                    print(f"  Skipping empty/short content in {filename}")
                    continue
                
                # Step 3: 메타데이터 주입 (청킹 전)
                prefix = (
                    f"# {metadata['card_company']} {metadata['card_name']} {metadata['card_type']}\n\n"
                )
                enriched_content = prefix + clean_content
                
                # Step 4: Document 객체 생성 (메타데이터 포함)
                new_doc = Document(
                    text=enriched_content,
                    metadata=metadata,
                    excluded_embed_metadata_keys=[],  # 모든 메타데이터 임베딩에 포함
                    excluded_llm_metadata_keys=[]
                )
                
                all_documents.append(new_doc)
                
        except Exception as e:
            print(f" Error parsing {filename}: {str(e)}")
            continue
    
    # Step 5: 통합 청킹 (일관된 크기)
    print(f"\n🔪 Chunking {len(all_documents)} documents")
    all_nodes = sentence_splitter.get_nodes_from_documents(
        all_documents,
        show_progress=True
    )
    
    print(f" Generated {len(all_nodes)} nodes")
    return all_nodes


# 실행
print(" 구형 데이터는 잊으세요. 프리미엄 인덱싱 시작!")
final_nodes = get_perfect_nodes("./data/card")

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex(
    final_nodes, 
    storage_context=storage_context, 
    embed_model=embed_model,
    show_progress=True
)
print(" [성공] 모든 데이터가 고화질 마크다운 노드로 교체되었습니다!")