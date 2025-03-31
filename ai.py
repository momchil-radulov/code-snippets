### Naïve Bayes Classifier ###

from sklearn.feature_extraction.text import CountVectorizer                                                                        
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Примерни данни: две категории (спам и нормални съобщения)
X_train = ["Промоция! Спечели награда сега!", 
           "Здравей, как си днес?", 
           "Купи сега и получи 50% отстъпка!", 
           "Грандиозна оферта! Безплатен iPhone!", 
           "Това е обикновен имейл без реклама."]
y_train = ["spam", "normal", "spam", "spam", "normal"]

# Създаваме модел
model = make_pipeline(CountVectorizer(), MultinomialNB())

# Тренираме модела
model.fit(X_train, y_train)

# Тестваме с нов текст
test_messages = ["Специална оферта за теб!", "Как мина срещата днес?"]
predictions = model.predict(test_messages)

# Извеждаме резултатите
print(predictions)  # ['spam', 'normal']


### Анализ ###
## Bag of Words (Чанта с думи) ##
# Този метод подобрява Bag of Words, като не само брои думите, но и дава по-малка тежест на често срещаните думи
# (като "и", "за") и по-голяма тежест на важните думи.
# Формулата за TF-IDF е: 𝑇𝐹 − 𝐼𝐷𝐹 = 𝑇𝐹 × 𝐼𝐷𝐹
# където: TF (Term Frequency) – честота на дадена дума в документа.
#         IDF (Inverse Document Frequency) – колко "рядка" е думата в целия корпус.

texts = X_train
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)

print(vectorizer.get_feature_names_out())
print(X.toarray())


### Анализ ###
## TF-IDF (Term Frequency - Inverse Document Frequency) ##
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

print(vectorizer.get_feature_names_out())
print(X.toarray())  # Стойностите ще бъдат нормализирани и претеглени



### Word2Vec ###
# Word embeddings представляват многомерни вектори, които улавят семантичното значение на думите.
# Един от най-популярните методи за създаване на такива вектори е Word2Vec, който използва невронни мрежи,
# за да научи представяния на думи на базата на контекста, в който се срещат.

from gensim.models import Word2Vec                                                                                                 

# Примерни изречения
sentences = [
    ["куче", "лае", "на", "котка"],
    ["котка", "скача", "на", "масата"],
    ["птица", "лети", "над", "дървото"],
    ["куче", "гони", "топка"],
    ["котка", "лежи", "на", "дивана"],
    ["птица", "пее", "на", "клона"]
]

# Обучаваме Word2Vec модела
# vector_size=10 – размерът на векторите (може да се увеличи за по-добро качество).
# window=2 – брой съседни думи, които моделът ще използва за контекст.
# min_count=1 – минимален брой срещания на дума в обучаващите данни.
# workers=4 – използва 4 CPU нишки за обучение.
model = Word2Vec(sentences, vector_size=10, window=2, min_count=1, workers=4)

# Извличаме векторното представяне на думата "куче"
vector = model.wv["куче"]
print("Вектор за 'куче':", vector)

# Намираме най-близките думи до "куче"
similar_words = model.wv.most_similar("куче", topn=3)
print("Най-близки думи до 'куче':", similar_words)


### Word2Vec + Prompt Matching ###
from gensim.models import Word2Vec
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# Примерни изречения (База знания)
knowledge_base = [
    "Какво е машинно обучение?",
    "Как работи Word2Vec?",
    "Какво е невронна мрежа?",
    "Как да използвам Python за NLP?",
    "Как работи Naïve Bayes класификаторът?"
]

# Обучаваме Word2Vec модела върху базата знания
tokenized_sentences = [sentence.lower().split() for sentence in knowledge_base]
model = Word2Vec(tokenized_sentences, vector_size=100, window=5, min_count=1, workers=4)

# Функция за преобразуване на изречение във вектор (усреднен вектор на думите)
def sentence_vector(sentence, model):
    words = sentence.lower().split()
    word_vectors = [model.wv[word] for word in words if word in model.wv]
    return np.mean(word_vectors, axis=0) if word_vectors else np.zeros(model.vector_size)

