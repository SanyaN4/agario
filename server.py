from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import time

sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('localhost', 8080))
sock.listen(5)
sock.setblocking(False)

players = {}
conn_ids = {}
player_names = {}  # Словник для зберігання імен
id_counter = 0


def handle_data():
    global id_counter
    while True:
        time.sleep(0.01)
        player_data = {}
        to_remove = []

        for conn in list(players):
            try:
                data = conn.recv(128).decode().strip()
                if data:
                    if ',' in data:
                        parts = data.split(',')
                        if len(parts) >= 4:
                            pid = int(parts[0])
                            x = int(parts[1])
                            y = int(parts[2])
                            r = int(parts[3])
                            pname = parts[4] if len(parts) > 4 else f"Player {pid}"

                            players[conn] = {'id': pid, 'x': x, 'y': y, 'r': r, 'name': pname}
                            player_names[pid] = pname
                            player_data[conn] = players[conn]
            except:
                # Помилка на зв'язку, видаляємо клієнта
                to_remove.append(conn)
                continue

        eliminated = []

        # Логіка взаємодії гравців
        for conn1 in player_data:
            if conn1 in eliminated:
                continue
            p1 = player_data[conn1]

            for conn2 in player_data:
                if conn1 == conn2 or conn2 in eliminated:
                    continue

                p2 = player_data[conn2]

                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5

                if distance < (p1['r'] + p2['r']) and p1['r'] > p2['r'] * 1.1:
                    p1['r'] += int(p2['r'] * 0.5)
                    players[conn1] = p1
                    eliminated.append(conn2)

        # Видалити гравців, яких не має
        for conn in list(players.keys()):
            if conn in eliminated:
                try:
                    conn.send("LOSE".encode())  # Повідомляємо про програш
                except:
                    pass
                to_remove.append(conn)
                continue

            try:
                # Відправляємо актуальні дані з іменами
                packet = '|'.join([f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']}"
                                   for c, p in players.items() if c != conn and c not in eliminated]) + '|'
                conn.send(packet.encode())
            except:
                to_remove.append(conn)

        # Видалення з'єднань, що більше не підключені
        for conn in to_remove:
            pid = players.get(conn, {}).get('id')
            if pid:
                player_names.pop(pid, None)
            players.pop(conn, None)
            conn_ids.pop(conn, None)
            try:
                conn.close()
            except:
                pass


Thread(target=handle_data, daemon=True).start()
print("SERVER running...")

while True:
    try:
        conn, addr = sock.accept()
        conn.setblocking(False)

        # Отримуємо ім'я від клієнта
        try:
            player_name = conn.recv(64).decode().strip()
            if not player_name:
                player_name = f"Player {id_counter + 1}"
        except:
            player_name = f"Player {id_counter + 1}"

        id_counter += 1
        players[conn] = {'id': id_counter, 'x': 0, 'y': 0, 'r': 20, 'name': player_name}
        conn_ids[conn] = id_counter
        player_names[id_counter] = player_name

        conn.send(f"{id_counter},0,0,20".encode())  # Відправляємо початкові дані
        print(f"Підключився гравець: {player_name} (ID: {id_counter})")
    except:
        pass
