see: https://www.volkerschatz.com/net/socatproc.html
### socat ###
# http traffic
socat -v tcp-listen:80,reuseaddr tcp:some_domain.com:80
in /etc/hosts insert: "127.0.0.1 some_domain.com"
# smtp traffic
socat -v tcp-listen:25,reuseaddr tcp:your-smtp-server.foo:25

### Reverse SSH Tunnel ###
see: tailscale.com
От вътрешния Linux компютър създай reverse SSH tunnel
ssh -R 2222:localhost:22 user@vps_server_ip
От друг компютър се свържи към VPS сървъра и оттам достъпи твоя Linux компютър
ssh -p 2222 localhost
