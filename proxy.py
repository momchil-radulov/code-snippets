#[main_proxy.py]#
import uvicorn
from fastapi import FastAPI, Request, Response, BackgroundTasks
import httpx
import json
from pathlib import Path

# Конфигурация:
BACKEND_URL = "http://127.0.0.1:5000"   # Бекенд сървърът, към който препращаме заявките
LOGGING_URL = "https://your_domain/your_log_url"  # URL за логване във формат JSON
LOG_FILE = Path("log.txt")

app = FastAPI()

async def send_log(log_data: dict):
    """
    Изпраща лог данните (заявка и отговор) във формат JSON към LOGGING_URL.
    """
    async with httpx.AsyncClient() as client:
        try:
            await client.post(LOGGING_URL, json=log_data)
        except Exception as e:
            print("Грешка при изпращане на лог:", e)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(full_path: str, request: Request, background_tasks: BackgroundTasks):
    """
    Препраща заявката към бекенд сървъра и връща отговора към клиента.
    Логва съдържанието на заявката и отговора чрез background task.
    """
    # Четене на тялото на заявката:
    body = await request.body()
    # Създаване на URL за бекенд сървъра:
    backend_url = f"{BACKEND_URL}/{full_path}"

    # Препращане на заявката към бекенда:
    async with httpx.AsyncClient() as client:
        backend_response = await client.request(
            method=request.method,
            url=backend_url,
            headers=request.headers.raw,
            params=request.query_params,
            data=body
        )

    # Подготовка на лог данните:
    log_data = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "body": body.decode("utf-8", errors="replace")
        },
        "response": {
            "status_code": backend_response.status_code,
            "headers": dict(backend_response.headers),
            "body": backend_response.text
        }
    }
    # Добавяне на логването като background task, за да не блокира връщането на отговора:
    background_tasks.add_task(send_log, log_data)
    await save_log(log_data)
   # Връщане на отговора към клиента:
    return Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        headers=dict(backend_response.headers)
    )

async def save_log(log_data: dict):
    """
    Записва логовете във файл log.txt във формат JSON.
    """
    try:
        # Отваря файла в append режим и добавя JSON лог на нов ред
        with LOG_FILE.open("a", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False)
            f.write("\n")  # нов ред за всяка заявка
    except Exception as e:
        print("Грешка при записване в log.txt:", e)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

#[requirements.txt]#
fastapi
httpx
uvicorn

#[proxy1.py]#
import asyncio
import logging

# Настройка на логването
logging.basicConfig(
    filename='proxy.log',
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Конфигурация
PROXY_HOST = '127.0.0.1'  # на този адрес ще слуша проксито
PROXY_PORT = 8888         # този порт ще приема клиенти

BACKEND_HOST = '127.0.0.1'  # бекенд сървъра, към който ще препраща
BACKEND_PORT = 9000         # порт на бекенда

async def forward(reader, writer):
    try:
        while not reader.at_eof():
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception as e:
        logging.warning(f'Грешка при пренасочване: {e}')
    finally:
        writer.close()
        await writer.wait_closed()

async def handle_client(client_reader, client_writer):
    client_addr = client_writer.get_extra_info('peername')
    logging.info(f'Нова връзка от {client_addr}')

    try:
        backend_reader, backend_writer = await asyncio.open_connection(BACKEND_HOST, BACKEND_PORT)
        logging.info(f'Свързан с бекенда {BACKEND_HOST}:{BACKEND_PORT}')

        # Две задачи: клиент -> бекенд и бекенд -> клиент
        task1 = asyncio.create_task(forward(client_reader, backend_writer))
        task2 = asyncio.create_task(forward(backend_reader, client_writer))

        await asyncio.gather(task1, task2)
    except Exception as e:
        logging.error(f'Грешка при обработка на клиента {client_addr}: {e}')
    finally:
        client_writer.close()
        await client_writer.wait_closed()
        logging.info(f'Връзката с клиента {client_addr} е затворена')

async def main():
    server = await asyncio.start_server(handle_client, PROXY_HOST, PROXY_PORT)
    addr = server.sockets[0].getsockname()
    logging.info(f'Проксито слуша на {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Проксито беше спряно ръчно.')

#[proxy2.py]#
import asyncio
import logging
from datetime import datetime

# Конфигурация на логването
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy.log'),
        logging.StreamHandler()
    ]
)

async def handle_client(reader, writer, backend_host, backend_port):
    client_addr = writer.get_extra_info('peername')
    logging.info(f"Нова връзка от клиент: {client_addr}")
    
    try:
        # Свързване с бекенда
        backend_reader, backend_writer = await asyncio.open_connection(
            backend_host, backend_port)
        logging.info(f"Свързан с бекенд {backend_host}:{backend_port} за клиент {client_addr}")
        
        # Създаваме задачи за двупосочно предаване на данни
        client_to_backend = asyncio.create_task(
            pipe_data(reader, backend_writer, f"Клиент {client_addr} -> Бекенд"))
        backend_to_client = asyncio.create_task(
            pipe_data(backend_reader, writer, f"Бекенд -> Клиент {client_addr}"))
        
        # Изчакваме някоя от задачите да завърши
        done, pending = await asyncio.wait(
            [client_to_backend, backend_to_client],
            return_when=asyncio.FIRST_COMPLETED
        )
        
    except Exception as e:
        logging.error(f"Грешка при обработка на клиент {client_addr}: {e}")
    finally:
        # Затваряме всички връзки
        logging.info(f"Затваряне на връзки за клиент {client_addr}")
        writer.close()
        try:
            await writer.wait_closed()
        except:
            pass
        
        if 'backend_writer' in locals():
            backend_writer.close()
            try:
                await backend_writer.wait_closed()
            except:
                pass
        
        # Отмяна на всички pending задачи
        for task in pending:
            task.cancel()

async def pipe_data(reader, writer, label):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                logging.info(f"{label}: Няма повече данни (затваряне)")
                break
            writer.write(data)
            await writer.drain()
            logging.debug(f"{label}: Предадени {len(data)} байта")
    except ConnectionResetError:
        logging.info(f"{label}: Връзката е затворена от другия край")
    except Exception as e:
        logging.error(f"{label}: Грешка при предаване на данни: {e}")
    finally:
        writer.close()

async def run_proxy(local_host, local_port, backend_host, backend_port):
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, backend_host, backend_port),
        local_host, local_port
    )
    
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Прокси сървър слуша на {addrs}')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    # Конфигурация
    LOCAL_HOST = '0.0.0.0'  # слуша на всички интерфейси
    LOCAL_PORT = 8888         # локален порт за клиенти
    BACKEND_HOST = 'example.com'  # хост на бекенда
    BACKEND_PORT = 80             # порт на бекенда
    
    logging.info(f"Стартиране на прокси сървър {LOCAL_HOST}:{LOCAL_PORT} -> {BACKEND_HOST}:{BACKEND_PORT}")
    
    try:
        asyncio.run(run_proxy(LOCAL_HOST, LOCAL_PORT, BACKEND_HOST, BACKEND_PORT))
    except KeyboardInterrupt:
        logging.info("Прокси сървърът е спрян")
    except Exception as e:
        logging.error(f"Фатална грешка: {e}")
