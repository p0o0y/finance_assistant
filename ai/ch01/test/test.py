import time
import os

# 이 설정을 넣으면 다운로드 진행 상황이 터미널에 보일 수도 있습니다.
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

print(" [1/3] 라이브러리 로딩 중...")
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

print(" [2/3] BGE-M3 모델 연결 중... (첫 실행 시 수 분이 소요됩니다)")
start_time = time.time()

try:
   # timeout을 넉넉히 , 스트리밍으로 한 글자씩 받기
    llm = OllamaLLM(model="qwen2.5:1.5b", temperature=0)

  # 수정 후
    print(" AI 답변 생성 중: ", end="", flush=True)
    for chunk in llm.stream("고양이와 강아지 비교해줘"):
        print(chunk, end="", flush=True) # 한 글자씩 옆으로 붙어서 나옵니다.
    print("\n") # 다 끝나면 줄바꿈

except Exception as e:
    print(f"\n 에러 발생: {e}")

print(f"\n 총 실행 시간: {time.time() - start_time:.2f}초")