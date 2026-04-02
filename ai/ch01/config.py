import os
from dotenv import load_dotenv
# 1. 에러 해결: 필요한 클래스를 반드시 임포트해야 합니다.
from llama_index.vector_stores.postgres import PGVectorStore

# .env 파일 로드
load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5433")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "finance_db")
    DB_TABLE = os.getenv("DB_TABLE", "financial_knowledge")
    # env에서 읽어온 값은 문자열이므로 int로 변환 (값이 없을 경우 대비 1024 기본값)
    DB_EMBEDDING_DIM = int(os.getenv("DB_EMBEDDING_DIM", 1024))

    # LlamaCloud
    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

# 2. 에러 해결: Config 클래스를 '인스턴스화(객체 생성)' 해야 config.DB_HOST 처럼 쓸 수 있습니다.
config = Config()

# 3. 에러 해결: 이제 'config' 변수가 정의되었으므로 아래 코드가 작동합니다.
vector_store = PGVectorStore.from_params(
    host=config.DB_HOST,
    port=config.DB_PORT,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    database=config.DB_NAME,
    table_name=config.DB_TABLE,
    embed_dim=config.DB_EMBEDDING_DIM,
)