# Генериране на вектори за базата знания
kb_vectors = [sentence_vector(sent, model) for sent in knowledge_base]

# Входен prompt от потребителя
user_prompt = "Как работи NLP с Python?"
prompt_vector = sentence_vector(user_prompt, model)

# Намираме най-близкото изречение чрез косинусова близост
similarities = cosine_similarity([prompt_vector], kb_vectors)
best_match_index = np.argmax(similarities)

# Извеждаме най-подходящия отговор
print("Въпрос: ", user_prompt)                             
print("Най-подходящ отговор:", knowledge_base[best_match_index])



import os

def get_files(directory, ext):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(ext):
                python_files.append(os.path.join(root, file))
    return python_files

def read_code(files):
    code_lines = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            code = f.readlines()
            tokenized_lines = [line.strip().split() for line in code if line.strip()]
            code_lines.extend(tokenized_lines)
    return code_lines

# Пример: събиране на код от "my_project/"
python_code_files = get_python_files("my_project/", ".py")
print("Намерени файлове:", python_code_files)

# Зареждаме и обработваме кода
tokenized_code = read_python_code(python_code_files)

# Обучаваме Word2Vec върху кода
model = Word2Vec(tokenized_code, vector_size=100, window=5, min_count=1, workers=4)
model.save("word2vec_code.model")  # Запазваме модела за бъдеща употреба
print("Моделът е обучен и записан.")


## Обработване на Prompt и Търсене на Подходящ Код ##

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Зареждаме обучен модел
model = Word2Vec.load("word2vec_code.model")

# Функция за преобразуване на текст във вектор
def sentence_vector(sentence, model):
    words = sentence.lower().split()
    word_vectors = [model.wv[word] for word in words if word in model.wv]
    return np.mean(word_vectors, axis=0) if word_vectors else np.zeros(model.vector_size)

# Преобразуваме всички редове от кода в вектори
code_vectors = [sentence_vector(" ".join(line), model) for line in tokenized_code]

# Търсене по prompt
def find_best_code_match(prompt):
    prompt_vector = sentence_vector(prompt, model)
    similarities = cosine_similarity([prompt_vector], code_vectors)
    best_match_index = np.argmax(similarities)
    return " ".join(tokenized_code[best_match_index])

# Примерен prompt
user_prompt = "чети JSON файл"
best_match = find_best_code_match(user_prompt)
print("Най-подходящ код:", best_match)

## Генериране на нов код въз основа на резултата ##
import openai  # Ако използваш OpenAI API

openai.api_key = "API_KEY"

def generate_code(prompt, base_code):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ти си асистент за писане на Python код."},
            {"role": "user", "content": f"Довърши този код:\n{base_code}\n\n{prompt}"}
        ]
    )
    return response["choices"][0]["message"]["content"]

generated_code = generate_code(user_prompt, best_match)
print("Генериран код:\n", generated_code)

## Извличане на Функции от Python Кода ##
import os
import ast

def extract_functions_from_file(filepath):
    """ Извлича всички функции от даден Python файл. """
    with open(filepath, "r", encoding="utf-8") as file:
        code = file.read()

    tree = ast.parse(code)
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):  # Намерена е функция
            function_code = ast.unparse(node)  # Връща кода на функцията
            functions.append(function_code)

    return functions

def get_all_functions(directory):
    """ Извлича всички функции от всички Python файлове в проекта. """
    all_functions = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                all_functions.extend(extract_functions_from_file(file_path))
    return all_functions

# Пример: Извличане на всички функции от проекта
project_path = "my_project/"
python_functions = get_all_functions(project_path)

print(f"Намерени {len(python_functions)} функции.")
print("Примерна функция:\n", python_functions[0])

## Трениране на Word2Vec върху функциите ##
from gensim.models import Word2Vec
import re

def tokenize_function_code(function_code):
    """ Разделя функцията на отделни думи и токени. """
    tokens = re.findall(r"\b\w+\b", function_code)  # Взима всички думи и идентификатори
    return tokens

# Токенизираме всички функции
tokenized_functions = [tokenize_function_code(func) for func in python_functions]

