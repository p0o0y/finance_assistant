package demo.senior_project.global.security.jwt;


import demo.senior_project.domain.user.domain.User;
import demo.senior_project.domain.user.repository.UserRepository;
import demo.senior_project.global.security.oauth.CustomOauth2User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import lombok.Data;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;
import io.jsonwebtoken.security.Keys;
import java.security.Key;
import java.util.Collections;
import java.util.Date;

@Component
public class JwtTokenProvider {
    private final Key secretKey;
    private final long accessTokenValidity;
    private final UserRepository userRepository;

    public JwtTokenProvider(
        @Value("${app.jwt.secret}") String secret,
        @Value("${app.jwt.access.token.validity.seconds}") long validitySeconds,
        UserRepository userRepository
        )
    {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes());
        this.accessTokenValidity = validitySeconds * 1000;
        this.userRepository=userRepository;
    }

    public String createAccessToken(Long userId){
        Date now = new Date();
        Date expiry = new Date(now.getTime()+accessTokenValidity);

        return Jwts.builder()
                .setSubject(String.valueOf(userId))
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(secretKey, SignatureAlgorithm.HS256)
                .compact();
    }

    //jwt -> authntication
    public Authentication getAuthentication(String token) {
        // 1. JWT 파싱
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(secretKey)
                .build()
                .parseClaimsJws(token)
                .getBody();

        // 2. userId 추출
        Integer userId = Integer.parseInt(claims.getSubject());

        // 3. DB 조회 (핵심)
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // 4. Principal 생성
        CustomOauth2User principal =
                new CustomOauth2User(user, Collections.emptyMap());

        // 5. Authentication 생성
        return new UsernamePasswordAuthenticationToken(
                principal,
                null,
                principal.getAuthorities()
        );
    }



    public boolean validate(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(secretKey)
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
