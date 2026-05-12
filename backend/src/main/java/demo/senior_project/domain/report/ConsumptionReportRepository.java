package demo.senior_project.domain.report;

import demo.senior_project.domain.user.domain.User;
import org.apache.logging.log4j.simple.internal.SimpleProvider;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ConsumptionReportRepository extends JpaRepository<ConsumptionReport,Long>{
    List<ConsumptionReport> findTop3ByUserOrderByYearMonthDesc(User user);
    // Batch에서 이미 해당 월 리포트 있는지 중복 체크
    Optional<ConsumptionReport> findByUserAndYearMonth(User user, String yearMonth);

    List<ConsumptionReport> findByUser(User user);


}

