import os
import re
from dotenv import load_dotenv
from llama_parse import LlamaParse
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

# 1. .env 파일에서 LLAMA_CLOUD_API_KEY와 OPENAI_API_KEY를 가져옵니다.
load_dotenv()

class LlamaMultimodalParser:
    def __init__(self):
        # LlamaParse 설정: 멀티모달(GPT-4o) 모드 활성화
        self.parser = LlamaParse(
            result_type="markdown",  # 결과를 마크다운 표 형태로 받음
            num_workers=4,           # 병렬 처리 속도
            language="ko",           # 한국어 최적화
            use_vendor_multimodal_model=True,          # GPT-4o 같은 외부 모델 사용 설정
            vendor_multimodal_model_name="openai-gpt4o", # 이미지를 해석할 '눈' 역할
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            parsing_instruction="""
            이 파일은 한국어 신용카드 혜택 안내서입니다. 
            표(Table) 구조를 특히 신경 써서 마크다운 형식으로 복원해줘.
            이미지 안에 있는 글자나 로고 옆의 숫자도 놓치지 말고 텍스트로 변환해줘.모든 페이지 작은 글씨 하나도 놓치지마
            출력은 반드시 마크다운(#, ##, |---|) 형식을 유지해줘.
            """,
        )
        
        # 텍스트를 자를 도구 (512자 단위)
        self.splitter = SentenceSplitter(chunk_size=512, chunk_overlap=128)

    def run_test(self, file_path):
        print(f" [멀티모달 파싱 시작] {os.path.basename(file_path)}")
        
        # [Step 1] LlamaParse 호출 (이미지 -> GPT-4o 분석 -> 마크다운 텍스트)
        documents = self.parser.load_data(file_path)
        
        final_nodes = []
        
        for doc in documents:
            # 파일명에서 카드 이름 추출 (맥락 주입용)
            filename = os.path.basename(file_path)
            card_name = filename.replace(".pdf", "").replace("_", " ")
            
            # [Step 2] 마크다운 본문 앞에 카드 이름 박기
            enriched_text = f"# {card_name}\n\n" + doc.get_content()
            
            # LlamaIndex Document 객체 생성
            new_doc = Document(text=enriched_text, metadata={"filename": filename})
            
            # [Step 3] 512자 단위로 노드 쪼개기
            nodes = self.splitter.get_nodes_from_documents([new_doc])
            
            # [Step 4] 모든 노드 상단에 [카드명] 한 번 더 박기 (가영님 아이디어 반영)
            for node in nodes:
                node.text = f"[{card_name}] " + node.text
                final_nodes.append(node)
        
        return final_nodes

if __name__ == "__main__":
    TEST_FILE = "./data/card_pdf/하나_트래블로그_신용.pdf"
    
    if not os.path.exists(TEST_FILE):
        print(f" 파일을 찾을 수 없습니다: {TEST_FILE}")
    else:
        tester = LlamaMultimodalParser()
        nodes = tester.run_test(TEST_FILE)
        
        print("\n" + "="*60)
        print(f" 파싱 완료! 총 {len(nodes)}개의 노드가 생성되었습니다.")
        print("="*60)
        
        # [수정] 모든 노드를 하나씩 꺼내서 전체 내용을 출력합니다.
        for i, node in enumerate(nodes):
            print(f"\n [노드 {i}] 상세 내용:")
            print("-" * 50)
            # 노드의 실제 텍스트 내용을 출력
            print(node.get_content())
            
            # 메타데이터도 잘 들어갔는지 확인하고 싶다면 아래 주석 해제
            # print(f"🔗 메타데이터: {node.metadata}") 
            print("-" * 50)

        print("\n 모든 노드 출력이 완료되었습니다.")