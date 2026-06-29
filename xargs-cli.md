# xargs Cheat Sheet

`xargs` взима вход от `stdin` и го превръща в аргументи на друга команда.

---

## Най-прост пример

```bash
echo file.txt | xargs ls -l
```

Реално изпълнява:

```bash
ls -l file.txt
```

---

## С `find`

```bash
find . -name "*.py" | xargs pylint
```

Реално:

```bash
pylint file1.py file2.py file3.py ...
```

---

## По един файл наведнъж

```bash
find . -name "*.py" | xargs -n1 pylint
```

Реално:

```bash
pylint file1.py
pylint file2.py
pylint file3.py
```

---

## Заместващ символ (-I)

```bash
find . -name "*.py" | xargs -I{} echo "Processing {}"
```

Реално:

```bash
echo "Processing file1.py"
echo "Processing file2.py"
```

Може да използваш всякакъв заместител:

```bash
xargs -I%
xargs -IFILE
xargs -I@
```

---

## Имена с интервали (важно!)

❌ Не винаги е безопасно:

```bash
find . | xargs rm
```

✅ Безопасният вариант:

```bash
find . -print0 | xargs -0 rm
```

---

## Ограничаване на броя аргументи

По един:

```bash
xargs -n1
```

По два:

```bash
xargs -n2
```

Пример:

```bash
echo "1 2 3 4 5 6" | xargs -n2
```

Изпълнява:

```
cmd 1 2
cmd 3 4
cmd 5 6
```

---

## Само показване (debug)

```bash
find . | xargs echo
```

или

```bash
find . | xargs -I{} echo "-> {}"
```

---

## Стартиране на команда за всеки файл

```bash
find . -name "*.jpg" | xargs -n1 xdg-open
```

или

```bash
find . -exec xdg-open {} \;
```

---

## Полезни комбинации

Форматиране:

```bash
find . -name "*.py" | xargs black
```

Lint:

```bash
find . -name "*.py" | xargs pylint
```

Изтриване:

```bash
find . -name "*.tmp" -print0 | xargs -0 rm
```

Размер:

```bash
find . -type f | xargs du -sh
```

---

## Най-полезните опции

| Опция | Значение |
|--------|----------|
| `-0` | Чете NUL (`\0`) вместо newline |
| `-n1` | По един аргумент |
| `-nN` | По N аргумента |
| `-I{}` | Замества `{}` с текущия аргумент |
| `-P4` | 4 паралелни процеса |
| `-r` | Не изпълнява нищо при празен вход (GNU xargs) |

---

## xargs или find -exec?

Когато командата приема много аргументи наведнъж:

```bash
find . -name "*.py" | xargs pylint
```

Когато трябва да се изпълнява по веднъж за всеки файл:

```bash
find . -exec xdg-open {} \;
```

или

```bash
find . | xargs -n1 xdg-open
```
