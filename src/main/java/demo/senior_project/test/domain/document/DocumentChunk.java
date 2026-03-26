package demo.senior_project.test.domain.document;

import jakarta.persistence.*;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Array;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDate;
import java.time.LocalDateTime;


/**
 * 금융 약관 문서 청크 엔티티
 * 하나의 테이블로 여러 금융사 약관을 모두 관리.
 * 별도 Document 엔티티 없이 메타데이터 컬럼으로 구분.
 *
 * 지원 문서 예시:
 *   - 신한카드 이용약관 (doc_type=CARD,    institution=신한카드)
 *   - KB국민은행 약관   (doc_type=BANKING,  institution=KB국민은행)
 *   - 삼성증권 약관     (doc_type=STOCK,    institution=삼성증권)
 *   - 카카오페이 약관   (doc_type=FINTECH,  institution=카카오페이)
 */
@Entity
@Getter
@NoArgsConstructor
@Table(name = "document_chunks", indexes = {
        @Index(name = "idx_doc_type",    columnList = "doc_type"),
        @Index(name = "idx_category",    columnList = "category"),
        @Index(name = "idx_institution", columnList = "institution")
})
public class DocumentChunk {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 원본 파일 정보
    @Column(name = "doc_name", nullable = false)
    private String docName;         // 파일명: "신한카드_이용약관_2024.pdf"
    @Column(name = "chunk_index", nullable = false)
    private Integer chunkIndex;     // 문서 내 청크 순번
    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;      // 실제 약관 텍스트 (BM25 검색에도 사용)

    // ── pgvector 임베딩 ─────────────────────────────────────────
    @Column(name = "embedding", columnDefinition = "vector(1536)")
    @JdbcTypeCode(SqlTypes.VECTOR)
    @Array(length = 1536)
    private float[] embedding;      // Contextual Embedding 결과

    // ── Metadata (Retrieval 시 필터링용) ────────────────────────
    @Enumerated(EnumType.STRING)
    @Column(name = "doc_type", length = 20)
    private DocType docType;        // CARD / BANKING / STOCK / FINTECH / INSURANCE

    @Column(name = "category", length = 100)
    private String category;        // "이자율", "연체", "해지", "수수료", "분실신고"

    @Column(name = "institution", length = 100)
    private String institution;     // "신한카드", "KB국민은행", "삼성증권"

    @Column(name = "source_date")
    private LocalDate sourceDate;   // 약관 기준일 (최신 약관 우선 검색 시 사용)

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    // ── DocType 열거형 ──────────────────────────────────────────
    public enum DocType {
        CARD,       // 카드사
        BANKING,    // 은행
        STOCK,      // 증권
        FINTECH,    // 핀테크 (카카오페이 등)
        INSURANCE   // 보험
    }

    @Builder
    public DocumentChunk(String docName, Integer chunkIndex, String content,
                         float[] embedding, DocType docType, String category,
                         String institution, LocalDate sourceDate) {
        this.docName      = docName;
        this.chunkIndex   = chunkIndex;
        this.content      = content;
        this.embedding    = embedding;
        this.docType      = docType;
        this.category     = category;
        this.institution  = institution;
        this.sourceDate   = sourceDate;
        this.createdAt    = LocalDateTime.now();
    }
}