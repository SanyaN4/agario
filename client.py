from math import hypot
from socket import socket, AF_INET, SOCK_STREAM
import pygame
from threading import Thread
from random import randint
from launcher import ConnectWindow

# ---------- CONNECT WINDOW ----------
win = ConnectWindow()
win.mainloop()

name = win.name
host = win.host
port = int(win.port)

# ---------- SOCKET ----------
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((host, port))

# Відправляємо ім'я на сервер
sock.send(name.encode())

my_data = list(map(int, sock.recv(64).decode().strip().split(',')))
my_id = my_data[0]
my_player = [my_data[1], my_data[2], my_data[3]]  # x, y, r

sock.setblocking(False)

# ---------- PYGAME ----------
pygame.init()
window = pygame.display.set_mode((1000, 1000))
clock = pygame.time.Clock()

font_big = pygame.font.Font(None, 50)
font_name = pygame.font.Font(None, 30)
food_font = pygame.font.Font(None, 20)

running = True
lose = False
all_players = []
player_names = {}  # Словник для зберігання імен гравців


# ---------- RECEIVE DATA ----------
def receive_data():
    global all_players, lose, running, player_names
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
                continue

            if data:
                players = []
                packets = data.strip("|").split("|")
                for p in packets:
                    vals = p.split(",")
                    if len(vals) >= 4:
                        pid = int(vals[0])
                        x = int(vals[1])
                        y = int(vals[2])
                        r = int(vals[3])
                        pname = vals[4] if len(vals) > 4 else f"Player {pid}"
                        players.append([pid, x, y, r])
                        player_names[pid] = pname
                all_players = players

        except:
            pass


Thread(target=receive_data, daemon=True).start()


# ---------- FOOD ----------
class Eat:
    def __init__(self, x, y, r, c):
        self.X = x
        self.Y = y
        self.radius = r
        self.color = c

    def check_collision(self, px, py, pr):
        return hypot(self.X - px, self.Y - py) <= self.radius + pr


# Початкова їжа (більше їжі для нескінченної карти)
eats = [
    Eat(
        randint(-5000, 5000),
        randint(-5000, 5000),
        10,
        (randint(0, 255), randint(0, 255), randint(0, 255))
    ) for _ in range(500)
]

# ---------- MAIN LOOP ----------
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    window.fill((255, 255, 255))

    # Масштаб (zoom)
    scale = max(0.3, min(50 / my_player[2], 1.5))

    # ---------- DRAW OTHER PLAYERS ----------
    for p in all_players:
        if p[0] == my_id:
            continue
        sx = int((p[1] - my_player[0]) * scale + 500)
        sy = int((p[2] - my_player[1]) * scale + 500)

        # Малюємо гравця
        pygame.draw.circle(window, (255, 0, 0), (sx, sy), int(p[3] * scale))

        # Малюємо ім'я гравця
        player_name = player_names.get(p[0], f"Player {p[0]}")
        name_text = font_name.render(player_name, True, (0, 0, 0))
        name_rect = name_text.get_rect(center=(sx, sy - int(p[3] * scale) - 20))
        window.blit(name_text, name_rect)

    # ---------- DRAW MY PLAYER ----------
    pygame.draw.circle(window, (0, 255, 0), (500, 500), int(my_player[2] * scale))

    # Малюємо своє ім'я
    my_name_text = font_name.render(name, True, (0, 0, 0))
    my_name_rect = my_name_text.get_rect(center=(500, 500 - int(my_player[2] * scale) - 20))
    window.blit(my_name_text, my_name_rect)

    # ---------- FOOD ----------
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.25)  # Ріст
        else:
            sx = int((eat.X - my_player[0]) * scale + 500)
            sy = int((eat.Y - my_player[1]) * scale + 500)

            # Малюємо їжу тільки якщо вона на екрані
            if -50 < sx < 1050 and -50 < sy < 1050:
                pygame.draw.circle(window, eat.color, (sx, sy), int(eat.radius * scale))

    # ---------- FOOD RESPAWN (INFINITE) ----------
    for e in to_remove:
        eats.remove(e)

        # Генеруємо нову їжу в межах видимості гравця
        new_eat = Eat(
            randint(my_player[0] - 4000, my_player[0] + 4000),
            randint(my_player[1] - 4000, my_player[1] + 4000),
            10,
            (randint(0, 255), randint(0, 255), randint(0, 255))
        )
        eats.append(new_eat)

    # Додаємо нову їжу якщо її занадто мало навколо гравця
    if len(eats) < 500:
        for _ in range(10):
            new_eat = Eat(
                randint(my_player[0] - 4000, my_player[0] + 4000),
                randint(my_player[1] - 4000, my_player[1] + 4000),
                10,
                (randint(0, 255), randint(0, 255), randint(0, 255))
            )
            eats.append(new_eat)

    # ---------- LOSE ----------
    if lose:
        t = font_big.render("YOU LOSE!", True, (255, 0, 0))
        window.blit(t, (380, 500))

    pygame.display.update()
    clock.tick(60)

    # ---------- MOVEMENT ----------
    if not lose:
        keys = pygame.key.get_pressed()
        speed = 15

        if keys[pygame.K_w]: my_player[1] -= speed
        if keys[pygame.K_s]: my_player[1] += speed
        if keys[pygame.K_a]: my_player[0] -= speed
        if keys[pygame.K_d]: my_player[0] += speed

        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]},{name}"
            sock.send(msg.encode())
        except:
            pass

pygame.quit()