# Обучаваме Word2Vec върху функциите
model = Word2Vec(tokenized_functions, vector_size=100, window=5, min_count=1, workers=4)
model.save("word2vec_functions.model")  # Запазваме модела
print("Обучението на Word2Vec е завършено.")

## Търсене на Най-Близка Функция към Prompt ##
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Зареждаме обучен модел
model = Word2Vec.load("word2vec_functions.model")

# Преобразуваме цяла функция във вектор
def function_vector(function_code, model):
    tokens = tokenize_function_code(function_code)
    word_vectors = [model.wv[word] for word in tokens if word in model.wv]
    return np.mean(word_vectors, axis=0) if word_vectors else np.zeros(model.vector_size)

# Преобразуваме всички функции в вектори
function_vectors = [function_vector(func, model) for func in python_functions]

# Търсене на най-близка функция
def find_best_function(prompt):
    prompt_vector = function_vector(prompt, model)
    similarities = cosine_similarity([prompt_vector], function_vectors)
    best_match_index = np.argmax(similarities)
    return python_functions[best_match_index]

# Примерен prompt
user_prompt = "прочети json файл"
best_function = find_best_function(user_prompt)

print("Най-близката функция:\n", best_function)

## Генериране на Нов Код ##
import openai

openai.api_key = "API_KEY"

def generate_code(prompt, base_function):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ти си асистент за писане на Python код."},
            {"role": "user", "content": f"Допълни или подобри тази функция:\n{base_function}\n\n{prompt}"}
        ]
    )
    return response["choices"][0]["message"]["content"]

generated_code = generate_code(user_prompt, best_function)
print("Генериран код:\n", generated_code)

## Проверка за вече обучен модел ##
import os
from gensim.models import Word2Vec

MODEL_PATH = "word2vec_functions.model"

def load_existing_model():
    """ Зарежда съществуващия Word2Vec модел, ако има такъв. """
    if os.path.exists(MODEL_PATH):
        print("🔄 Зареждане на съществуващия Word2Vec модел...")
        return Word2Vec.load(MODEL_PATH)
    else:
        print("🆕 Няма наличен модел. Ще създадем нов.")
        return None

existing_model = load_existing_model()

## Извличане на Нови Функции и Подготовка на Данните ##
def get_new_functions(existing_functions, project_path):
    """ Намери новите функции, които не са били включени досега. """
    all_functions = get_all_functions(project_path)  # Всички функции от проекта
    new_functions = [func for func in all_functions if func not in existing_functions]
    return new_functions

new_functions = get_new_functions(existing_model.wv.index_to_key if existing_model else [], "my_project/")

if new_functions:
    print(f"🔍 Намерени {len(new_functions)} нови функции за обучение.")
else:
    print("✅ Няма нови функции. Моделът е актуален.")

## Дообучаване на Word2Vec с нови функции ##
if new_functions and existing_model:
    print("🔄 Дообучаваме съществуващия модел с нови функции...")
    tokenized_new_functions = [tokenize_function_code(func) for func in new_functions]
    
    # Дообучаваме модела
    existing_model.build_vocab(tokenized_new_functions, update=True)
    existing_model.train(tokenized_new_functions, total_examples=len(tokenized_new_functions), epochs=5)
    
    existing_model.save(MODEL_PATH)
    print("✅ Моделът беше успешно дообучен и запазен.")
    
elif not existing_model:
    print("🆕 Създаваме нов модел от нулата...")
    tokenized_all_functions = [tokenize_function_code(func) for func in new_functions]
    new_model = Word2Vec(tokenized_all_functions, vector_size=100, window=5, min_count=1, workers=4)
    new_model.save(MODEL_PATH)
    print("✅ Новият модел е обучен и запазен.")

## pip install watchdog ##
## Скрипт за автоматично обучение при промени ##
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class CodeChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):  # Само Python файлове
            print(f"🔄 Кодът се промени: {event.src_path}")
            retrain_model()

