Да. Най-добре е да го разглеждаш като **цял жизнен цикъл на диска и данните**, а не само като няколко LVM команди.

Ще тръгна от **чист физически диск**, после ще стигнем до Linux + LVM, filesystem, mount, snapshot, backup върху външен носител, възстановяване на отделна папка и накрая как snapshot-ът се премахва.

## 1. Физическият диск

Имаме например празен диск:

```text
/dev/sdb
200 GB
```

Linux вижда физическото устройство като:

```bash
lsblk
```

например:

```text
sdb    8:16   0  200G  0 disk
```

В този момент това е просто блоково устройство. Няма:

* дялове;
* filesystem;
* LVM;
* директории;
* файлове.

Може да си го представиш така:

```text
ФИЗИЧЕСКИ ДИСК
/dev/sdb
┌─────────────────────────────────────┐
│              празно                 │
│              200 GB                 │
└─────────────────────────────────────┘
```

---

# 2. Правим partition table

Обикновено днес използваме GPT.

Например:

```bash
sudo fdisk /dev/sdb
```

или:

```bash
sudo parted /dev/sdb
```

След partitioning може да получиш нещо подобно:

```text
/dev/sdb
├── /dev/sdb1     1 GB
├── /dev/sdb2     2 GB
└── /dev/sdb3   197 GB
```

При Ubuntu често архитектурата е приблизително:

```text
sdb
├─sdb1       EFI
├─sdb2       /boot
└─sdb3       LVM
```

Точно нещо подобно имаш и ти:

```text
sdb
├─sdb1   1.1G
├─sdb2     2G
└─sdb3   197G
```

---

# 3. Защо `/boot` и EFI са отделни

Например:

```text
sdb1 → EFI System Partition
sdb2 → /boot
sdb3 → LVM
```

EFI дялът съдържа bootloader-а.

`/boot` съдържа неща като:

```text
vmlinuz-...
initrd.img-...
grub/
```

А основната Linux система може да бъде върху LVM.

Архитектура:

```text
Физически диск /dev/sdb
│
├── /dev/sdb1      EFI
│
├── /dev/sdb2      /boot
│
└── /dev/sdb3
       │
       └── LVM
```

---

# 4. `/dev/sdb3` става LVM Physical Volume

Тук започва истинският LVM.

Командата е:

```bash
sudo pvcreate /dev/sdb3
```

`PV` = **Physical Volume**.

След това:

```bash
sudo pvs
```

например:

```text
PV         VG      Fmt  Attr PSize
/dev/sdb3          lvm2 ---  197G
```

Това не означава, че имаме filesystem.

Просто казваме на LVM:

> Този физически дял може да бъде използван от LVM.

Схематично:

```text
/dev/sdb3
     │
     ▼
Physical Volume
     PV
```

---

# 5. Създаваме Volume Group

Следващото ниво е:

**VG — Volume Group**

Например:

```bash
sudo vgcreate ubuntu-vg /dev/sdb3
```

Получаваме:

```text
/dev/sdb3
   │
   ▼
PV
   │
   ▼
VG ubuntu-vg
```

Проверяваме:

```bash
sudo vgs
```

например:

```text
VG        #PV #LV VSize   VFree
ubuntu-vg   1   0 197.00g 197.00g
```

Volume Group можеш да си го представиш като **басейн с дисково пространство**.

```text
           ubuntu-vg
┌─────────────────────────────────────┐
│            197 GB pool              │
└─────────────────────────────────────┘
```

---

# 6. От Volume Group правим Logical Volume

Тук създаваме логическия "диск", който Linux после ще използва.

Например:

```bash
sudo lvcreate -L 160G -n ubuntu-lv ubuntu-vg
```

Получаваме:

```text
VG ubuntu-vg
┌─────────────────────────────────────┐
│                                     │
│ ubuntu-lv            free           │
│ 160 GB               37 GB          │
│ ███████████████████  ░░░░           │
└─────────────────────────────────────┘
```

Проверка:

```bash
sudo lvs
```

пример:

```text
LV        VG        Attr       LSize
ubuntu-lv ubuntu-vg -wi-a----- 160.00g
```

