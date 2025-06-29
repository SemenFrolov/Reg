import zmq
import getpass
import sys

def create_socket():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # Таймаут 5 секунд
    socket.setsockopt(zmq.LINGER, 0)      # Не ждать при закрытии
    socket.connect("tcp://server:5555")  # На клиенте подсоединяемся к серверу
    return socket, context

def send_message(socket, message):
    try:
        socket.send_string(message)
        return socket.recv_string()
    except zmq.Again:
        return "Сервер не отвечает (таймаут)"
    except zmq.ZMQError as e:
        return f"Ошибка соединения: {str(e)}"

def main():
    socket, context = create_socket()
    
    try:
        while True:
            print("\n1. Registration\n2. Login\n3. Exit")
            choice = input("Chose option: ").strip()
            
            if choice == "3":
                break
                
            if choice in ("1", "2"):
                username = input("Username: ").strip()
                password = input("Password: ")
                
                if not username or not password:
                    print("Username and password can not be empty")
                    continue
                    
                command = "register" if choice == "1" else "login"
                message = f"{command}:{username}:{password}"
                
                response = send_message(socket, message)
                print(f"Server: {response}")
                
                # Пересоздаем сокет после каждого запроса
                socket.close()
                socket, context = create_socket()
            else:
                print("Wrong messege, try again")
                
    except KeyboardInterrupt:
        print("\nExit")
    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    main()