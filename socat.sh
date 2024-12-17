see: https://www.volkerschatz.com/net/socatproc.html
# http traffic
socat -v tcp-listen:80,reuseaddr tcp:some_domain.com:80
in /etc/hosts insert: "127.0.0.1 some_domain.com"
# smtp traffic
socat -v tcp-listen:25,reuseaddr tcp:your-smtp-server.foo:25
