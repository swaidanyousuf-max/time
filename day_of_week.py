"""Day of the Week Finder.

Enter a month, day and year and the app reveals which day of the week it
falls on, with an animated Dear ImGui interface (via imgui-bundle).

Run:  pip install -r requirements.txt
      python day_of_week.py
"""

import calendar
import colorsys
import datetime
import math
import random

from imgui_bundle import hello_imgui, imgui, immapp

ImVec2 = imgui.ImVec2
ImVec4 = imgui.ImVec4

MONTHS = list(calendar.month_name)[1:]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MIN_YEAR, MAX_YEAR = datetime.MINYEAR, datetime.MAXYEAR

CARD_W, CARD_H = 470, 560
SPIN_DURATION = 1.6  # seconds for the slot-machine reveal


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def rgba(r, g, b, a=1.0):
    return imgui.color_convert_float4_to_u32(ImVec4(r, g, b, a))


def hsv(h, s, v, a=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return rgba(r, g, b, a)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_quint(t):
    return 1 - (1 - t) ** 5


def ease_out_elastic(t):
    if t <= 0 or t >= 1:
        return clamp(t, 0, 1)
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def day_of_week(year, month, day):
    """Return the weekday index (Monday=0) using Zeller's congruence."""
    if month < 3:
        month += 12
        year -= 1
    k, j = year % 100, year // 100
    h = (day + (13 * (month + 1)) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    # Zeller: 0 = Saturday ... 6 = Friday  ->  convert to Monday = 0
    return (h + 5) % 7


# --------------------------------------------------------------------------
# Particles
# --------------------------------------------------------------------------
class Orb:
    """A soft glowing bubble floating up the background."""

    def __init__(self, w, h, anywhere=True):
        self.reset(w, h, anywhere)

    def reset(self, w, h, anywhere=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h) if anywhere else h + 40
        self.r = random.uniform(4, 22)
        self.speed = random.uniform(12, 45)
        self.hue = random.random()
        self.phase = random.uniform(0, math.tau)

    def update(self, dt, t, w, h):
        self.y -= self.speed * dt
        self.x += math.sin(t * 0.8 + self.phase) * 10 * dt
        if self.y < -40:
            self.reset(w, h)

    def draw(self, dl, t):
        hue = self.hue + t * 0.05
        for i in range(4, 0, -1):  # layered circles = cheap glow
            dl.add_circle_filled(ImVec2(self.x, self.y), self.r * (1 + i * 0.45), hsv(hue, 0.6, 1.0, 0.035), 24)
        dl.add_circle_filled(ImVec2(self.x, self.y), self.r * 0.45, hsv(hue, 0.4, 1.0, 0.35), 24)


class Confetti:
    def __init__(self, x, y):
        angle = random.uniform(-math.pi, 0)
        speed = random.uniform(250, 650)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.rot = random.uniform(0, math.tau)
        self.spin = random.uniform(-10, 10)
        self.size = random.uniform(4, 9)
        self.hue = random.random()
        self.life = self.max_life = random.uniform(1.6, 2.8)

    def update(self, dt):
        self.vy += 700 * dt
        self.vx *= 1 - 1.2 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.spin * dt
        self.life -= dt
        return self.life > 0

    def draw(self, dl):
        a = clamp(self.life / self.max_life * 1.5, 0, 1)
        s, c = math.sin(self.rot), math.cos(self.rot)
        w, h = self.size, self.size * 0.5 * abs(math.sin(self.rot * 1.7)) + 1
        pts = [ImVec2(self.x + dx * c - dy * s, self.y + dx * s + dy * c)
               for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        dl.add_quad_filled(*pts, hsv(self.hue, 0.75, 1.0, a))


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class App:
    def __init__(self):
        today = datetime.date.today()
        self.month = today.month - 1  # combo index
        self.day = today.day
        self.year = today.year

        self.t = 0.0
        self.orbs = []
        self.confetti = []

        self.spin_t = None          # None = no reveal yet, else seconds since start
        self.result = None          # (weekday index, date)
        self.spin_start = 0
        self.burst_done = False

        self.error = ""
        self.shake = 0.0
        self.result_center = ImVec2(0, 0)

    # ---------------- logic ----------------
    def reveal(self):
        if not MIN_YEAR <= self.year <= MAX_YEAR:
            self.error = f"Year must be between {MIN_YEAR} and {MAX_YEAR}"
            self.shake = 1.0
            return
        self.error = ""
        m = self.month + 1
        wd = day_of_week(self.year, m, self.day)
        self.result = (wd, datetime.date(self.year, m, self.day))
        self.spin_start = random.randrange(7)
        self.spin_t = 0.0
        self.burst_done = False

    def set_today(self):
        today = datetime.date.today()
        self.month, self.day, self.year = today.month - 1, today.day, today.year

    # ---------------- drawing ----------------
    def draw_background(self, w, h, dt):
        dl = imgui.get_background_draw_list()
        t = self.t
        top_l = hsv(0.70 + 0.05 * math.sin(t * 0.20), 0.75, 0.22)
        top_r = hsv(0.85 + 0.05 * math.sin(t * 0.25), 0.70, 0.25)
        bot_r = hsv(0.55 + 0.05 * math.sin(t * 0.30), 0.80, 0.18)
        bot_l = hsv(0.62 + 0.05 * math.sin(t * 0.17), 0.85, 0.12)
        dl.add_rect_filled_multi_color(ImVec2(0, 0), ImVec2(w, h), top_l, top_r, bot_r, bot_l)

        if not self.orbs:
            self.orbs = [Orb(w, h) for _ in range(45)]
        for o in self.orbs:
            o.update(dt, t, w, h)
            o.draw(dl, t)

    def draw_wavy_title(self, dl, text, center_x, y, size):
        font = imgui.get_font()
        imgui.push_font(None, size)
        total = imgui.calc_text_size(text).x
        x = center_x - total / 2
        for i, ch in enumerate(text):
            cw = imgui.calc_text_size(ch).x
            dy = math.sin(self.t * 4 + i * 0.45) * 5
            col = hsv(self.t * 0.15 + i * 0.04, 0.55, 1.0)
            dl.add_text(font, size, ImVec2(x + 2, y + dy + 3), rgba(0, 0, 0, 0.35), ch)
            dl.add_text(font, size, ImVec2(x, y + dy), col, ch)
            x += cw
        imgui.pop_font()

    def centered_text(self, dl, text, cx, y, size, col):
        imgui.push_font(None, size)
        tw = imgui.calc_text_size(text).x
        imgui.pop_font()
        dl.add_text(imgui.get_font(), size, ImVec2(cx - tw / 2, y), col, text)

    def draw_result(self, dl, x0, y0, width, height):
        cx = x0 + width / 2
        cy = y0 + height / 2
        self.result_center = ImVec2(cx, cy)

        # Panel behind the result
        dl.add_rect_filled(ImVec2(x0, y0), ImVec2(x0 + width, y0 + height), rgba(1, 1, 1, 0.05), 16)
        dl.add_rect(ImVec2(x0, y0), ImVec2(x0 + width, y0 + height),
                    hsv(self.t * 0.1, 0.5, 1.0, 0.35), 16, 1.5)

        if self.spin_t is None:
            pulse = 0.5 + 0.5 * math.sin(self.t * 3)
            self.centered_text(dl, "?", cx, cy - 40 - pulse * 4, 64, rgba(1, 1, 1, 0.25 + 0.35 * pulse))
            self.centered_text(dl, "Pick a date and hit Reveal!", cx, cy + 30, 17, rgba(1, 1, 1, 0.6))
            return

        wd, date = self.result
        p = clamp(self.spin_t / SPIN_DURATION, 0, 1)
        big = 50

        if p < 1:
            # Slot machine: scroll through weekday names, decelerating onto the answer
            steps = 21 + (wd - self.spin_start) % 7
            pos = ease_out_quint(p) * steps
            idx = int(pos)
            frac = pos - idx
            dl.push_clip_rect(ImVec2(x0, cy - 45), ImVec2(x0 + width, cy + 35), True)
            for k in (-1, 0, 1):
                name = WEEKDAYS[(self.spin_start + idx + k) % 7]
                y = cy - 30 + (k - frac) * 60
                a = 1 - min(1, abs(k - frac))
                self.centered_text(dl, name, cx, y, big, hsv(self.t * 0.6 + k * 0.1, 0.5, 1.0, 0.2 + 0.8 * a))
            dl.pop_clip_rect()
            return

        # Final reveal: elastic pop + glow
        settle = clamp((self.spin_t - SPIN_DURATION) / 0.9, 0, 1)
        scale = 0.6 + 0.4 * ease_out_elastic(settle)
        name = WEEKDAYS[wd]
        size = big * scale * (1 + 0.03 * math.sin(self.t * 3))
        glow_col = hsv(self.t * 0.2, 0.6, 1.0, 0.10)
        for r in (95, 75, 55):
            dl.add_circle_filled(ImVec2(cx, cy - 8), r * scale, glow_col, 48)
        self.centered_text(dl, name, cx + 2, cy - 30 + 3, size, rgba(0, 0, 0, 0.4))
        self.centered_text(dl, name, cx, cy - 30, size, hsv(self.t * 0.2, 0.45, 1.0))

        fade = ease_out_cubic(clamp((self.spin_t - SPIN_DURATION - 0.2) / 0.6, 0, 1))
        today = datetime.date.today()
        verb = "is" if date == today else ("was" if date < today else "will be")
        line = f"{MONTHS[date.month - 1]} {date.day}, {date.year} {verb} a {name}"
        self.centered_text(dl, line, cx, cy + 35 + (1 - fade) * 15, 17, rgba(1, 1, 1, 0.85 * fade))

        if not self.burst_done:
            self.burst_done = True
            self.confetti += [Confetti(cx, cy) for _ in range(140)]

    def draw_card(self, w, h, dt):
        # Entrance animation: slide up + fade in
        intro = ease_out_cubic(clamp(self.t / 1.0, 0, 1))
        self.shake = max(0.0, self.shake - dt * 2.5)
        shake_x = math.sin(self.t * 55) * 14 * self.shake

        imgui.set_next_window_pos(ImVec2(w / 2 + shake_x, h / 2 + (1 - intro) * 80), imgui.Cond_.always, ImVec2(0.5, 0.5))
        imgui.set_next_window_size(ImVec2(CARD_W, CARD_H))
        imgui.set_next_window_bg_alpha(0.0)
        imgui.push_style_var(imgui.StyleVar_.alpha, intro)
        flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_move
                 | imgui.WindowFlags_.no_collapse | imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_saved_settings)
        imgui.begin("##card", None, flags)

        dl = imgui.get_window_draw_list()
        wp, ws = imgui.get_window_pos(), imgui.get_window_size()
        # Glassy card with an animated rainbow border
        dl.add_rect_filled(ImVec2(wp.x + 6, wp.y + 10), ImVec2(wp.x + ws.x + 6, wp.y + ws.y + 10), rgba(0, 0, 0, 0.30 * intro), 22)
        dl.add_rect_filled(wp, ImVec2(wp.x + ws.x, wp.y + ws.y), rgba(0.08, 0.07, 0.16, 0.82 * intro), 22)
        dl.add_rect(wp, ImVec2(wp.x + ws.x, wp.y + ws.y), hsv(self.t * 0.12, 0.6, 1.0, 0.8 * intro), 22, 2.5)

        cx = wp.x + ws.x / 2
        self.draw_wavy_title(dl, "What Day Is It?", cx, wp.y + 26, 38)
        self.centered_text(dl, "Discover the day of the week for any date", cx, wp.y + 78, 15, rgba(1, 1, 1, 0.55))

        imgui.set_cursor_pos(ImVec2(40, 120))
        label_w = 70
        field_w = CARD_W - 80 - label_w

        def label(text):
            imgui.align_text_to_frame_padding()
            imgui.text_colored(ImVec4(0.75, 0.70, 1.0, 1.0), text)
            imgui.same_line(40 + label_w)
            imgui.set_next_item_width(field_w)

        # Month
        imgui.set_cursor_pos_x(40)
        label("Month")
        _, self.month = imgui.combo("##month", self.month, MONTHS)

        # Year (asked before day so the day slider knows about leap years)
        imgui.dummy(ImVec2(0, 6))
        imgui.set_cursor_pos_x(40)
        label("Year")
        _, self.year = imgui.input_int("##year", self.year, 1, 10)
        self.year = clamp(self.year, MIN_YEAR - 1, MAX_YEAR + 1)  # allow out-of-range to show error

        # Day (limited to the real number of days in the month)
        valid_year = clamp(self.year, MIN_YEAR, MAX_YEAR)
        max_day = calendar.monthrange(valid_year, self.month + 1)[1]
        self.day = clamp(self.day, 1, max_day)
        imgui.dummy(ImVec2(0, 6))
        imgui.set_cursor_pos_x(40)
        label("Day")
        _, self.day = imgui.slider_int("##day", self.day, 1, max_day)

        # Buttons
        imgui.dummy(ImVec2(0, 14))
        imgui.set_cursor_pos_x(40)
        bw = CARD_W - 80
        pulse = 0.5 + 0.5 * math.sin(self.t * 4)
        bp = imgui.get_cursor_screen_pos()
        for i in range(3, 0, -1):  # pulsing glow around the main button
            g = i * 3 + pulse * 4
            dl.add_rect_filled(ImVec2(bp.x - g, bp.y - g), ImVec2(bp.x + bw * 0.68 + g, bp.y + 44 + g),
                               hsv(self.t * 0.12, 0.6, 1.0, 0.06), 14 + g)
        if imgui.button("Reveal the Day!", ImVec2(bw * 0.68, 44)) or imgui.is_key_pressed(imgui.Key.enter):
            self.reveal()
        imgui.same_line()
        if imgui.button("Today", ImVec2(bw * 0.32 - imgui.get_style().item_spacing.x, 44)):
            self.set_today()

        if self.error:
            imgui.set_cursor_pos_x(40)
            imgui.text_colored(ImVec4(1.0, 0.45, 0.5, 1.0), self.error)

        # Result area
        ry = wp.y + 345
        self.draw_result(dl, wp.x + 30, ry, ws.x - 60, ws.y - (ry - wp.y) - 30)

        imgui.end()
        imgui.pop_style_var()

    def gui(self):
        io = imgui.get_io()
        dt = min(io.delta_time, 1 / 20)
        self.t += dt
        if self.spin_t is not None:
            self.spin_t += dt
        w, h = io.display_size.x, io.display_size.y

        self.draw_background(w, h, dt)
        self.draw_card(w, h, dt)

        fg = imgui.get_foreground_draw_list()
        self.confetti = [c for c in self.confetti if c.update(dt)]
        for c in self.confetti:
            c.draw(fg)


def setup_style():
    style = imgui.get_style()
    style.window_rounding = 22
    style.frame_rounding = 10
    style.grab_rounding = 10
    style.popup_rounding = 12
    style.window_border_size = 0
    style.frame_padding = ImVec2(12, 9)
    style.item_spacing = ImVec2(10, 8)
    style.grab_min_size = 18

    C = imgui.Col_
    colors = {
        C.text: (0.95, 0.94, 1.00, 1.00),
        C.frame_bg: (0.20, 0.17, 0.36, 0.85),
        C.frame_bg_hovered: (0.30, 0.24, 0.52, 0.90),
        C.frame_bg_active: (0.38, 0.28, 0.64, 1.00),
        C.button: (0.52, 0.30, 0.92, 1.00),
        C.button_hovered: (0.64, 0.42, 1.00, 1.00),
        C.button_active: (0.42, 0.22, 0.80, 1.00),
        C.slider_grab: (0.95, 0.50, 0.85, 1.00),
        C.slider_grab_active: (1.00, 0.65, 0.92, 1.00),
        C.popup_bg: (0.12, 0.10, 0.22, 0.97),
        C.header: (0.52, 0.30, 0.92, 0.60),
        C.header_hovered: (0.64, 0.42, 1.00, 0.80),
        C.header_active: (0.42, 0.22, 0.80, 1.00),
        C.border: (0.60, 0.45, 1.00, 0.40),
    }
    for idx, col in colors.items():
        style.set_color_(idx, ImVec4(*col))


def main():
    app = App()
    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "Day of the Week Finder"
    params.app_window_params.window_geometry.size = (760, 720)
    params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.no_default_window
    params.fps_idling.enable_idling = False  # keep animations running
    params.callbacks.setup_imgui_style = setup_style
    params.callbacks.show_gui = app.gui
    immapp.run(params)


if __name__ == "__main__":
    main()
