package demo.senior_project.domain.report.batch;

import demo.senior_project.domain.report.ConsumptionReport;
import demo.senior_project.domain.report.ConsumptionReportRepository;
import demo.senior_project.domain.report.dto.UserYearMonth;
import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jspecify.annotations.Nullable;
import org.springframework.batch.infrastructure.item.ItemReader;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class UserItemReader implements ItemReader<UserYearMonth> {
    private final UserRepository userRepository;
    private final ConsumptionReportRepository consumptionReportRepository;

    private Queue<UserYearMonth> queue;
    //read 호출마다 poll로 한 개씩 꺼내기
    public void reset(){
        this.queue = null;
    }

    @Override
    public UserYearMonth read() throws Exception {
        if(queue==null){
            queue = new ArrayDeque<>();

            List<String> allMonths = new ArrayList<>();
            LocalDate now = LocalDate.now();
            for(int i=12;i>=1;i--){
                allMonths.add(now.minusMonths(i).format(DateTimeFormatter.ofPattern("yyyy-MM")));
            }
            log.info("[reader]처리 대상 월 :{} ",allMonths);

            // 페이징 조회
            int userPage =0;
            int userSize=100;


            while(true){
                Page<User> page = userRepository.findAll(
                        PageRequest.of(userPage,userSize)
                );

                for(User user : page.getContent()){
                    Set<String> existingMonths = consumptionReportRepository
                            .findByUser(user)
                            .stream()
                            .map(ConsumptionReport::getYearMonth)
                            .collect(Collectors.toSet());
                    for (String yearMonth : allMonths) {
                        if (!existingMonths.contains(yearMonth)) {
                            queue.add(new UserYearMonth(user, yearMonth));
                        }
                    }
                }

                if(!page.hasNext()) break;
                userPage++;
            }
        }
        //큐에서 1개씩 꺼내서 processor 전달
        return queue.isEmpty() ? null : queue.poll();
    }
}
