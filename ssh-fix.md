# SSH: диагностика на `No route to host` в Ubuntu/Linux

Практически наръчник за диагностика на SSH, маршрутизация, IPv4/IPv6, firewall и Fail2Ban.

## 1. Илюстративен пример (анонимизиран)

Изпълнена команда:

```bash
ssh ubuntu@ssh.example.com
```

Получена грешка:

```text
ssh: connect to host backend.example.com port 22: No route to host
```

Това е мрежова грешка преди SSH удостоверяването. Тя не означава автоматично, че в routing table липсва маршрут. Linux често показва този текст за `EHOSTUNREACH`; причината може да е и изричен ICMP отказ от firewall.

**Важно:** Името `backend.example.com` се различава от въведеното `ssh.example.com`. Проверете дали причината е SSH `HostName`, DNS/CNAME или друго преобразуване, вместо да приемате конкретна причина предварително.

## 2. Какво означават близките грешки

| Съобщение | Типично значение |
|---|---|
| `No route to host` | Хостът е недостижим; възможен ICMP отказ или проблем със съсед/маршрут. |
| `Network is unreachable` | Няма използваем маршрут до мрежата. |
| `Connection timed out` | Не е получен отговор в срока. |
| `Connection refused` | TCP връзката е активно отказана, например няма слушащ процес или firewall връща TCP RST. |
| `Permission denied` | Достигнат е SSH сървърът, но удостоверяването е отказано. |
| `Could not resolve hostname` | Проблем с разрешаването на името. |

Една и съща първопричина може да даде различни съобщения според конфигурацията на мрежата.

## 3. Проверете окончателната SSH конфигурация

```bash
ssh -G ssh.example.com | grep -Ei '^(hostname|user|port|proxyjump|proxycommand) '
```

`-G` отпечатва ефективната конфигурация, без да установява връзка. Проверете `~/.ssh/config`, системната конфигурация и правилата `Host`/`Match`, ако `hostname` е неочакван.

За подробен опит за свързване:

```bash
ssh -vvv -o ConnectTimeout=5 ubuntu@ssh.example.com
```

## 4. DNS и адреси

```bash
getent ahosts ssh.example.com
getent ahosts backend.example.com

dig ssh.example.com
dig ssh.example.com CNAME
```

`getent` използва системния механизъм за разрешаване на имена (включително `/etc/hosts` според конфигурацията), докато `dig` проверява DNS. Сравнете резултатите.

## 5. Маршрут и достижимост

Заменете `203.0.113.39` с действителния адрес на вашия сървър:

```bash
ip -4 route get 203.0.113.39
ip -4 route
ping -c 3 203.0.113.39
nc -vz -w 5 203.0.113.39 22
```

`ping` може да е блокиран дори при работещ SSH. `ip route get` показва локалния избор на маршрут, но не доказва достижимост до сървъра.

Проверка на IP версиите поотделно:

```bash
ssh -4 -vvv -o ConnectTimeout=5 ubuntu@ssh.example.com
ssh -6 -vvv -o ConnectTimeout=5 ubuntu@ssh.example.com
```

По желание:

```bash
tracepath 203.0.113.39
traceroute -T -p 22 203.0.113.39
```

## 6. Най-показателната проверка: tcpdump

В първи терминал:

```bash
sudo tcpdump -ni any 'tcp port 22 or icmp or icmp6'
```

Във втори:

```bash
ssh -o ConnectTimeout=5 ubuntu@ssh.example.com
```

Примерен, анонимизиран запис:

```text
Out IP 192.0.2.7.50544 > 203.0.113.39.22: Flags [S]
In  IP 203.0.113.39 > 192.0.2.7: ICMP host 203.0.113.39 unreachable - admin prohibited
```