def watch_directory(directory):
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"👀 Следене на {directory} за промени...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def retrain_model():
    """ Преобучава модела само ако има нови функции. """
    existing_model = load_existing_model()
    new_functions = get_new_functions(existing_model.wv.index_to_key if existing_model else [], "my_project/")

    if new_functions:
        print("🔄 Дообучаваме модела с нови функции...")
        tokenized_new_functions = [tokenize_function_code(func) for func in new_functions]
        
        if existing_model:
            existing_model.build_vocab(tokenized_new_functions, update=True)
            existing_model.train(tokenized_new_functions, total_examples=len(tokenized_new_functions), epochs=5)
            existing_model.save(MODEL_PATH)
        else:
            new_model = Word2Vec(tokenized_new_functions, vector_size=100, window=5, min_count=1, workers=4)
            new_model.save(MODEL_PATH)

        print("✅ Моделът е обновен.")

# Стартираме наблюдението на папката
watch_directory("my_project/")

## Добавяне на лог файл ##
import logging

# Настройка на лог файла
logging.basicConfig(
    filename="training_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_training_event(event_message):
    """ Записва събитие в training_log.txt """
    logging.info(event_message)
    print(event_message)  # Показва съобщението и в терминала

## Актуализиране на retrain_model() да записва логове ##
def retrain_model():
    """ Преобучава модела само ако има нови функции и записва логове. """
    existing_model = load_existing_model()
    new_functions = get_new_functions(existing_model.wv.index_to_key if existing_model else [], "my_project/")

    if new_functions:
        log_training_event(f"🔄 Открити {len(new_functions)} нови функции за обучение.")

        tokenized_new_functions = [tokenize_function_code(func) for func in new_functions]
        
        if existing_model:
            existing_model.build_vocab(tokenized_new_functions, update=True)
            existing_model.train(tokenized_new_functions, total_examples=len(tokenized_new_functions), epochs=5)
            existing_model.save(MODEL_PATH)
        else:
            new_model = Word2Vec(tokenized_new_functions, vector_size=100, window=5, min_count=1, workers=4)
            new_model.save(MODEL_PATH)

        log_training_event("✅ Моделът е успешно обновен.")
    else:
        log_training_event("✅ Няма нови функции. Обучението не е необходимо.")

## Добавяне на логове при следене на файловете ##
class CodeChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            log_training_event(f"📂 Файлът {event.src_path} беше променен.")
            retrain_model()

## Изпращане на логовете по Email (SMTP) ##
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # 16-цифрен App Password

def send_email():
    """ Изпраща training_log.txt като email. """
    if not os.path.exists("training_log.txt"):
        print("⚠️ Няма training_log.txt, няма какво да изпратя.")
        return

    with open("training_log.txt", "r", encoding="utf-8") as file:
        log_content = file.read()

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS  # Може да добавиш друг получател
    msg["Subject"] = "🔄 AI Training Log Update"
    
    msg.attach(MIMEText(log_content, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())
        server.quit()
        print("✅ Логовете бяха изпратени по email.")
    except Exception as e:
        print("❌ Грешка при изпращане на email:", str(e))

# Изпращаме email след обучение
retrain_model()
send_email()

## Изпращане на логовете в Telegram ##
# Ако предпочиташ Telegram, ще използваме Telegram Bot API.
# 2.1 Създаване на Telegram бот
# Отиди в Telegram и потърси @BotFather
# Напиши:
# /newbot
# Дай име и username на бота
# Получаваш API ключ (запази го)
# 2.2 Получаване на Telegram Chat ID
# Отиди на https://t.me/userinfobot
# Напиши /start
# Ще получиш твоя Chat ID

import requests

TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

def send_telegram_message():
    """ Изпраща training_log.txt като Telegram съобщение. """
    if not os.path.exists("training_log.txt"):
        print("⚠️ Няма training_log.txt, няма какво да изпратя.")
        return

    with open("training_log.txt", "r", encoding="utf-8") as file:
        log_content = file.read()

    message = f"🔄 AI Training Log Update:\n\n{log_content[-4000:]}"  # Ограничение от 4096 символа

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("✅ Логовете бяха изпратени в Telegram.")
    else:
        print("❌ Грешка при изпращане в Telegram:", response.text)

# Изпращаме в Telegram след обучение
retrain_model()
send_telegram_message()

## Създаване на systemd услуга (service) ##
sudo vim /etc/systemd/system/code_training.service
[Unit]
Description=AI Code Training Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/script.py
WorkingDirectory=/path/to/your/project
User=your_username
Group=your_group
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=code_training

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable code_training.service
sudo systemctl start code_training.service
sudo systemctl status code_training.service
journalctl -u code_training.service -f


## Изпращане на известия при грешка ##
import smtplib
from email.mime.text import MIMEText

def send_error_notification(error_message):
    """ Изпраща известие за грешка по email """
    try:
        # Използваш същия код за изпращане на email, както по-горе
        msg = MIMEText(f"❌ Грешка при изпълнение на скрипта:\n\n{error_message}")
        msg["From"] = "your_email@gmail.com"
        msg["To"] = "your_email@gmail.com"
        msg["Subject"] = "AI Training Script Error"
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("your_email@gmail.com", "your_app_password")
        server.sendmail("your_email@gmail.com", "your_email@gmail.com", msg.as_string())
        server.quit()
        print("✅ Известие за грешка изпратено.")
    except Exception as e:
        print(f"❌ Неуспешно изпращане на известие за грешка: {str(e)}")

# Пример за обработка на грешка
try:
    retrain_model()
except Exception as e:
    send_error_notification(str(e))

## Използване на Docker за изолирана среда ##
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "script.py"]

## Подобряване на логовете с повече детайли ##
import time

def log_training_event(event_message):
    """ Записва събитие в training_log.txt с допълнителни детайли. """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {event_message}"
    logging.info(log_message)
    print(log_message)  # Показва съобщението и в терминала

## Планиране на редовно обучение (Cron Jobs) ##
crontab -e
0 3 * * * /usr/bin/python3 /path/to/your/script.py

## Мониторинг на системата (за мониторинг на ресурсите) ##
import psutil

def monitor_system_resources():
    """ Мониторира системните ресурси по време на обучението """
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    print(f"CPU Usage: {cpu_usage}%")
    print(f"Memory Usage: {memory_info.percent}%")

# Пример за използване:
monitor_system_resources()

## Оптимизации ##
def load_model(model_path):
    """ Зарежда съществуващия модел от пътя. """
    try:
        model = Word2Vec.load(model_path)
        print("Моделът беше успешно зареден.")
        return model
    except Exception as e:
        print(f"Грешка при зареждане на модела: {e}")
        return None

def retrain_model(model, new_functions, epochs=5, vector_size=100):
    """ Обучава модела с нови функции. """
    tokenized_new_functions = [tokenize_function_code(func) for func in new_functions]
    
    if model:
        model.build_vocab(tokenized_new_functions, update=True)
        model.train(tokenized_new_functions, total_examples=len(tokenized_new_functions), epochs=epochs)
        model.save("model.bin")
        print("Моделът беше обновен успешно.")
    else:
        print("Няма зареден модел за обучение.")

def send_email_notification(subject, body, to_email="your_email@gmail.com"):
    """ Изпраща email известие при грешка или събитие. """
    try:
        msg = MIMEText(body)
        msg["From"] = "your_email@gmail.com"
        msg["To"] = to_email
        msg["Subject"] = subject
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("your_email@gmail.com", "your_app_password")
        server.sendmail("your_email@gmail.com", to_email, msg.as_string())
        server.quit()
        print("Известие за грешка е изпратено.")
    except Exception as e:
        print(f"Грешка при изпращане на email: {str(e)}")


def tokenize_function_code(function_code):
    """
    Токенизира Python код.
    
    :param function_code: Стринг с Python код
    :return: Лист с токенизирани думи
    """
    # Тук използваме примерен механизъм за токенизация
    tokens = function_code.split()
    return tokens


class ModelTrainer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = self.load_model()

    def load_model(self):
        """ Зарежда модел. """
        try:
            model = Word2Vec.load(self.model_path)
            print("Моделът беше успешно зареден.")
            return model
        except Exception as e:
            print(f"Грешка при зареждане на модела: {e}")
            return None

    def retrain_model(self, new_functions):
        """ Преобучава модела. """
        if self.model:
            tokenized_new_functions = [tokenize_function_code(func) for func in new_functions]
            self.model.build_vocab(tokenized_new_functions, update=True)
            self.model.train(tokenized_new_functions, total_examples=len(tokenized_new_functions), epochs=5)
            self.model.save(self.model_path)
            print("Моделът беше обновен успешно.")
        else:
            print("Няма зареден модел за обучение.")


import logging

logging.basicConfig(filename="training_log.txt", level=logging.INFO)

def log_training_event(event_message):
    """ Записва събитие в training_log.txt """
    logging.info(event_message)
    print(event_message)  # Показва съобщението и в терминала
import logging

logging.basicConfig(filename="training_log.txt", level=logging.INFO)

def log_training_event(event_message):
    """ Записва събитие в training_log.txt """
    logging.info(event_message)
    print(event_message)  # Показва съобщението и в терминала


## unit test ##
def test_tokenize_function_code():
    result = tokenize_function_code("def hello_world(): print('Hello World')")
    assert result == ['def', 'hello_world()', ':', 'print(', "'Hello", 'World'", ')']


### pipe / конвейнер ###
def read_data(file_path):
    """Чете съдържание на файл и връща текста като низ."""
    with open(file_path, 'r') as f:
        data = f.read()
    return data

def tokenize_data(data):
    """Токенизира текста (разделя на отделни думи)."""
    return data.split()

def filter_stopwords(tokens, stopwords):
    """Филтрира често използвани думи (като "и", "на" и т.н.)."""
    return [token for token in tokens if token not in stopwords]

def count_tokens(tokens):
    """Преброява колко пъти се среща всяка дума."""
    return {token: tokens.count(token) for token in set(tokens)}

def display_results(results):
    """Показва резултатите (броя на всяка дума)."""
    for word, count in results.items():
        print(f"{word}: {count}")

# Подготвяме спиралата (pipe) с данни
stopwords = {"и", "на", "от", "за", "с", "по", "като"}

file_path = "text.txt"
result = (read_data(file_path)  # Четем данни от файл
          | tokenize_data  # Токенизираме данните
          | filter_stopwords(stopwords)  # Филтрираме стоп-думи
          | count_tokens  # Преброяваме честотата на думите
          | display_results)  # Показваме резултатите

## custom pipe ##
class Pipe:
    def __init__(self, func):
        self.func = func

    def __or__(self, other):
        """ Позволява използване на pipe (|) за свързване на функции. """
        return Pipe(lambda x: other.func(self.func(x)))

    def __call__(self, data):
        """ Извиква функцията на pipe с входните данни. """
        return self.func(data)

# Пример за използване на pipe в Python
read = Pipe(read_data)
tokenize = Pipe(tokenize_data)
filter = Pipe(lambda data: filter_stopwords(data, stopwords))
count = Pipe(count_tokens)
display = Pipe(display_results)

result = (read("text.txt")
          | tokenize
          | filter
          | count
          | display)

## пример ##
def load_data(file_path):
    """Чете данни от файл и ги връща като списък."""
    with open(file_path, "r") as f:
        return f.readlines()

def preprocess_data(data):
    """Предобработва данни (например премахва символи, нормализира и т.н.)."""
    return [d.strip().lower() for d in data]

def train_model(data):
    """Обучава модел с данни."""
    model = SomeMachineLearningModel()
    model.train(data)
    return model

def evaluate_model(model, test_data):
    """Оценява модела с тестови данни."""
    accuracy = model.evaluate(test_data)
    return accuracy

def display_results(accuracy):
    """Показва резултатите от оценката."""
    print(f"Моделът има точност: {accuracy}%")

pipeline = (Pipe(load_data)
            | Pipe(preprocess_data)
            | Pipe(train_model)
            | Pipe(lambda model: evaluate_model(model, test_data))
            | Pipe(display_results))

# Стартираш конвейера с файл с данни
pipeline("data.txt")

{
  "data": {
    "text": "Това е примерен текст за обработка.",
    "numbers": [1, 2, 3, 4, 5],
    "timestamp": "2025-03-30"
  },
  "metadata": {
    "language": "bg",
    "operation": "tokenization"
  }
}

import json

class Pipe:
    def __init__(self, func):
        self.func = func

    def __or__(self, other):
        """Позволява използването на pipe (|) за свързване на функции."""
        return Pipe(lambda data: other.func(self.func(data)))

    def __call__(self, data):
        """Извиква функцията на pipe с входните данни."""
        return self.func(data)

def process_text(data):
    """Примерна функция за обработка на текст от JSON."""
    text = data.get("data", {}).get("text", "")
    if text:
        processed_text = text.lower()
        data["data"]["text"] = processed_text
    return data

def extract_numbers(data):
    """Примерна функция за извличане и обработка на числови данни от JSON."""
    numbers = data.get("data", {}).get("numbers", [])
    squared_numbers = [n ** 2 for n in numbers]
    data["data"]["numbers"] = squared_numbers
    return data

def filter_metadata(data):
    """Примерна функция за филтриране на метаданни от JSON."""
    metadata = data.get("metadata", {})
    if metadata.get("operation") == "tokenization":
        data["metadata"]["status"] = "Processing"
    return data

def display_results(data):
    """Функция за показване на резултатите от обработката."""
    print("Обработени данни:")
    print(json.dumps(data, indent=2))
    return data

# Примерен JSON, с който работим
data = {
    "data": {
        "text": "Това е примерен текст за обработка.",
        "numbers": [1, 2, 3, 4, 5],
        "timestamp": "2025-03-30"
    },
    "metadata": {
        "language": "bg",
        "operation": "tokenization"
    }
}

# Създаване на pipe с функции
result = (Pipe(lambda data: data)  # Започваме с входния JSON
          | process_text           # Обработваме текста
          | extract_numbers        # Обработваме числата
          | filter_metadata        # Филтрираме метаданните
          | display_results)       # Показваме резултатите

# Изпълняваме конвейера
result(data)

def filter_metadata(data):
    """Филтрира метаданни и при нужда извършва различни операции в зависимост от метаданните."""
    metadata = data.get("metadata", {})
    
    if metadata.get("operation") == "tokenization":
        data["metadata"]["status"] = "Tokenizing text"
    elif metadata.get("operation") == "summarization":
        data["metadata"]["status"] = "Summarizing text"
    else:
        data["metadata"]["status"] = "Unknown operation"
    
    return data

class Pipe:
    def __init__(self, func):
        self.func = func

    def __or__(self, other):
        """ Позволява използването на pipe (|) за свързване на функции. """
        return Pipe(lambda data: other.func(self.func(data)))

    def __call__(self, data):
        """ Извиква функцията на pipe с входните данни. """
        return self.func(data)

def process_text(data):
    """Обработва текста от JSON."""
    text = data.get("data", {}).get("text", "")
    if text:
        processed_text = text.lower()
        data["data"]["text"] = processed_text
    return data

def filter_metadata(data):
    """Филтрира метаданни и настройва операцията според текущото състояние."""
    metadata = data.get("metadata", {})
    if metadata.get("operation") == "tokenization":
        data["metadata"]["status"] = "Tokenizing text"
    elif metadata.get("operation") == "summarization":
        data["metadata"]["status"] = "Summarizing text"
    else:
        data["metadata"]["status"] = "Unknown operation"
    return data

# Примерен JSON
data = {
    "data": {
        "text": "Това е примерен текст за обработка.",
        "numbers": [1, 2, 3, 4, 5],
        "timestamp": "2025-03-30"
    },
    "metadata": {
        "language": "bg",
        "operation": "tokenization"
    }
}

# Създаване на pipeline
result = (Pipe(lambda data: data)  # Започваме с входния JSON
          | process_text           # Обработваме текста
          | extract_numbers        # Обработваме числата
          | filter_metadata        # Филтрираме метаданните
          | display_results)       # Показваме резултатите

# Стартиране на pipeline
result(data)
