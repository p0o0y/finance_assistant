package demo.senior_project.external.codef.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import java.util.Map;

@Getter
@Component
@ConfigurationProperties(prefix = "app.codef")
//@ConfigurationProperties 외부값 주입 -> setter 필요
@Setter
public class Codefproperties {
    private String clientId;
    private String clientSecret;
    private String publicKey;
    private String domain;
    private Map<String, String> path;
}


