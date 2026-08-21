ако имам една mqtt команда, която за да се реализира води до няколко други mqtt команди и съответно отговори по тези команди, как мога лесно да обновя статуса на главната команда в зависимост от успшеното изпълнение на подкомандите?

Да — най-чистият начин е да третираш главната MQTT команда като workflow / parent command, а породените от нея команди като child commands, всяка със собствен command_id и връзка към parent_command_id.

Така не се опитваш да „познаеш“ състоянието от MQTT topic-ите, а имаш малка state machine.

Примерно:

MAIN COMMAND
    id = 1000
    status = processing


        ├── command 1001 → success
        ├── command 1002 → success
        └── command 1003 → pending

Докато 1003 не приключи:

1000 = processing

Когато всички приключат успешно:

1000 = success

Ако една се провали:

1000 = failed
1. Най-простият модел

Бих използвал статуси:

pending
processing
success
failed
timeout

И структура например:

CREATE TABLE commands (
    id              BIGSERIAL PRIMARY KEY,


    parent_id       BIGINT NULL REFERENCES commands(id),


    command_type    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',


    correlation_id  UUID NOT NULL,


    error_message   TEXT,


    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);

Например:

id    parent_id    command_type        status
-------------------------------------------------
1000  NULL         configure_device    processing
1001  1000         set_temperature     success
1002  1000         set_mode            success
1003  1000         reboot              pending

Това вече ти позволява много лесно:

SELECT status
FROM commands
WHERE parent_id = 1000;
2. Основната идея: не увеличавай/намалявай броячи ръчно

Може да направиш:

children_total = 3
children_success = 2
children_failed = 0

но това създава проблеми с:

повторни MQTT съобщения;
retry;
duplicated acknowledgement;
crash между две операции;
race conditions.

По-надеждно е истината да бъде status-ът на всяка child команда, а aggregate status да се изчислява от тях.

Например:

SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE status = 'success') AS success,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed,
    COUNT(*) FILTER (
        WHERE status IN ('pending', 'processing')
    ) AS running
FROM commands
WHERE parent_id = 1000;

После логиката е:

if failed > 0:
    parent_status = "failed"
elif running > 0:
    parent_status = "processing"
elif success == total:
    parent_status = "success"
3. Още по-добре: всяка подкоманда си обновява статуса

Например изпращаш:

iot/device/123/command

payload:

{
    "command_id": "1001",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "command": "set_temperature",
    "value": 22
}

Устройството отговаря:

iot/device/123/response
{
    "command_id": "1001",
    "status": "success"
}

Тук command_id е критичен.

Не разчитай на:

topic + време + device_id

за да разбереш на коя команда е отговорът.

Имай изричен:

command_id
4. Workflow

Пример:

Главната команда е:

configure_device

Тя поражда:

set_mode
set_temperature
set_schedule
restart

Последователността:

configure_device
       |
       v
   set_mode
       |
       v
set_temperature
       |
       v
 set_schedule
       |
       v
   restart

Ако са зависими една от друга, бих ги пускал последователно.

Но ако са независими:

             +--> set_mode --------+
             |                     |
configure ---+--> set_temp --------+--> restart
             |                     |
             +--> set_schedule ----+

можеш да пуснеш първите три паралелно.

5. Много полезно правило

Всеки път когато child command промени status:

pending → processing
processing → success
processing → failed

извикай:

update_parent_status(parent_id)

Например:

def update_parent_status(conn, parent_id: int):
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,


            COUNT(*) FILTER (
                WHERE status = 'success'
            ) AS success,


            COUNT(*) FILTER (
                WHERE status IN ('failed', 'timeout')
            ) AS failed,


            COUNT(*) FILTER (
                WHERE status IN ('pending', 'processing')
            ) AS running


        FROM commands
        WHERE parent_id = %s
        """,
        (parent_id,)
    ).fetchone()


    if row["total"] == 0:
        return


    if row["failed"] > 0:
        new_status = "failed"


    elif row["running"] > 0:
        new_status = "processing"


    elif row["success"] == row["total"]:
        new_status = "success"


    else:
        new_status = "processing"


    conn.execute(
        """
        UPDATE commands
        SET
            status = %s,
            finished_at =
                CASE
                    WHEN %s IN ('success', 'failed')
                    THEN now()
                    ELSE NULL
                END
        WHERE id = %s
        """,
        (
            new_status,
            new_status,
            parent_id
        )
    )
6. Но има един важен нюанс

Ако имаш command tree:

1000
 ├── 1001
 ├── 1002
 │    ├── 2001
 │    └── 2002
 └── 1003

тогава 1002 също е parent.

При завършване на:

2001

обновяваш:

1002

После евентуално:

1000

Тоест можеш рекурсивно:

def refresh_command_tree(command_id):
    parent_id = update_parent_status(command_id)


    if parent_id:
        refresh_command_tree(parent_id)

На практика обаче често само 1–2 нива са достатъчни.

7. Аз бих разделил command и execution

При по-сериозна система има още един вариант, който ми харесва повече:

workflow
workflow_step
mqtt_command

Например:

workflow
--------------------------------
id: 100
type: configure_device
status: processing




workflow_step
--------------------------------
101 set_mode         success
102 set_temperature  success
103 set_schedule     processing




mqtt_command
--------------------------------
10001 workflow_step=101
10002 workflow_step=102
10003 workflow_step=103

Това е по-правилно концептуално, защото:

бизнес команда ≠ MQTT packet

Една бизнес операция може да доведе до:

5 MQTT команди
2 DB операции
1 HTTP API request

И въпреки това да бъде един workflow.

8. MQTT command ID / correlation ID

Аз бих имал поне тези ID-та:

{
    "command_id": "01K3...",
    "workflow_id": "01K3...",
    "correlation_id": "01K3..."
}

Но често не са нужни и трите.

Може:

workflow_id
command_id

например:

{
    "workflow_id": "configure-12345",
    "command_id": "cmd-98765",


    "command": "set_temperature",


    "params": {
        "temperature": 22
    }
}

Response:

{
    "workflow_id": "configure-12345",
    "command_id": "cmd-98765",


    "status": "success"
}

Така lookup-ът е тривиален:

UPDATE commands
SET status = 'success'
WHERE external_id = 'cmd-98765';
9. Задължително: idempotency

MQTT може да ти даде duplicate delivery, особено при QoS 1:

At least once

Следователно:

response cmd-98765 SUCCESS

може да бъде получен два пъти.

Кодът трябва спокойно да понесе:

success → success

Например:

UPDATE commands
SET
    status = 'success',
    finished_at = COALESCE(finished_at, now())
WHERE external_id = $1
  AND status NOT IN ('success', 'failed');

Или още по-добре имаш state transition rules.

10. State machine

Например позволени:

pending
    ↓
sent
    ↓
acknowledged
    ↓
processing
    ↓
success

или:

processing
    ↓
failed

или:

sent
    ↓
timeout

Не позволяваш:

success → processing

случайно от старо MQTT съобщение.

Например:

ALLOWED_TRANSITIONS = {
    "pending": {"sent", "failed"},
    "sent": {"acknowledged", "success", "failed", "timeout"},
    "acknowledged": {"processing", "success", "failed", "timeout"},
    "processing": {"success", "failed", "timeout"},
    "success": set(),
    "failed": set(),
    "timeout": set(),
}
11. Timeout е много важен

Представи си:

main
 ├── child1 success
 ├── child2 success
 └── child3 processing

Но устройството угасва.

И тогава:

main = processing

завинаги.

Следователно child command трябва да има:

deadline

Например:

deadline TIMESTAMPTZ

и периодичен процес:

UPDATE commands
SET
    status = 'timeout',
    finished_at = now()
WHERE status IN ('pending', 'sent', 'processing')
AND deadline < now();

След това:

update_parent_status(parent_id)

и parent става:

failed

или:

partial_failure

според бизнес логиката.

12. Може да имаш и partial_success

Понякога:

3 / 4 success

не означава непременно:

failed

Може да е:

partial_success

Например:

if failed == 0 and success == total:
    status = "success"


elif failed > 0 and success > 0 and running == 0:
    status = "partial_success"


elif failed == total:
    status = "failed"


else:
    status = "processing"

Получаваш:

pending
processing
success
partial_success
failed
timeout
13. Още по-полезно — progress

Тъй като имаш подкомандите, много лесно можеш да показваш:

3 / 5
60%

SQL:

SELECT
    COUNT(*) FILTER (
        WHERE status IN ('success', 'failed', 'timeout')
    )::float
    /
    NULLIF(COUNT(*), 0)
    * 100 AS progress


FROM commands
WHERE parent_id = $1;

Например:

{
    "workflow_id": 1000,
    "status": "processing",
    "progress": 60,
    "steps": {
        "total": 5,
        "completed": 3,
        "success": 3,
        "failed": 0
    }
}
14. За твоя случай бих направил архитектурата така
                         PostgreSQL
                             |
                             |
                           command
                             |
           +-----------------+----------------+
           |                 |                |
           v                 v                v
        child 1           child 2          child 3
           |                 |                |
           v                 v                v
        MQTT publish      MQTT publish     MQTT publish
           |                 |                |
           v                 v                v
        DEVICE            DEVICE           DEVICE
           |                 |                |
           v                 v                v
        response          response         response
           |                 |                |
           +-----------------+----------------+
                             |
                             v
                    MQTT response handler
                             |
                             v
                    UPDATE child status
                             |
                             v
                    recompute parent

Ключовото е:

MQTT не държи workflow state.

MQTT е само транспортът.

State-ът стои например в:

PostgreSQL
15. И не бих правил това

Например:

pending_commands = {}


pending_commands["main123"] = [
    "child1",
    "child2",
    "child3"
]

само в RAM.

Защото:

service restart
       ↓
цялото състояние изчезва

Може да имаш RAM cache, но authoritative state трябва да бъде в DB / Redis.

16. Ако използваш Redis

Понеже преди говорихме за Redis Streams, може да имаш:

MQTT
 ↓
MQTT worker
 ↓
Redis Stream
 ↓
workflow worker
 ↓
PostgreSQL

Но за самото следене на parent → child status не ти трябва Redis.

PostgreSQL е напълно достатъчен.

Redis има повече смисъл за:

queues
events
workers
retry processing
load distribution
17. Един конкретен пример

Имаш команда:

START_SYSTEM

тя води до:

SET_MODE
SET_LIMITS
START_MOTOR

DB:

commands


id   parent_id   command       status
-------------------------------------------
1    NULL        START_SYSTEM  processing
2    1           SET_MODE      success
3    1           SET_LIMITS    processing
4    1           START_MOTOR   pending

Получаваш:

{
    "command_id": 3,
    "status": "success"
}

правиш:

UPDATE commands
SET status = 'success'
WHERE id = 3;

проверяваш parent:

2 success
3 success
4 pending

следователно:

1 processing

После получаваш:

{
    "command_id": 4,
    "status": "success"
}

получаваш:

2 success
3 success
4 success

следователно:

1 success

Това е цялата идея.

Аз бих го направил точно по този модел

За твоята система:

Command
 ├── id
 ├── parent_id
 ├── system_id/device_id
 ├── type
 ├── status
 ├── payload
 ├── response
 ├── error
 ├── deadline
 ├── created_at
 ├── sent_at
 └── finished_at

и едно централно:

refresh_parent_status(parent_id)

което се извиква след всяка промяна на child status.

Така получаваш много прост и устойчив механизъм:

child MQTT response
        ↓
update child
        ↓
aggregate children
        ↓
update parent
        ↓
ако parent има parent
        ↓
aggregate нагоре

Това всъщност се превръща в малък workflow engine, без да ти трябва специален workflow framework. И е много подходящо за MQTT/IoT система, защото естествено решава delayed responses, retries, duplicate MQTT messages, timeout-и и рестартиране на backend процеса.
