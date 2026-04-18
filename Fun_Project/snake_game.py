import tkinter as tk
import random
import json
import os

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
CELL      = 20          # size of each grid cell in pixels
COLS      = 25          # number of columns
ROWS      = 25          # number of rows
WIDTH     = CELL * COLS
HEIGHT    = CELL * ROWS
FPS_EASY   = 120        # ms per frame (higher = slower)
FPS_MEDIUM = 80
FPS_HARD   = 45

COLORS = {
    "bg":           "#0d0d0d",
    "grid":         "#1a1a1a",
    "snake_head":   "#00ff88",
    "snake_body":   "#00cc66",
    "snake_tail":   "#009944",
    "food":         "#ff4444",
    "food_glow":    "#ff8888",
    "bonus":        "#ffcc00",
    "bonus_glow":   "#fff0aa",
    "text":         "#ffffff",
    "text_dim":     "#666666",
    "panel_bg":     "#111111",
    "accent":       "#00ff88",
    "danger":       "#ff4444",
    "score_bg":     "#1a1a2e",
}

HIGHSCORE_FILE = "snake_highscore.json"


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE) as f:
                return json.load(f).get("highscore", 0)
        except Exception:
            pass
    return 0


def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump({"highscore": score}, f)


# ─── MAIN APP ─────────────────────────────────────────────────────────────────
class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🐍  Snake")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])

        self.highscore    = load_highscore()
        self.difficulty   = tk.StringVar(value="Medium")
        self.score        = 0
        self.running      = False
        self.paused       = False
        self.game_over    = False
        self._after_id    = None

        # Snake state
        self.snake        = []
        self.direction    = (1, 0)
        self.next_dir     = (1, 0)
        self.food         = None
        self.bonus        = None
        self.bonus_timer  = 0
        self.bonus_blink  = 0

        self._build_ui()
        self._show_start_screen()
        self._bind_keys()

    # ── UI CONSTRUCTION ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Top panel
        top = tk.Frame(self.root, bg=COLORS["panel_bg"], pady=6)
        top.pack(fill=tk.X)

        tk.Label(top, text="🐍  SNAKE", font=("Courier", 16, "bold"),
                 bg=COLORS["panel_bg"], fg=COLORS["accent"]).pack(side=tk.LEFT, padx=14)

        right_info = tk.Frame(top, bg=COLORS["panel_bg"])
        right_info.pack(side=tk.RIGHT, padx=14)

        # Score
        score_box = tk.Frame(right_info, bg=COLORS["score_bg"], padx=10, pady=2)
        score_box.pack(side=tk.LEFT, padx=6)
        tk.Label(score_box, text="SCORE", font=("Courier", 8),
                 bg=COLORS["score_bg"], fg=COLORS["text_dim"]).pack()
        self.score_lbl = tk.Label(score_box, text="0", font=("Courier", 18, "bold"),
                                   bg=COLORS["score_bg"], fg=COLORS["accent"])
        self.score_lbl.pack()

        # High score
        hi_box = tk.Frame(right_info, bg=COLORS["score_bg"], padx=10, pady=2)
        hi_box.pack(side=tk.LEFT, padx=6)
        tk.Label(hi_box, text="BEST", font=("Courier", 8),
                 bg=COLORS["score_bg"], fg=COLORS["text_dim"]).pack()
        self.hi_lbl = tk.Label(hi_box, text=str(self.highscore),
                                font=("Courier", 18, "bold"),
                                bg=COLORS["score_bg"], fg=COLORS["bonus"])
        self.hi_lbl.pack()

        # Level label
        self.level_lbl = tk.Label(right_info, text="LVL 1", font=("Courier", 11, "bold"),
                                   bg=COLORS["panel_bg"], fg=COLORS["text_dim"])
        self.level_lbl.pack(side=tk.LEFT, padx=10)

        # Canvas
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                 bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack()

        # Bottom bar
        bot = tk.Frame(self.root, bg=COLORS["panel_bg"], pady=5)
        bot.pack(fill=tk.X)

        # Difficulty selector
        tk.Label(bot, text="Difficulty:", font=("Courier", 9),
                 bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(side=tk.LEFT, padx=(14, 4))
        for val in ("Easy", "Medium", "Hard"):
            rb = tk.Radiobutton(bot, text=val, variable=self.difficulty, value=val,
                                font=("Courier", 9), bg=COLORS["panel_bg"],
                                fg=COLORS["text"], selectcolor=COLORS["bg"],
                                activebackground=COLORS["panel_bg"],
                                activeforeground=COLORS["accent"],
                                cursor="hand2")
            rb.pack(side=tk.LEFT, padx=3)

        tk.Label(bot, text="WASD / Arrows  |  P = Pause  |  R = Restart",
                 font=("Courier", 8), bg=COLORS["panel_bg"],
                 fg=COLORS["text_dim"]).pack(side=tk.RIGHT, padx=14)

    # ── KEY BINDINGS ──────────────────────────────────────────────────────────
    def _bind_keys(self):
        for key, d in [
            ("<Up>",    (0,-1)), ("<w>", (0,-1)), ("<W>", (0,-1)),
            ("<Down>",  (0, 1)), ("<s>", (0, 1)), ("<S>", (0, 1)),
            ("<Left>",  (-1,0)), ("<a>", (-1,0)), ("<A>", (-1,0)),
            ("<Right>", (1, 0)), ("<d>", (1, 0)), ("<D>", (1, 0)),
        ]:
            self.root.bind(key, lambda e, dir=d: self._set_dir(dir))

        self.root.bind("<p>", lambda e: self._toggle_pause())
        self.root.bind("<P>", lambda e: self._toggle_pause())
        self.root.bind("<r>", lambda e: self._restart())
        self.root.bind("<R>", lambda e: self._restart())
        self.root.bind("<Return>", lambda e: self._start_game() if not self.running else None)
        self.root.bind("<space>", lambda e: self._start_game() if not self.running else None)

    def _set_dir(self, d):
        # Prevent reversing
        if (d[0] + self.direction[0], d[1] + self.direction[1]) != (0, 0):
            self.next_dir = d

    # ── SCREENS ───────────────────────────────────────────────────────────────
    def _draw_grid(self):
        for x in range(0, WIDTH, CELL):
            self.canvas.create_line(x, 0, x, HEIGHT, fill=COLORS["grid"], width=1)
        for y in range(0, HEIGHT, CELL):
            self.canvas.create_line(0, y, WIDTH, y, fill=COLORS["grid"], width=1)

    def _show_start_screen(self):
        self.canvas.delete("all")
        self._draw_grid()

        # Animated snake logo
        demo = [(5+i, 12) for i in range(8)]
        for i, (cx, cy) in enumerate(demo):
            shade = COLORS["snake_head"] if i == 0 else (COLORS["snake_body"] if i < 5 else COLORS["snake_tail"])
            self._draw_cell(cx, cy, shade, tag="demo")

        # Food dot
        self._draw_food_dot(14, 12, COLORS["food"])

        cx, cy = WIDTH // 2, HEIGHT // 2
        self.canvas.create_text(cx, cy - 60, text="🐍  S N A K E",
                                 font=("Courier", 28, "bold"), fill=COLORS["accent"])
        self.canvas.create_text(cx, cy - 20, text="Classic arcade  —  eat, grow, survive",
                                 font=("Courier", 11), fill=COLORS["text_dim"])

        # Blinking start prompt
        self.canvas.create_text(cx, cy + 30, text="▶  Press ENTER or SPACE to play",
                                 font=("Courier", 13, "bold"), fill=COLORS["text"],
                                 tags="blink")

        self.canvas.create_text(cx, cy + 60,
                                 text=f"🏆  High Score: {self.highscore}",
                                 font=("Courier", 11), fill=COLORS["bonus"])

        self.canvas.create_text(cx, cy + 90,
                                 text="WASD / Arrow Keys  |  P = Pause  |  R = Restart",
                                 font=("Courier", 9), fill=COLORS["text_dim"])
        self._blink_loop()

    def _blink_loop(self):
        if self.running:
            return
        items = self.canvas.find_withtag("blink")
        for item in items:
            state = self.canvas.itemcget(item, "state")
            self.canvas.itemconfig(item, state="hidden" if state != "hidden" else "normal")
        self._after_id = self.root.after(500, self._blink_loop)

    def _show_game_over(self):
        cx, cy = WIDTH // 2, HEIGHT // 2

        # Dark overlay
        self.canvas.create_rectangle(cx-160, cy-90, cx+160, cy+110,
                                      fill="#000000", outline=COLORS["danger"],
                                      width=2, tags="overlay")

        self.canvas.create_text(cx, cy - 60, text="GAME  OVER",
                                 font=("Courier", 24, "bold"), fill=COLORS["danger"],
                                 tags="overlay")

        new_best = ""
        if self.score >= self.highscore and self.score > 0:
            new_best = "  🏆 NEW BEST!"

        self.canvas.create_text(cx, cy - 20,
                                 text=f"Score: {self.score}{new_best}",
                                 font=("Courier", 13), fill=COLORS["accent"],
                                 tags="overlay")
        self.canvas.create_text(cx, cy + 10,
                                 text=f"Best:  {self.highscore}",
                                 font=("Courier", 13), fill=COLORS["bonus"],
                                 tags="overlay")
        self.canvas.create_text(cx, cy + 55,
                                 text="R  — Restart",
                                 font=("Courier", 11, "bold"), fill=COLORS["text"],
                                 tags="overlay")
        self.canvas.create_text(cx, cy + 80,
                                 text="ESC — Quit",
                                 font=("Courier", 11), fill=COLORS["text_dim"],
                                 tags="overlay")
        self.root.bind("<Escape>", lambda e: self.root.quit())

    # ── GAME INIT ─────────────────────────────────────────────────────────────
    def _start_game(self):
        if self.running:
            return
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._init_state()
        self.running   = True
        self.game_over = False
        self._game_loop()

    def _restart(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.running   = False
        self.game_over = False
        self._init_state()
        self.running = True
        self._game_loop()

    def _init_state(self):
        self.score      = 0
        self.paused     = False
        self.direction  = (1, 0)
        self.next_dir   = (1, 0)
        self.bonus      = None
        self.bonus_timer = 0
        self.bonus_blink = 0

        # Snake starts in the middle, length 4
        mid_x = COLS // 2
        mid_y = ROWS // 2
        self.snake = [(mid_x - i, mid_y) for i in range(4)]

        self.score_lbl.config(text="0")
        self._place_food()

    def _fps(self):
        d = self.difficulty.get()
        base = {"Easy": FPS_EASY, "Medium": FPS_MEDIUM, "Hard": FPS_HARD}.get(d, FPS_MEDIUM)
        # Speed up slightly every 5 points
        speedup = (self.score // 5) * 3
        return max(base - speedup, 30)

    def _level(self):
        return self.score // 5 + 1

    # ── FOOD ──────────────────────────────────────────────────────────────────
    def _place_food(self):
        occupied = set(self.snake)
        if self.bonus:
            occupied.add(self.bonus)
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occupied]
        self.food = random.choice(free) if free else None

    def _maybe_spawn_bonus(self):
        # 20% chance to spawn a bonus after eating food (if none active)
        if self.bonus is None and random.random() < 0.20:
            occupied = set(self.snake) | {self.food}
            free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occupied]
            if free:
                self.bonus = random.choice(free)
                self.bonus_timer = 40   # ticks before it disappears
                self.bonus_blink = 0

    # ── GAME LOOP ─────────────────────────────────────────────────────────────
    def _game_loop(self):
        if not self.running or self.paused:
            return

        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Wall collision
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self._end_game()
            return

        # Self collision (ignore last tail segment which moves away)
        if new_head in self.snake[:-1]:
            self._end_game()
            return

        self.snake.insert(0, new_head)

        ate_food  = new_head == self.food
        ate_bonus = new_head == self.bonus

        if ate_food:
            self.score += 1
            self.score_lbl.config(text=str(self.score))
            self.level_lbl.config(text=f"LVL {self._level()}")
            if self.score > self.highscore:
                self.highscore = self.score
                self.hi_lbl.config(text=str(self.highscore))
                save_highscore(self.highscore)
            self._place_food()
            self._maybe_spawn_bonus()
        else:
            self.snake.pop()

        if ate_bonus and self.bonus:
            self.score += 3
            self.score_lbl.config(text=str(self.score))
            if self.score > self.highscore:
                self.highscore = self.score
                self.hi_lbl.config(text=str(self.highscore))
                save_highscore(self.highscore)
            self.bonus = None
            self.bonus_timer = 0

        # Countdown bonus timer
        if self.bonus:
            self.bonus_timer -= 1
            self.bonus_blink += 1
            if self.bonus_timer <= 0:
                self.bonus = None

        self._draw_frame()
        self._after_id = self.root.after(self._fps(), self._game_loop)

    def _end_game(self):
        self.running   = False
        self.game_over = True
        self._show_game_over()

    def _toggle_pause(self):
        if not self.running and not self.game_over:
            return
        if self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            cx, cy = WIDTH // 2, HEIGHT // 2
            self.canvas.create_rectangle(cx-100, cy-30, cx+100, cy+30,
                                          fill=COLORS["panel_bg"],
                                          outline=COLORS["accent"], width=2,
                                          tags="pause_box")
            self.canvas.create_text(cx, cy, text="⏸  PAUSED  —  P to resume",
                                     font=("Courier", 12, "bold"),
                                     fill=COLORS["accent"], tags="pause_box")
        else:
            self.canvas.delete("pause_box")
            self._game_loop()

    # ── DRAWING ───────────────────────────────────────────────────────────────
    def _draw_cell(self, cx, cy, color, tag="cell", radius=3):
        x1 = cx * CELL + 1
        y1 = cy * CELL + 1
        x2 = x1 + CELL - 2
        y2 = y1 + CELL - 2
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color,
                                      outline="", tags=tag)

    def _draw_food_dot(self, cx, cy, color):
        pad = 4
        x1 = cx * CELL + pad
        y1 = cy * CELL + pad
        x2 = cx * CELL + CELL - pad
        y2 = cy * CELL + CELL - pad
        # Glow ring
        self.canvas.create_oval(x1-2, y1-2, x2+2, y2+2,
                                  fill="", outline=COLORS["food_glow"], width=1)
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="")

    def _draw_bonus_dot(self, cx, cy):
        # Only draw on even blink ticks so it flashes when low on time
        if self.bonus_timer <= 12 and self.bonus_blink % 2 == 0:
            return
        pad = 3
        x1 = cx * CELL + pad
        y1 = cy * CELL + pad
        x2 = cx * CELL + CELL - pad
        y2 = cy * CELL + CELL - pad
        self.canvas.create_oval(x1-2, y1-2, x2+2, y2+2,
                                  fill="", outline=COLORS["bonus_glow"], width=1)
        self.canvas.create_oval(x1, y1, x2, y2,
                                  fill=COLORS["bonus"], outline="")
        # Star symbol in centre
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2
        self.canvas.create_text(mx, my, text="★", font=("Courier", 9, "bold"),
                                  fill=COLORS["bg"])

    def _draw_frame(self):
        self.canvas.delete("all")
        self._draw_grid()

        # Snake
        for i, (cx, cy) in enumerate(self.snake):
            if i == 0:
                color = COLORS["snake_head"]
            elif i < len(self.snake) * 0.4:
                color = COLORS["snake_body"]
            else:
                color = COLORS["snake_tail"]
            self._draw_cell(cx, cy, color)

        # Eyes on head
        hx, hy = self.snake[0]
        dx, dy = self.direction
        ex = hx * CELL + CELL // 2
        ey = hy * CELL + CELL // 2
        # offset eyes perpendicular to direction
        perp = (-dy, dx)
        for sign in (1, -1):
            ex2 = ex + sign * perp[0] * 4 + dx * 4
            ey2 = ey + sign * perp[1] * 4 + dy * 4
            self.canvas.create_oval(ex2-2, ey2-2, ex2+2, ey2+2,
                                     fill=COLORS["bg"], outline="")

        # Food
        if self.food:
            self._draw_food_dot(*self.food, COLORS["food"])

        # Bonus
        if self.bonus:
            self._draw_bonus_dot(*self.bonus)

        # Score ribbon at top-left during play
        self.canvas.create_text(8, 8, anchor="nw",
                                  text=f"Score {self.score}  |  Level {self._level()}",
                                  font=("Courier", 9), fill=COLORS["text_dim"])

        # Bonus hint
        if self.bonus:
            remaining = self.bonus_timer
            self.canvas.create_text(WIDTH - 8, 8, anchor="ne",
                                     text=f"★ BONUS +3  ({remaining})",
                                     font=("Courier", 9, "bold"),
                                     fill=COLORS["bonus"])


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