Logical Volume се появява като блоково устройство:

```text
/dev/ubuntu-vg/ubuntu-lv
```

и също като device mapper:

```text
/dev/mapper/ubuntu--vg-ubuntu--lv
```

Тези две имена сочат практически към едно и също устройство.

---

# 7. Все още няма filesystem

Това е много важно.

Имаме:

```text
physical disk
→ partition
→ PV
→ VG
→ LV
```

но още **нямаме ext4**.

Не можем просто да започнем да създаваме:

```text
/etc
/home
/var
```

Трябва filesystem.

Например:

```bash
sudo mkfs.ext4 /dev/ubuntu-vg/ubuntu-lv
```

Сега вече:

```text
Logical Volume
      │
      ▼
    ext4
```

---

# 8. Filesystem се mount-ва

Ако това е root filesystem, по време на boot Linux го mount-ва като:

```text
/
```

Тогава структурата става:

```text
/
├── bin
├── boot
├── dev
├── etc
├── home
├── root
├── usr
├── var
└── ...
```

Схематично:

```text
/dev/sdb
   │
   └── sdb3
        │
        ▼
       PV
        │
        ▼
       VG
        │
        ▼
   ubuntu-lv
        │
        ▼
       ext4
        │
        ▼
        /
```

Това е една от най-важните картинки за разбиране на Linux storage:

```text
PHYSICAL
=======================

Hard disk
/dev/sdb
   │
   ▼
Partition
/dev/sdb3

LVM
=======================

Physical Volume
PV
   │
   ▼
Volume Group
VG
   │
   ▼
Logical Volume
LV

FILESYSTEM
=======================

ext4
   │
   ▼
mount
   │
   ▼
/
├── etc
├── home
├── var
└── ...
```

---

# 9. Къде се появява snapshot-ът

Да кажем, че основният ти LV е:

```text
/dev/ubuntu-vg/ubuntu-lv
```

и съдържа:

```text
/
├── etc
├── home
│   └── momchil
├── var
│   ├── lib
│   └── www
└── ...
```

В 15:00 решаваш:

> Искам замразен изглед на файловата система към 15:00.

Създаваш snapshot.

Например:

```bash
sudo lvcreate \
    --snapshot \
    --size 20G \
    --name ubuntu-snapshot \
    /dev/ubuntu-vg/ubuntu-lv
```

Тогава имаме:

```text
                   ubuntu-vg
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
        ubuntu-lv          ubuntu-snapshot
        ORIGINAL              SNAPSHOT
```

Snapshot-ът представлява:

```text
състоянието на ubuntu-lv в 15:00
```

---

# 10. Snapshot не означава пълно физическо копие

Да кажем, че оригиналът е 160 GB.

Не означава:

```text
160 GB original
+
160 GB snapshot
=
320 GB
```

Класическият LVM snapshot използва **Copy-on-Write**.

В началото:

```text
Original:

[A][B][C][D][E][F]

Snapshot:
    използва оригиналните блокове
```

После оригиналът променя блок `C`.

Преди промяната LVM запазва старото `C` за snapshot-а:

```text
Original:

[A][B][X][D][E][F]
       ↑
    нов C
```

Snapshot знае:

```text
[A][B][C][D][E][F]
       ↑
     стар C
```

Затова snapshot-ът пази **старите версии на блоковете, които се променят**.

---

# 11. Snapshot ≠ backup

Това е фундаментално.

Snapshot:

```text
оригинален диск
        │
        ├── original LV
        │
        └── snapshot
```

Ако физическият диск:

```text
/dev/sdb
```

умре, може да загубиш едновременно:

```text
original
+
snapshot
```

Следователно:

> **Snapshot е инструмент за създаване на консистентно резервно копие, но самият snapshot не е достатъчно резервно копие.**

---

# 12. Защо snapshot е полезен за backup

Представи си, че копираш директно:

```bash
rsync /
```

Докато копирането върви:

```text
15:00   копира /etc
15:05   базата се променя
15:10   копира /var
15:20   копира /home
```

Backup-ът може да съдържа файлове от различни моменти.

При snapshot:

