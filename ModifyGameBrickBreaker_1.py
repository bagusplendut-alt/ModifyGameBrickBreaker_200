import tkinter as tk
import random

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


#merubah pada bagian bola dengan earna oranye kuning merah dan memberikan efek api
class Ball(GameObject):
    # warna ekor api: dari kuning terang -> merah -> gelap
    TRAIL_COLORS = ["#ffee55", "#ffc233", "#ff9922", "#ff6611",
                    "#dd3300", "#992200", "#661100"]
    # warna tepi bola yang berkedip
    FLICKER = ["#ff3300", "#ff4400", "#ff5500", "#ff2200"]

    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 14
        self.trail = []

        # lapisan luar bola api
        item = canvas.create_oval(
            x - self.radius,
            y - self.radius,
            x + self.radius,
            y + self.radius,
            fill="#ff3300",
            outline="#ff9900",
            width=2,
        )
        # lapisan dalam: oranye, kuning, putih (inti api)
        self.inner_parts = [
            canvas.create_oval(x - 7, y - 7, x + 7, y + 7,
                               fill="#ff9900", outline=""),
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                               fill="#ffdd33", outline=""),
            canvas.create_oval(x - 2, y - 2, x + 2, y + 2,
                               fill="#ffffff", outline=""),
        ]
        super(Ball, self).__init__(canvas, item)

    def move(self, x, y):
        # gerakkan lapisan luar dan semua lapisan dalam
        super(Ball, self).move(x, y)
        for part in self.inner_parts:
            self.canvas.move(part, x, y)

    def delete(self):
        super(Ball, self).delete()
        for part in self.inner_parts:
            self.canvas.delete(part)
        for item, _ in self.trail:
            self.canvas.delete(item)
        self.trail = []

    def add_trail(self):
        # tambah satu "percikan api" di posisi bola saat ini
        coords = self.get_position()
        cx = (coords[0] + coords[2]) / 2
        cy = (coords[1] + coords[3]) / 2
        r = self.radius * 0.9
        t = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=self.TRAIL_COLORS[0], outline="",
        )
        self.canvas.tag_lower(t, self.item)  # taruh di belakang bola
        self.trail.append([t, 0])

    def fade_trail(self):
        # kecilkan dan ubah warna percikan api seiring waktu
        for entry in self.trail[:]:
            entry[1] += 1
            item, age = entry
            if age >= len(self.TRAIL_COLORS):
                self.canvas.delete(item)
                self.trail.remove(entry)
            else:
                c = self.canvas.coords(item)
                cx = (c[0] + c[2]) / 2
                cy = (c[1] + c[3]) / 2
                r = self.radius * 0.9 * (1 - age / len(self.TRAIL_COLORS))
                self.canvas.coords(item, cx - r, cy - r, cx + r, cy + r)
                self.canvas.itemconfig(item, fill=self.TRAIL_COLORS[age])

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1

        self.fade_trail()
        self.add_trail()

        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)
        # efek api berkedip
        self.canvas.itemconfig(self.item, fill=random.choice(self.FLICKER))

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(
            x - self.width / 2,
            y - self.height / 2,
            x + self.width / 2,
            y + self.height / 2,
            fill="yellow",
        )
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: "#e74c3c", 2: "#3498db", 3: "#222222"}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(
            x - self.width / 2,
            y - self.height / 2,
            x + self.width / 2,
            y + self.height / 2,
            fill=color,
            tags="brick",
        )
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(
            self,
            bg="#aaaaff",
            width=self.width,
            height=self.height,
        )
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle
        rows = 7  # jumlah baris balok, ubah sesuai selera
        for row in range(rows):
            y = 50 + row * 20
            if row == 0:
                hits = 3      # hitam, 3x pukul
            elif row < 3:
                hits = 2      # biru, 2x pukul
            else:
                hits = 1      # merah, 1x pukul
            for x in range(5, self.width - 5, 75): 
                self.add_brick(x + 37.5, y, hits)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind("<Left>", lambda _: self.paddle.move(-10))
        self.canvas.bind("<Right>", lambda _: self.paddle.move(10))

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, "Press Space to start")
        self.canvas.bind("<space>", lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size="40"):
        font = ("Forte", size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_lives_text(self):
        text = "Lives: %s" % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind("<space>")
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag("brick"))
        if num_bricks == 0:
            self.ball.speed = 0
            self.draw_text(300, 200, "You win!")
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = 0
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, "You Lose!!! Game Over!")
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Hello, Jarvis!")
    game = Game(root)
    game.mainloop() 