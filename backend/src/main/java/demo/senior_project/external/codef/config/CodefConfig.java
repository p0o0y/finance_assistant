package demo.senior_project.external.codef.config;

import io.codef.api.EasyCodef;
import io.codef.api.EasyCodefUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class CodefConfig {

    private final Codefproperties codefproperties;

    @Bean
    public EasyCodef easyCodef(){
        EasyCodef easyCodef = new EasyCodef();

        easyCodef.setClientInfoForDemo(
                codefproperties.getClientId(),
                codefproperties.getClientSecret()
        );
        easyCodef.setPublicKey(codefproperties.getPublicKey());

        return easyCodef;
    }

    @Bean
    public EasyCodefUtil easyCodefUtil() {
        return new EasyCodefUtil();
    }
}