```text
15:00

Създаваме snapshot
        ↓
Състоянието е фиксирано
        ↓
Копираме спокойно 1 час
```

Всички файлове се виждат така, както са били към 15:00.

---

# 13. Mount-ваме snapshot-а

Например:

```bash
sudo mkdir -p /mnt/alfa-snapshot
```

После:

```bash
sudo mount -o ro \
    /dev/ubuntu-vg/ubuntu-snapshot \
    /mnt/alfa-snapshot
```

Добра идея е:

```text
-o ro
```

тоест read-only.

Сега:

```bash
ls /mnt/alfa-snapshot
```

може да даде:

```text
bin
boot
etc
home
lib
root
usr
var
...
```

Получил си втори изглед на root filesystem-а:

```text
/                       ← LIVE
/mnt/alfa-snapshot      ← frozen state
```

Например:

```text
/home/momchil/file.txt

/mnt/alfa-snapshot/home/momchil/file.txt
```

Първото е текущият файл.

Второто е версията от момента на snapshot-а.

---

# 14. Възстановяване на една папка

Това е много удобно.

Да кажем, че случайно си изтрил:

```text
/home/momchil/projects
```

Но snapshot-ът е от преди изтриването.

Проверяваш:

```bash
ls /mnt/alfa-snapshot/home/momchil/projects
```

И папката е там.

Можеш да я възстановиш например с:

```bash
rsync -aHAX \
    /mnt/alfa-snapshot/home/momchil/projects/ \
    /home/momchil/projects/
```

Това вече е **restore**.

---

# 15. Защо предпочитам rsync вместо cp

За системни backup-и:

```bash
rsync -aHAX
```

е много по-подходящо.

Опциите грубо означават:

```text
-a    archive
-H    hard links
-A    ACL
-X    extended attributes
```

Пример:

```bash
sudo rsync -aHAX \
    /mnt/alfa-snapshot/etc/nginx/ \
    /etc/nginx/
```

Възстановяваш `/etc/nginx`.

Но тук бих препоръчал първо:

```bash
sudo rsync -aHAXn \
    /mnt/alfa-snapshot/etc/nginx/ \
    /etc/nginx/
```

`-n` означава:

```text
dry-run
```

Тоест виждаш какво ще стане без промени.

След това:

```bash
sudo rsync -aHAX \
    /mnt/alfa-snapshot/etc/nginx/ \
    /etc/nginx/
```

---

# 16. Истински backup върху външен диск

Сега идва важната част.

Имаме например USB disk:

```text
/dev/sdc
```

Mount-ваме го:

```bash
sudo mkdir -p /mnt/backup
sudo mount /dev/sdc1 /mnt/backup
```

Проверяваме:

```bash
df -h /mnt/backup
```

После:

```bash
sudo rsync -aHAX \
    /mnt/alfa-snapshot/ \
    /mnt/backup/alfa-2026-08-11/
```

Получаваме:

```text
External USB disk
/mnt/backup/
└── alfa-2026-08-11/
    ├── etc
    ├── home
    ├── usr
    ├── var
    └── ...
```

Това вече е реално резервно копие на друг носител.

---

# 17. Целият backup workflow

Практически:

```text
LIVE SYSTEM
    │
    ▼
Create LVM snapshot
    │
    ▼
Mount snapshot read-only
    │
    ▼
rsync snapshot → external disk
    │
    ▼
verify backup
    │
    ▼
umount snapshot
    │
    ▼
lvremove snapshot
```

Примерни команди:

```bash
sudo lvcreate \
    -L 20G \
    -s \
    -n ubuntu-snapshot \
    /dev/ubuntu-vg/ubuntu-lv
```

после:

```bash
sudo mkdir -p /mnt/alfa-snapshot
```

```bash
sudo mount -o ro \
    /dev/ubuntu-vg/ubuntu-snapshot \
    /mnt/alfa-snapshot
```

проверка:

```bash
findmnt /mnt/alfa-snapshot
```

backup:

```bash
sudo rsync -aHAX --numeric-ids \
    /mnt/alfa-snapshot/ \
    /mnt/backup/alfa-2026-08-11/
```

После:

```bash
sync
```

размонтиране:

