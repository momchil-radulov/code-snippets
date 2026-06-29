# xdg-open Cheat Sheet

`xdg-open` отваря файл, директория или URL с програмата по подразбиране.

---

## Основен синтаксис

```bash
xdg-open <файл|директория|URL>
```

---

## Отваряне на файл

```bash
xdg-open document.pdf
```

Отваря PDF-а с програмата по подразбиране.

---

## Отваряне на изображение

```bash
xdg-open image.png
```

---

## Отваряне на HTML

```bash
xdg-open index.html
```

Ще отвори страницата в браузъра.

---

## Отваряне на директория

```bash
xdg-open .
```

или

```bash
xdg-open ~/Downloads
```

Отваря файловия мениджър.

---

## Отваряне на URL

```bash
xdg-open https://google.com
```

или

```bash
xdg-open https://kemsa.net
```

Отваря браузъра.

---

## mailto

```bash
xdg-open "mailto:test@example.com"
```

Отваря email клиента.

---

## Телефонен номер

```bash
xdg-open "tel:+359888123456"
```

Ако има регистрирано приложение.

---

## Google Maps

```bash
xdg-open "https://maps.google.com/?q=42.6977,23.3219"
```

---

## Отваряне на първия намерен файл

```bash
xdg-open "$(find . -name '*.pdf' | head -n1)"
```

или

```bash
find . -name "*.pdf" -exec xdg-open {} \; -quit
```

---

## Отваряне на всички PDF файлове

```bash
find . -name "*.pdf" -print0 | xargs -0 -n1 xdg-open
```

⚠ Това ще отвори много прозорци.

---

## Отваряне на текущата директория

```bash
xdg-open .
```

Еквивалентно на двойно щракване върху папката.

---

## Проверка дали съществува

```bash
which xdg-open
```

или

```bash
command -v xdg-open
```

---

## Помощ

```bash
xdg-open --help
```

---

# Как работи?

```
Файл
   │
   ▼
xdg-open
   │
   ▼
XDG MIME Database
   │
   ▼
Приложението по подразбиране
```

Например:

```
.pdf  → Evince / Okular
.html → Firefox / Chrome
.png  → Image Viewer
.mp3  → VLC
```

---

# Често срещани грешки

## ❌ Не приема повече от един аргумент

Няма да работи:

```bash
xdg-open file1 file2
```

Ще получиш:

```
xdg-open: unexpected argument
```

---

## За множество файлове

```bash
find . -print0 | xargs -0 -n1 xdg-open
```

или

```bash
find . -exec xdg-open {} \;
```

---

# Полезни комбинации

Отвори README:

```bash
find . -name README.md -exec xdg-open {} \; -quit
```

Отвори първия PDF:

```bash
find . -name "*.pdf" -exec xdg-open {} \; -quit
```

Отвори лог:

```bash
xdg-open logfile.txt
```

Отвори текущия проект:

```bash
xdg-open .
```

Отвори документация:

```bash
xdg-open docs/index.html
```

---

# Сродни команди

```bash
gio open
```

```bash
gnome-open    # остаряло
```

```bash
kde-open      # KDE
```

```bash
exo-open      # XFCE
```

# 💡 Малък трик, който често използвам: ако пишеш скриптове, вместо да проверяваш дали потребителят е с GNOME, KDE или XFCE, просто използвай:
```bash
xdg-open "$FILE"
```

`xdg-open` е стандартният и най-преносимият вариант за повечето Linux дистрибуции.