**Тълкуване:** локалният компютър изпраща TCP SYN към порт 22, след което получава ICMP административна забрана. Това обяснява `No route to host` за конкретния IPv4 опит. Не доказва само по себе си кое устройство или кое правило е генерирало отказа. Възможни източници са firewall на сървъра, хостинг firewall или междинно устройство. Изходният IP в ICMP пакета не е достатъчен за окончателно установяване на източника.

В същия запис има и отделен IPv6 проблем:

```text
ICMP6, destination unreachable, unreachable route 2001:db8:1::40
```

Той показва недостижим IPv6 маршрут, но не обяснява сам по себе си IPv4 административната забрана. Диагностицирайте двата протокола отделно.

Ако се виждат само повтарящи се SYN пакети без отговор, по-вероятен е timeout. ICMP `admin prohibited` насочва към изрична мрежова забрана.

## 7. Проверете публичния си IPv4

```bash
curl -4 https://api.ipify.org; echo
```

В анонимизирания пример резултатът е `198.51.100.25`. Това е адресът, който може да се търси във firewall или списъците за блокиране на сървъра. При NAT, VPN или смяна на мрежата публичният IP може да се промени.

## 8. Проверки на отдалечения сървър

Изпълнявайте тези команди **на сървъра**, само ако имате достъп през друга SSH връзка или конзолата на хостинг доставчика.

Проверка дали SSH слуша:

```bash
sudo ss -lntp | grep -E ':(22|2222)\b'
sudo systemctl status ssh
```

Проверете действителния SSH порт в конфигурацията. Порт `2222` тук е само пример.

Firewall:

```bash
sudo ufw status verbose
sudo iptables -L INPUT -n -v --line-numbers
sudo iptables -S
sudo nft list ruleset
```

Търсене на конкретния публичен адрес:

```bash
sudo iptables -S | grep -F '198.51.100.25'
sudo nft list ruleset | grep -F '198.51.100.25'
```

**Внимание:** липсата на съвпадение не доказва, че IP адресът не е блокиран. Правилото може да е за цяла мрежа, ipset/nft set, порт или интерфейс, или да е във firewall на хостинг доставчика.

Fail2Ban (ако е инсталиран):

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd banip
```

Командите за jail `sshd` работят само ако такъв jail съществува. При някои версии опциите за показване на сроковете се различават; `status sshd` е удобна първа проверка.

Ако **потвърдите**, че IP адресът е блокиран в jail `sshd`, и имате административно разрешение:

```bash
sudo fail2ban-client set sshd unbanip 198.51.100.25
```

Тази команда не премахва забрани от други jail-ове, iptables/nftables или хостинг firewall. Не променяйте на сляпо firewall правилата, особено през единствената си активна SSH сесия.

## 9. Проверка през друга мрежа

Опитайте същата SSH команда през мобилен hotspot или друг интернет доставчик. Ако работи само от другата мрежа, това е силна индикация за IP-специфично блокиране или проблем по маршрута, **но не е окончателно доказателство**. Сравнете публичните IP адреси и `tcpdump` от двата опита.

## 10. Бърза последователност за диагностика

1. `ssh -G HOST` — проверете ефективните hostname, порт и proxy.
2. `getent ahosts HOST` — установете IPv4/IPv6 адресите.
3. `ssh -4 -vvv -o ConnectTimeout=5 USER@HOST` — изолирайте IPv4.
4. `ip -4 route get IP` — проверете локалния маршрут.
5. `nc -vz -w 5 IP PORT` — тествайте TCP порта.
6. `sudo tcpdump -ni any 'tcp port 22 or icmp or icmp6'` — вижте реалния отговор.
7. `curl -4 https://api.ipify.org; echo` — установете изходния публичен IP.
8. През конзола на сървъра проверете слушащия SSH, firewall, Fail2Ban и firewall на доставчика.
9. При нужда сравнете опит от друга мрежа.

## 11. Извод от анонимизирания пример

Наблюдаваното IPv4 събитие е **TCP SYN → ICMP host unreachable / admin prohibited** за `203.0.113.39:22`. Следва да се провери къде се генерира забраната и дали тя е специфична за публичния клиентски IP `198.51.100.25`. Отделно е отчетена IPv6 недостижимост. Нито един от тези записи не доказва проблем с SSH ключа или паролата.