```bash
sudo umount /mnt/alfa-snapshot
```

премахване snapshot:

```bash
sudo lvremove /dev/ubuntu-vg/ubuntu-snapshot
```

---

# 18. Какво остава след `lvremove`

Преди:

```text
Disk
└── VG
    ├── ubuntu-lv
    │      └── LIVE SYSTEM
    │
    └── ubuntu-snapshot
           └── temporary snapshot

USB disk
└── alfa-2026-08-11
       └── permanent backup
```

След:

```bash
sudo lvremove ...ubuntu-snapshot
```

остава:

```text
Disk
└── VG
    └── ubuntu-lv
           └── LIVE SYSTEM

USB disk
└── alfa-2026-08-11
       └── BACKUP
```

Това е нормалният workflow.

---

# 19. Restore след дни или месеци

Да кажем след два месеца:

```text
/etc/nginx/sites-available/my-site
```

е повреден.

Външният backup е:

```text
/mnt/backup/alfa-2026-08-11/
```

Първо:

```bash
diff \
    /etc/nginx/sites-available/my-site \
    /mnt/backup/alfa-2026-08-11/etc/nginx/sites-available/my-site
```

След това възстановяваш:

```bash
sudo cp \
    /mnt/backup/alfa-2026-08-11/etc/nginx/sites-available/my-site \
    /etc/nginx/sites-available/my-site
```

или с `rsync`:

```bash
sudo rsync -a \
    /mnt/backup/alfa-2026-08-11/etc/nginx/sites-available/my-site \
    /etc/nginx/sites-available/
```

След това например:

```bash
sudo nginx -t
```

и:

```bash
sudo systemctl reload nginx
```

---

# 20. Restore на цяла директория

Например:

```text
/var/www/example
```

Dry run:

```bash
sudo rsync -aHAXn \
    /mnt/backup/alfa-2026-08-11/var/www/example/ \
    /var/www/example/
```

Ако е ОК:

```bash
sudo rsync -aHAX \
    /mnt/backup/alfa-2026-08-11/var/www/example/ \
    /var/www/example/
```

---

# 21. Ако искаш backup файл, а не directory tree

Може вместо:

```text
/mnt/backup/alfa-2026-08-11/
```

да създадеш архив:

```bash
sudo tar \
    --acls \
    --xattrs \
    --numeric-owner \
    -cpf /mnt/backup/alfa-2026-08-11.tar \
    -C /mnt/alfa-snapshot .
```

И компресиран:

```bash
sudo tar \
    --acls \
    --xattrs \
    --numeric-owner \
    -czpf /mnt/backup/alfa-2026-08-11.tar.gz \
    -C /mnt/alfa-snapshot .
```

Тогава външният диск съдържа:

```text
alfa-2026-08-11.tar.gz
```

---

# 22. Как се възстановява отделна папка от `.tar.gz`

Първо можеш да разгледаш:

```bash
tar -tzf /mnt/backup/alfa-2026-08-11.tar.gz | less
```

Например търсим:

```bash
tar -tzf /mnt/backup/alfa-2026-08-11.tar.gz |
grep '^./etc/nginx'
```

За извличане в временна директория:

```bash
mkdir ~/restore-test
```

```bash
sudo tar \
    -xzpf /mnt/backup/alfa-2026-08-11.tar.gz \
    -C ~/restore-test \
    ./etc/nginx
```

Получаваш:

```text
~/restore-test/etc/nginx
```

Можеш да го разгледаш преди да го върнеш в живата система.

Това е много по-безопасно от директно overwrite-ване.

---

# 23. Има два различни вида restore

Това също е важно.

## File-level restore

Например:

```text
/etc/nginx
/home/momchil/project
/var/www/app
```

Използваш:

```text
rsync
cp
tar
```

Това е най-честото.

## Full-system restore

При тотално повреден диск:

```text
disk dies
```

Трябва:

1. нов диск;
2. partitioning;
3. EFI;
4. `/boot`;
5. LVM;
6. filesystem;
7. restore на файловете;
8. `/etc/fstab`;
9. bootloader;
10. GRUB;
11. initramfs.

Това е вече disaster recovery.

