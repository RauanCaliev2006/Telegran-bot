from cryptography.fernet import Fernet
import os
import sys

ENCRYPTED_TOKEN_FILE = "token.enc"

def generate_key():
    """Генерирует мастер-ключ. Запусти один раз, сохрани ключ в переменную окружения MASTER_KEY."""
    key = Fernet.generate_key()
    print(f"Твой MASTER_KEY (сохрани в .env или Render Environment Variables):\n{key.decode()}")
    return key

def encrypt_token(token: str, master_key: str) -> None:
    """Шифрует токен бота и сохраняет в файл token.enc"""
    f = Fernet(master_key.encode())
    encrypted = f.encrypt(token.encode())
    with open(ENCRYPTED_TOKEN_FILE, "wb") as file:
        file.write(encrypted)
    print(f"Токен зашифрован и сохранён в {ENCRYPTED_TOKEN_FILE}")

def decrypt_token(master_key: str) -> str:
    """Расшифровывает токен из файла token.enc"""
    if not os.path.exists(ENCRYPTED_TOKEN_FILE):
        raise FileNotFoundError(f"Файл {ENCRYPTED_TOKEN_FILE} не найден! Сначала зашифруй токен.")
    f = Fernet(master_key.encode())
    with open(ENCRYPTED_TOKEN_FILE, "rb") as file:
        encrypted = file.read()
    return f.decrypt(encrypted).decode()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python security.py genkey          — сгенерировать мастер-ключ")
        print("  python security.py encrypt <TOKEN>  — зашифровать токен")
        print("  python security.py decrypt          — проверить расшифровку")
        sys.exit(1)

    command = sys.argv[1]

    if command == "genkey":
        generate_key()

    elif command == "encrypt":
        if len(sys.argv) < 3:
            print("Укажи токен: python security.py encrypt <BOT_TOKEN>")
            sys.exit(1)
        master_key = os.getenv("MASTER_KEY")
        if not master_key:
            print("Сначала установи MASTER_KEY в .env или переменных окружения!")
            sys.exit(1)
        encrypt_token(sys.argv[2], master_key)

    elif command == "decrypt":
        master_key = os.getenv("MASTER_KEY")
        if not master_key:
            print("MASTER_KEY не найден!")
            sys.exit(1)
        token = decrypt_token(master_key)
        print(f"Расшифрованный токен: {token[:10]}...{token[-5:]}")