---

*Наръчникът е изготвен по показаните в разговора команди и резултати. Всички хостове и IP адреси в примера са тестови: example.com, 203.0.113.0/24, 198.51.100.0/24, 192.0.2.0/24 и 2001:db8::/32. Заменете ги с реалните адреси при диагностика.*


## 12. Важни подробности за ICMP и TCP

- `ICMP destination unreachable / communication administratively prohibited` е активен отказ, но сам по себе си не установява кое правило или устройство го е изпратило. Сравнете трасето, firewall логовете и пакетите от двете страни.
- `SYN → SYN,ACK → ACK` означава установена TCP връзка; проблеми след това са в SSH протокола или удостоверяването.
- `SYN → RST` обикновено води до `Connection refused`.
- `SYN → повторни SYN без отговор` обикновено води до timeout.
- `ping` проверява ICMP echo, не SSH порт. Успешен ping не доказва отворен порт 22, а неуспешен ping не доказва недостъпен SSH.
- `tcpdump -i any` е удобен, но при по-сложни случаи посочете точния интерфейс, например `-i eth0`, и наблюдавайте двете страни.

## 13. Проверка на порт, интерфейс и SSH услуга

На сървъра (през конзола или друг работещ достъп):

```bash
sudo ss -lntp
sudo systemctl status ssh --no-pager
sudo journalctl -u ssh -n 100 --no-pager
sudo sshd -t
sudo sshd -T | grep -Ei '^(port|listenaddress|addressfamily|passwordauthentication|pubkeyauthentication) '
```

`sshd -t` проверява синтаксиса на конфигурацията. `sshd -T` показва ефективни стойности, но за правила `Match` може да е необходима опцията `-C` с подходящ контекст. На Ubuntu услугата обичайно е `ssh`, а не `sshd`. Не рестартирайте SSH, преди да проверите конфигурацията и да осигурите резервен достъп.

От клиента проверете и нетипичен порт, ако е конфигуриран:

```bash
ssh -G ssh.example.com | grep -E '^(hostname|port|user|addressfamily) '
nc -4 -vz -w 5 ssh.example.com 2222
ssh -4 -p 2222 -o ConnectTimeout=5 ubuntu@ssh.example.com
```

Порт `2222` е пример, не предположение за действителния сървър.

## 14. DNS, `/etc/hosts`, SSH aliases и ProxyJump

```bash
getent hosts ssh.example.com
getent ahostsv4 ssh.example.com
getent ahostsv6 ssh.example.com
dig +short A ssh.example.com
dig +short AAAA ssh.example.com
ssh -G ssh.example.com | grep -Ei '^(hostname|proxyjump|proxycommand|canonicalizehostname|port) '
```

Ако `getent` и `dig` се различават, проверете `/etc/hosts` и `/etc/nsswitch.conf`. Ако SSH се свързва с различно име, проверете `HostName`, `CanonicalizeHostname`, `ProxyJump` и `ProxyCommand` в `~/.ssh/config` и системните SSH конфигурации. Не променяйте `/etc/hosts` само за да заобиколите неясен проблем: така може да скриете неправилна DNS настройка.

## 15. Локален маршрут, ARP/NDP и VPN

```bash
ip -br address
ip -4 route
ip -6 route
ip -4 route get 203.0.113.39
ip neigh show
ip rule show
nmcli connection show --active
```

`ip route get` показва избрания локален маршрут, не гарантира, че пакетът ще достигне целта. Ако следващият hop е в локалната мрежа, проверете съседите с `ip neigh`: `FAILED` или `INCOMPLETE` може да сочи проблем с ARP/NDP. При VPN проверете интерфейса, маршрутизацията и policy rules; при split tunneling само част от трафика минава през тунела.

