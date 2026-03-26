package demo.senior_project.global.security.config;

import demo.senior_project.domain.user.domain.User;
import demo.senior_project.global.security.jwt.JwtAuthenticationFilter;
import demo.senior_project.global.security.oauth.CustomOauth2User;
import demo.senior_project.global.security.oauth.OAuthSuccessHandler;
import demo.senior_project.global.security.service.CustomOAuth2UserService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.client.web.OAuth2LoginAuthenticationFilter;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.authentication.logout.LogoutFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final CustomOAuth2UserService customOAuth2UserService;
    private final OAuthSuccessHandler oAuthSuccessHandler;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.cors(corsCustomizer -> corsCustomizer.configurationSource(new CorsConfigurationSource() {
            @Override
            public CorsConfiguration getCorsConfiguration(HttpServletRequest request) {
                CorsConfiguration configuration = new CorsConfiguration();
                configuration.setAllowedOriginPatterns(List.of("*"));
                configuration.setAllowedMethods(List.of("*"));
                configuration.setAllowedHeaders(List.of("*"));
                configuration.setAllowCredentials(true);
//                configuration.setExposedHeaders(List.of("Set-Cookie", "Authorization"));
                configuration.setMaxAge(3600L);
                return configuration;
            }
        }));

        http.sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
        );
        http.securityContext(securityContext -> securityContext.requireExplicitSave(false));

        http.csrf(auth->auth.disable());
        http.formLogin(auth->auth.disable());
        http.httpBasic(auth->auth.disable());

//        http.
//                addFilterAfter(new JWTFilter(jwtUtil,userRepository,adminRepository), OAuth2LoginAuthenticationFilter.class);

        http.
                addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);


        //oAuth2 로그인

        http.
                oauth2Login((oauth2)->oauth2
                        .userInfoEndpoint((userInfoEndpointConfig)->userInfoEndpointConfig
                                .userService(customOAuth2UserService))
                        .successHandler(oAuthSuccessHandler)
                        .permitAll());

        //권한 설정
        http
                .authorizeHttpRequests(auth->auth
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers("/assets/**", "/favicon.ico", "/swagger-resources/**", "/swagger-ui.html", "/swagger-ui/**",
                                "/webjars/**", "/swagger/**","/api-docs/**","/images/logo.png","/v3/api-docs/**", "/actuator/**").permitAll()
                        .requestMatchers("/","/login","/join","/api/logout","/api/oauth2-jwt-header","/api/reissue","/api/categories/**","/api/home").permitAll()
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers(HttpMethod.GET,"/api").permitAll()
                        .requestMatchers("/api/admin/manage/login").permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .requestMatchers("/api/unregister").hasRole("USER")
                        .requestMatchers("/api/me").hasRole("USER")
                        .requestMatchers("/api/posts/**").hasRole("USER")
                        .requestMatchers("/api/notifications").hasRole("USER")
                        .requestMatchers(HttpMethod.GET, "/api/notifications/stream").authenticated()

                        .anyRequest().authenticated());

        return http.build();
    }
}
