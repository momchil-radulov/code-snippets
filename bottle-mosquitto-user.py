import os
import subprocess
from bottle import route, run


@route("/create_mosquitto_user/<user_string:path>")
def create_mosquitto_user(user_string):
    """
    Създава или ресетва Mosquitto потребител.

    Параметри:
    user_string (str): Стринг във формат 'име:път:парола'
    """
    print("Обработка на:", user_string)
    parts = user_string.split(":")
    if len(parts) != 3:
        print("Грешен формат на стринга. Използвайте 'име:път:парола'.")
        print("=>", user_string)
        return "error\n"

    username = parts[0]
    topic_path = parts[1]
    password = parts[2]

    passwd_file = "/etc/mosquitto/passwd"
    acl_file_path = "/etc/mosquitto/acls"

    # 1. Създаване или ресетване на парола
    print(f"Създаване/обновяване на потребител '{username}'")
    try:
        process = subprocess.run(
            ["mosquitto_passwd", "-b", passwd_file, username, password],
            capture_output=True,
            text=True,
            check=True,
        )
        if process.stdout:
            print("Изход от mosquitto_passwd:", process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Грешка при създаване/обновяване на потребител '{username}': {e.stderr}")
        return "error\n"
    except FileNotFoundError:
        print(
            "Грешка: mosquitto_passwd командата не е намерена. Уверете се, че Mosquitto е инсталиран и е в PATH."
        )
        return "error\n"

    # 2. Проверка дали вече има ACL запис
    has_acl_entry = False
    try:
        if os.path.exists(acl_file_path):
            with open(acl_file_path, "r") as f:
                acl_content = f.read()
                if f"user {username}" in acl_content:
                    has_acl_entry = True
    except Exception as e:
        print(f"Грешка при четене на ACL файла: {e}")
        return "error\n"

    # 3. Ако няма ACL за този user → добавяме ново правило
    if not has_acl_entry:
        acl_rule = f"\nuser {username}\ntopic readwrite {topic_path}/#\n"
        try:
            with open(acl_file_path, "a") as f:
                f.write(acl_rule)
            print(
                f"ACL добавен за потребител '{username}' към '{topic_path}/#'."
            )
        except IOError as e:
            print(f"Грешка при запис в ACL файла '{acl_file_path}': {e}")
            return "error\n"

    else:
        print(f"ACL за потребител '{username}' вече съществува – пропускам добавяне.")

    # 4. Рестартиране на Mosquitto
    try:
        subprocess.run(["systemctl", "reload", "mosquitto"], check=True)
        print("Reload Mosquitto.")
        return "OK\n"
    except Exception as e:
        print(f"Грешка при рестартиране на Mosquitto: {e}")
        return "error\n"


if __name__ == "__main__":
    run(host="localhost", port=8787)