## 16. По-прецизен tcpdump и запазване на доказателства

```bash
# На клиента: само целевият IPv4 адрес, SSH порт и ICMP
sudo tcpdump -ni any -vv 'host 203.0.113.39 and (tcp port 22 or icmp)'

# Запис за анализ с Wireshark; файлът може да съдържа чувствителни метаданни
sudo tcpdump -ni any -s 0 -w ssh-diagnostic.pcap   'host 203.0.113.39 and (tcp port 22 or icmp)'
```

Спрете записа с `Ctrl+C`. Ако имате достъп до сървъра, пуснете паралелно capture и там: ако SYN пристига, но отговорът се губи, проблемът може да е по обратния маршрут. Ако SYN изобщо не пристига, проверете междинните устройства и хостинг firewall. Не публикувайте `.pcap` без преглед — може да разкрива адреси, хостове и други метаданни.

## 17. Firewall и Fail2Ban: безопасен подход

```bash
# На сървъра
sudo ufw status numbered
sudo nft -a list ruleset
sudo iptables -S
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo journalctl -u fail2ban -n 100 --no-pager
```

Проверете също хостинг firewall/security groups, правила за IPv4 и IPv6, мрежови списъци и други инструменти за блокиране. `grep` по един IP може да пропусне subnet, set или общо правило за порт. Отблокирайте адрес само след като установите точния източник на забраната и имате право да го направите. Запазете работеща конзола и резервна SSH сесия преди промени.

## 18. Кратък диагностичен скрипт (без промени по системата)

Запишете като `ssh-check.sh`, после изпълнете `bash ssh-check.sh ssh.example.com 22`:

```bash
#!/usr/bin/env bash
set -u

host="${1:-}"
port="${2:-22}"
if [[ -z "$host" || ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
  echo "Употреба: bash $0 HOST [PORT]" >&2
  exit 2
fi

printf '\n== SSH конфигурация ==\n'
ssh -G "$host" 2>&1 | grep -Ei '^(hostname|user|port|proxyjump|proxycommand) ' || true

printf '\n== DNS / NSS ==\n'
getent ahosts "$host" || true

printf '\n== IPv4 маршрут ==\n'
ipv4="$(getent ahostsv4 "$host" | awk 'NR == 1 {print $1}')"
if [[ -n "$ipv4" ]]; then
  ip -4 route get "$ipv4" || true
else
  echo 'Няма намерен IPv4 адрес.'
fi

printf '\n== TCP порт ==\n'
if command -v nc >/dev/null 2>&1; then
  nc -4 -vz -w 5 "$host" "$port" 2>&1 || true
else
  echo 'nc не е инсталиран (пакет netcat-openbsd).'
fi

printf '\n== SSH IPv4 диагностика ==\n'
ssh -4 -vv -p "$port" -o BatchMode=yes -o ConnectTimeout=5 \
  -o ConnectionAttempts=1 "$host" true 2>&1 | tail -n 35
```

Скриптът не редактира настройки и не изисква `sudo`. Използва `BatchMode=yes`, за да не иска интерактивно парола; възможен отказ при удостоверяване след успешна мрежова връзка е нормален и е отделен от мрежовите грешки. Използвайте само за системи, които имате право да тествате.

## 19. Бързо дърво за решения

```text
Името не се разрешава?
  → getent / dig / /etc/hosts / SSH HostName
Няма локален маршрут?
  → ip route / ip rule / VPN / gateway
SYN → ICMP admin prohibited?
  → firewall на сървър, доставчик или междинно устройство
SYN → RST?
  → портът е отказан; проверете sshd и firewall
SYN → няма отговор?
  → timeout; capture от двете страни, маршрути и филтри
TCP работи, но SSH отказва вход?
  → ssh -vvv, sshd логове, ключове, потребител и права
```

**Основен принцип:** първо установете дали проблемът е DNS, маршрут, TCP, SSH протокол или удостоверяване; чак след това променяйте конфигурацията.
