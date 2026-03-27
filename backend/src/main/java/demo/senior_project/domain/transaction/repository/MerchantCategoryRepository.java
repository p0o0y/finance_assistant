package demo.senior_project.domain.transaction.repository;

import demo.senior_project.domain.transaction.domain.entity.MerchantCategory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MerchantCategoryRepository extends JpaRepository<MerchantCategory,Long> {
    Optional<MerchantCategory> findByBizNoAndStoreName(String bizNo , String storeName);
    // 가맹점 정보 한꺼번에
    @Query("SELECT m FROM MerchantCategory m WHERE m.bizNo IN :bizNos AND m.storeName IN :storeNames")
    List<MerchantCategory> findAllByBizNoInAndStoreNameIn(
            @Param("bizNos") List<String> bizNos,
            @Param("storeNames") List<String> storeNames
    );
}