---

# 24. Ако физическият диск умре

Да кажем:

```text
/dev/sdb
```

умира.

Купуваш нов:

```text
/dev/sdd
```

После приблизително:

```text
new disk
   ↓
GPT
   ↓
partitions
   ↓
PV
   ↓
VG
   ↓
LV
   ↓
ext4
   ↓
restore files
   ↓
install GRUB
   ↓
boot
```

Тук backup-ът върху **външен носител** е това, което те спасява.

Snapshot-ът на стария диск няма да помогне, ако самият стар диск е физически повреден.

---

# 25. Много важно: LVM snapshot може да се "напълни"

Да кажем:

```bash
lvcreate -L 10G -s ...
```

Snapshot пространството е 10 GB.

Ако след създаването му live системата промени повече блокове, отколкото snapshot-ът може да пази, той може да стане невалиден.

Следиш:

```bash
sudo lvs
```

или по-добре:

```bash
sudo lvs -o lv_name,origin,lv_size,data_percent
```

например:

```text
LV               Origin     LSize   Data%
ubuntu-snapshot  ubuntu-lv  20.00g  17.42
```

`Data%` показва колко от snapshot пространството е изразходвано.

Ако отива към:

```text
100%
```

имаш проблем.

---

# 26. Snapshot се пази възможно най-кратко

Правилната философия е:

```text
create snapshot
      ↓
backup
      ↓
delete snapshot
```

Не:

```text
create snapshot
      ↓
оставям го 6 месеца
```

Колкото по-дълго стои snapshot-ът:

* толкова повече промени трябва да пази;
* толкова повече пространство използва;
* може да влияе на performance;
* увеличава сложността.

---

# 27. Database backup е отделна тема

Ако имаш например PostgreSQL:

```text
/var/lib/postgresql/
```

не бих разчитал само на копиране на файловете му.

По-добре:

```bash
pg_dump
```

или:

```bash
pg_dumpall
```

За MySQL/MariaDB:

```bash
mysqldump
```

Тоест хубавият backup може да съдържа:

```text
backup/
├── filesystem/
│   ├── etc
│   ├── home
│   └── var/www
│
└── databases/
    ├── postgres.sql
    └── mysql.sql
```

Snapshot-ът помага за filesystem консистентност, но application-aware database dump има допълнителна стойност.

---

# 28. Практическият модел, който бих използвал

Например сервер:

```text
/dev/sda
   Linux system
```

и външен диск:

```text
/dev/sdb
   backups
```

Workflow:

```text
                     LIVE SERVER
                         │
                         ▼
                /dev/vg/root
                         │
                 LVM snapshot
                         │
                         ▼
               /mnt/snapshot
                         │
                         │ rsync
                         ▼
                EXTERNAL DISK
                 /mnt/backup
                         │
                         ▼
              backup-2026-08-11
```

След backup:

```text
snapshot → DELETE

external backup → KEEP
```

---

# 29. Например напълно практически скрипт

Нещо подобно:

```bash
#!/usr/bin/env bash

set -euo pipefail

VG="ubuntu-vg"
LV="ubuntu-lv"
SNAPSHOT="ubuntu-snapshot"

SNAP_SIZE="20G"

SNAP_MOUNT="/mnt/alfa-snapshot"
BACKUP_MOUNT="/mnt/backup"

DATE="$(date +%Y-%m-%d_%H-%M-%S)"
DEST="${BACKUP_MOUNT}/alfa-${DATE}"

echo "Creating snapshot..."

sudo lvcreate \
    --snapshot \
    --size "$SNAP_SIZE" \
    --name "$SNAPSHOT" \
    "/dev/${VG}/${LV}"

echo "Mounting snapshot..."

sudo mkdir -p "$SNAP_MOUNT"

sudo mount \
    -o ro \
    "/dev/${VG}/${SNAPSHOT}" \
    "$SNAP_MOUNT"

echo "Creating backup..."

sudo mkdir -p "$DEST"

sudo rsync \
    -aHAX \
    --numeric-ids \
    "${SNAP_MOUNT}/" \
    "${DEST}/"

echo "Flushing writes..."

sync

echo "Unmounting snapshot..."

sudo umount "$SNAP_MOUNT"

echo "Removing snapshot..."

sudo lvremove -y "/dev/${VG}/${SNAPSHOT}"

echo
echo "Backup completed:"
echo "$DEST"
```

Пускане:

```bash
chmod +x backup.sh
sudo ./backup.sh
```

Разбира се, преди реално използване трябва да замениш:

```bash
VG="ubuntu-vg"
LV="ubuntu-lv"
```

с истинските имена от:

```bash
sudo lvs
```

---

# 30. И restore script може да е прост

Например искаш да възстановиш:

```text
/etc/nginx
```

от:

```text
/mnt/backup/alfa-2026-08-11/
```

Първо:

```bash
sudo rsync -aHAXn \
    /mnt/backup/alfa-2026-08-11/etc/nginx/ \
    /etc/nginx/
```

След преглед:

```bash
sudo rsync -aHAX \
    /mnt/backup/alfa-2026-08-11/etc/nginx/ \
    /etc/nginx/
```

---

# 31. Как се връзва това конкретно с твоя `lsblk`

Ти имаш:

```text
sdb
├─sdb1
├─sdb2
└─sdb3
  └─ubuntu--snapshot-ubuntu--lv
       /mnt/alfa-snapshot
```

Това ни казва приблизително:

```text
/dev/sdb
   │
   ├── sdb1
   ├── sdb2
   │
   └── sdb3
        │
        ▼
       LVM PV
        │
        ▼
       VG
        │
        ▼
     ubuntu-lv
        │
        ▼
      ext4
        │
        ▼
 /mnt/alfa-snapshot
```

Но има една важна особеност: само от този `lsblk` **не бих заключил**, че `ubuntu--snapshot-ubuntu--lv` непременно е LVM snapshot в техническия смисъл.

Името може просто да означава, че VG се казва:

```text
ubuntu-snapshot
```

а LV:

```text
ubuntu-lv
```

Тогава:

```text
ubuntu--snapshot-ubuntu--lv
```

е просто escaped device-mapper името.

За да видим дали действително е snapshot:

```bash
sudo lvs -a -o \
lv_name,vg_name,lv_attr,origin,lv_size,data_percent
```

Това е командата, на която бих вярвал.

Например ако получиш:

```text
LV          VG              Attr       Origin     LSize
ubuntu-lv   ubuntu-snapshot -wi-a-----            158.5g
```

това **не е snapshot**. Това е обикновен LV в VG, която просто се казва `ubuntu-snapshot`.

А истински snapshot би изглеждал приблизително:

```text
LV              VG         Attr       Origin
ubuntu-snap     ubuntu-vg  swi-a-s--- ubuntu-lv
```

Това е много важно уточнение спрямо предишните ни съобщения.

---

## Най-кратката mental model картинка

Запомни това:

```text
ФИЗИЧЕСКО НИВО
─────────────────────────────
disk
 ↓
partition

LVM НИВО
─────────────────────────────
PV
 ↓
VG
 ↓
LV
 ├───────────────┐
 ↓               ↓
original      snapshot
                  │
                  │ temporary
                  ▼
FILESYSTEM НИВО
─────────────────────────────
ext4
 ↓
mount point
 ↓
files/directories

BACKUP НИВО
─────────────────────────────
snapshot
 ↓
rsync / tar
 ↓
external physical disk
 ↓
permanent backup

RESTORE
─────────────────────────────
external backup
 ↓
extract / rsync
 ↓
specific directory/file
 ↓
live filesystem
```

И най-важното разграничение е:

**LVM snapshot = временна моментна снимка.**

**Backup = независимо копие на друг носител.**

**Restore = връщане на данни от snapshot или backup обратно в работната система.**

А в твоя конкретен случай аз първо бих изпълнил:

```bash
sudo pvs
sudo vgs
sudo lvs -a -o lv_name,vg_name,lv_attr,origin,lv_size,data_percent
lsblk -f
```

Тези четири команди практически ще ни покажат **цялата storage архитектура на твоя `sdb` от физическия диск чак до filesystem-а** и ще можем да я разчетем ред по ред.
