"""Day of the Week Finder.

Enter a month, day and year and the app shows which day of the week it
falls on, in an animated dark dashboard built with Dear ImGui (imgui-bundle).

Run:  pip install -r requirements.txt
      python day_of_week.py
"""

import calendar
import datetime
import math
import random

from imgui_bundle import hello_imgui, imgui, immapp

ImVec2 = imgui.ImVec2
ImVec4 = imgui.ImVec4

MONTHS = list(calendar.month_name)[1:]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MIN_YEAR, MAX_YEAR = datetime.MINYEAR, datetime.MAXYEAR

# Palette: warm near-black with a single orange accent
BG = (0.055, 0.050, 0.047)
CARD = (0.115, 0.105, 0.098)
TEXT = (0.96, 0.95, 0.93)
MUTED = (0.58, 0.56, 0.53)
ORANGE = (0.96, 0.52, 0.16)
AMBER = (0.99, 0.70, 0.28)

PHRASES = [
    "Just ask me any date",
    "What day was July 4, 1776?",
    "Pick a month, day and year",
    "I'll tell you the weekday",
]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def ease_out_cubic(t):
    return 1 - (1 - clamp(t, 0, 1)) ** 3


def approach(cur, target, dt, speed=8.0):
    return cur + (target - cur) * (1 - math.exp(-speed * dt))


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def day_of_week(year, month, day):
    """Return the weekday index (Monday=0) using Zeller's congruence."""
    if month < 3:
        month += 12
        year -= 1
    k, j = year % 100, year // 100
    h = (day + (13 * (month + 1)) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    # Zeller: 0 = Saturday ... 6 = Friday  ->  convert to Monday = 0
    return (h + 5) % 7


class Dust:
    """Warm specks of light drifting through the background spotlight."""

    def __init__(self, w, h):
        self.x, self.y = random.uniform(0, w), random.uniform(0, h)
        self.r = random.uniform(0.8, 2.2)
        self.vy = random.uniform(-14, -4)
        self.vx = random.uniform(-4, 4)
        self.phase = random.uniform(0, math.tau)

    def update(self, dt, w, h):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y < -5:
            self.y, self.x = h + 5, random.uniform(0, w)


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class App:
    def __init__(self):
        today = datetime.date.today()
        self.month, self.day, self.year = today.month - 1, today.day, today.year
        self.t = 0.0
        self.alpha = 1.0  # fade multiplier applied to everything drawn by col()
        self.dust = []

        # Animated display values
        self.gauge = 0.0
        self.month_bars = [0.0] * 12
        self.year_bars = [0.0] * 9
        self.doy_disp = 0.0
        self.diff_disp = 0.0
        self.pulse = 0.0

    # ---------------- drawing primitives ----------------
    def col(self, c, a=1.0):
        return imgui.color_convert_float4_to_u32(ImVec4(c[0], c[1], c[2], a * self.alpha))

    def text(self, dl, x, y, s, size, c=TEXT, a=1.0, align=0.0):
        """Draw text at (x, y); align 0 = left, 0.5 = centre, 1 = right."""
        if align:
            x -= self.text_w(s, size) * align
        dl.add_text(imgui.get_font(), size, ImVec2(x, y), self.col(c, a), s)

    @staticmethod
    def text_w(s, size):
        imgui.push_font(None, size)
        w = imgui.calc_text_size(s).x
        imgui.pop_font()
        return w

    def card(self, dl, x, y, w, h, title, glyph, note=""):
        dl.add_rect_filled(ImVec2(x, y + 6), ImVec2(x + w, y + h + 6), self.col((0, 0, 0), 0.25), 18)
        dl.add_rect_filled(ImVec2(x, y), ImVec2(x + w, y + h), self.col(CARD, 0.82), 18)
        dl.add_rect(ImVec2(x, y), ImVec2(x + w, y + h), self.col((1, 1, 1), 0.07), 18, 1.0)
        self.icon(dl, x + 28, y + 28, glyph)
        self.text(dl, x + 50, y + 19, title, 17)
        if note:
            self.text(dl, x + w - 16, y + 22, note, 12, MUTED, align=1.0)

    def icon(self, dl, cx, cy, glyph, active=False, r=14):
        bg = (0.93, 0.92, 0.90) if active else (1, 1, 1)
        dl.add_circle_filled(ImVec2(cx, cy), r, self.col(bg, 0.92 if active else 0.08), 32)
        fg = self.col((0.1, 0.09, 0.08)) if active else self.col(TEXT, 0.9)
        if glyph == "grid":
            for i in (-1, 1):
                for j in (-1, 1):
                    dl.add_rect_filled(ImVec2(cx + i * 3.5 - 2.5, cy + j * 3.5 - 2.5),
                                       ImVec2(cx + i * 3.5 + 2.5, cy + j * 3.5 + 2.5), fg, 1.5)
        elif glyph == "cal":
            dl.add_rect(ImVec2(cx - 6, cy - 5), ImVec2(cx + 6, cy + 6), fg, 2, 1.5)
            dl.add_line(ImVec2(cx - 6, cy - 1), ImVec2(cx + 6, cy - 1), fg, 1.5)
            dl.add_rect_filled(ImVec2(cx + 1, cy + 1.5), ImVec2(cx + 4, cy + 4), self.col(ORANGE))
        elif glyph == "bars":
            for i, hh in enumerate((4, 8, 6)):
                bx = cx - 6 + i * 4.5
                dl.add_rect_filled(ImVec2(bx, cy + 6 - hh), ImVec2(bx + 3, cy + 6), fg, 1)
        elif glyph == "clock":
            dl.add_circle(ImVec2(cx, cy), 6.5, fg, 24, 1.5)
            dl.add_line(ImVec2(cx, cy), ImVec2(cx, cy - 4), fg, 1.5)
            dl.add_line(ImVec2(cx, cy), ImVec2(cx + 3, cy + 1), fg, 1.5)
        elif glyph == "wave":
            pts = [ImVec2(cx - 7 + i, cy + math.sin(i * 0.9) * 3) for i in range(15)]
            dl.add_polyline(pts, fg, 1.5, 0)
        elif glyph == "gauge":
            dl.path_arc_to(ImVec2(cx, cy + 3), 7, math.pi, math.tau, 16)
            dl.path_stroke(fg, 1.5)
            dl.add_line(ImVec2(cx, cy + 3), ImVec2(cx + 4, cy - 2), self.col(ORANGE), 1.5)
        elif glyph == "user":
            dl.add_circle(ImVec2(cx, cy - 2.5), 3, fg, 16, 1.5)
            dl.path_arc_to(ImVec2(cx, cy + 7), 6, math.pi, math.tau, 16)
            dl.path_stroke(fg, 1.5)

    def waves(self, dl, x0, x1, cy, amp, phase_speed, seed):
        """Two flowing lines (white + orange), the 'signal' look from the mockup."""
        for k, (c, a, th) in enumerate(((TEXT, 0.35, 1.2), (ORANGE, 0.9, 2.0))):
            pts = []
            n = 70
            for i in range(n + 1):
                u = i / n
                env = math.sin(u * math.pi) ** 1.5
                y = cy + amp * env * math.sin(u * (9 + k * 3) + self.t * phase_speed * (1 + k * 0.4) + seed + k)
                pts.append(ImVec2(x0 + (x1 - x0) * u, y))
            dl.add_polyline(pts, self.col(c, a), th, 0)

    def stat(self, dl, x, y, label, value):
        self.text(dl, x, y, label, 12, MUTED)
        self.text(dl, x, y + 16, value, 18)

    # ---------------- sections ----------------
    def draw_background(self, dl, w, h, dt):
        dl.add_rect_filled(ImVec2(0, 0), ImVec2(w, h), self.col(BG))
        # Breathing warm spotlight standing in for the photo in the mockup
        cx, cy = w * 0.56, h * 0.22
        breathe = 1 + 0.04 * math.sin(self.t * 0.8)
        for i in range(80, 0, -1):
            r = (30 + i * 6.5) * breathe
            c = mix((0.45, 0.28, 0.14), BG, i / 80)
            dl.add_circle_filled(ImVec2(cx, cy), r, self.col(c, 0.045), 96)
        # Fade the bottom into the base colour so the cards sit on darkness
        dl.add_rect_filled_multi_color(ImVec2(0, h * 0.35), ImVec2(w, h),
                                       self.col(BG, 0), self.col(BG, 0), self.col(BG, 1), self.col(BG, 1))
        if not self.dust:
            self.dust = [Dust(w, h) for _ in range(70)]
        for d in self.dust:
            d.update(dt, w, h)
            a = 0.10 + 0.20 * (0.5 + 0.5 * math.sin(self.t * 1.5 + d.phase))
            dl.add_circle_filled(ImVec2(d.x, d.y), d.r, self.col((1.0, 0.82, 0.62), a), 8)

    def draw_sidebar(self, dl, h):
        dl.add_rect_filled(ImVec2(16, 18), ImVec2(52, 54), self.col(ORANGE), 12)
        self.text(dl, 34, 25, "D", 22, (1, 1, 1), align=0.5)
        glyphs = ["grid", "cal", "clock", "bars", "wave"]
        for i, g in enumerate(glyphs):
            cy = 92 + i * 46
            hovered = imgui.is_mouse_hovering_rect(ImVec2(16, cy - 18), ImVec2(52, cy + 18))
            if hovered and i:
                dl.add_circle_filled(ImVec2(34, cy), 18, self.col((1, 1, 1), 0.06), 32)
            self.icon(dl, 34, cy, g, active=(i == 0), r=16)
        self.icon(dl, 34, h - 40, "user", r=16)

    def draw_header(self, dl, w):
        self.text(dl, 84, 20, "Day Finder", 16)
        self.text(dl, 84, 40, "Calendar", 12, MUTED)

        cx = w / 2
        self.text(dl, cx, 22, "Hey, need a date?", 17, align=0.5)
        # Typewriter that types and deletes the phrases in turn
        cycle = [len(p) / 16 + 1.8 + len(p) / 40 for p in PHRASES]
        t = self.t % sum(cycle)
        i = 0
        while t > cycle[i]:
            t -= cycle[i]
            i += 1
        p = PHRASES[i]
        type_t, hold = len(p) / 16, 1.8
        n = int(t * 16) if t < type_t else len(p) if t < type_t + hold else max(0, len(p) - int((t - type_t - hold) * 40))
        shown = p[:n]
        size = 30
        full_w = self.text_w(p, size)
        x = cx - full_w / 2
        if int(self.t * 2) % 2 == 0:
            dl.add_line(ImVec2(x - 6, 50), ImVec2(x - 6, 82), self.col(TEXT, 0.9), 2)
        self.text(dl, x, 50, shown, size)

        # Profile chip on the right
        ax = w - 160
        dl.add_circle_filled(ImVec2(ax, 36), 17, self.col(ORANGE), 32)
        dl.add_circle_filled(ImVec2(ax - 4, 31), 9, self.col(AMBER, 0.6), 24)
        self.text(dl, ax, 28, "DF", 14, (1, 1, 1), align=0.5)
        self.text(dl, ax + 26, 20, "Date Explorer", 15)
        self.text(dl, ax + 26, 39, "Weekday tools", 12, MUTED)

    def pill_button(self, label, x, y, w, primary=False):
        imgui.set_cursor_screen_pos(ImVec2(x, y))
        if primary:
            imgui.push_style_color(imgui.Col_.button, ImVec4(0.95, 0.94, 0.92, 1))
            imgui.push_style_color(imgui.Col_.button_hovered, ImVec4(1, 1, 1, 1))
            imgui.push_style_color(imgui.Col_.button_active, ImVec4(0.85, 0.84, 0.82, 1))
            imgui.push_style_color(imgui.Col_.text, ImVec4(0.08, 0.07, 0.06, 1))
        else:
            imgui.push_style_color(imgui.Col_.button, ImVec4(0.12, 0.11, 0.10, 0.85))
            imgui.push_style_color(imgui.Col_.button_hovered, ImVec4(0.20, 0.18, 0.16, 0.95))
            imgui.push_style_color(imgui.Col_.button_active, ImVec4(0.26, 0.23, 0.20, 1))
            imgui.push_style_color(imgui.Col_.text, ImVec4(*TEXT, 1))
        clicked = imgui.button(label, ImVec2(w, 34))
        imgui.pop_style_color(4)
        return clicked

    def card_fade(self, i):
        a = ease_out_cubic((self.t - 0.25 - i * 0.12) / 0.7)
        self.alpha = a
        imgui.get_style().alpha = max(a, 0.01)
        return (1 - a) * 24  # slide-up offset

    # ---------------- main frame ----------------
    def gui(self):
        io = imgui.get_io()
        dt = min(io.delta_time, 1 / 20)
        self.t += dt
        self.pulse = max(0.0, self.pulse - dt * 0.8)
        W, H = io.display_size.x, io.display_size.y

        imgui.set_next_window_pos(ImVec2(0, 0))
        imgui.set_next_window_size(ImVec2(W, H))
        flags = (imgui.WindowFlags_.no_decoration | imgui.WindowFlags_.no_background | imgui.WindowFlags_.no_move
                 | imgui.WindowFlags_.no_saved_settings | imgui.WindowFlags_.no_bring_to_front_on_focus
                 | imgui.WindowFlags_.no_scroll_with_mouse)
        imgui.begin("##dash", None, flags)
        dl = imgui.get_background_draw_list()

        self.alpha = 1.0
        imgui.get_style().alpha = 1.0
        self.draw_background(dl, W, H, dt)
        self.alpha = ease_out_cubic(self.t / 0.6)
        self.draw_sidebar(dl, H)
        self.draw_header(dl, W)

        # ---- data for the current selection ----
        self.year = clamp(self.year, MIN_YEAR, MAX_YEAR)
        m = self.month + 1
        max_day = calendar.monthrange(self.year, m)[1]
        self.day = clamp(self.day, 1, max_day)
        date = datetime.date(self.year, m, self.day)
        wd = day_of_week(self.year, m, self.day)
        today = datetime.date.today()
        days_in_year = 366 if calendar.isleap(self.year) else 365
        doy = date.timetuple().tm_yday
        diff = (date - today).days

        # ---- layout ----
        left, right, gap = 84, W - 20, 14
        row1_h, row2_h = 172, 156
        top = H - 20 - row2_h - gap - row1_h
        gw = (right - left) * 0.27
        cw = right - left - gw - gap
        sw = (cw - 2 * gap) / 3
        bw = (cw - gap) / 2
        gx = right - gw

        # ---- action row ----
        self.alpha = ease_out_cubic((self.t - 0.1) / 0.6)
        imgui.get_style().alpha = max(self.alpha, 0.01)
        ay = top - 50
        self.pill_button(today.strftime("%d %b %Y"), right - 370, ay, 130)
        if self.pill_button("Today", right - 230, ay, 90):
            self.month, self.day, self.year = today.month - 1, today.day, today.year
            self.reveal()
        if self.pill_button("Reveal Day", right - 130, ay, 130, primary=True) or imgui.is_key_pressed(imgui.Key.enter):
            self.reveal()

        # ---- Month card ----
        dy = self.card_fade(0)
        x, y = left, top + dy
        self.card(dl, x, y, sw, row1_h, "Month", "cal", "12 months")
        imgui.set_cursor_screen_pos(ImVec2(x + 14, y + 52))
        imgui.set_next_item_width(min(130, sw * 0.45))
        _, self.month = imgui.combo("##month", self.month, MONTHS)
        self.text(dl, x + 14, y + row1_h - 62, str(calendar.monthrange(self.year, self.month + 1)[1]), 34)
        self.text(dl, x + 14, y + row1_h - 26, "days in month", 12, MUTED)
        bx0, bx1 = x + sw * 0.52, x + sw - 16
        by0, by1 = y + 56, y + row1_h - 22
        step = (bx1 - bx0) / 12
        for i in range(12):
            days = calendar.monthrange(self.year, i + 1)[1]
            target = 0.3 + 0.7 * (days - 28) / 3
            self.month_bars[i] = approach(self.month_bars[i], target, dt, 6 + i * 0.4)
            hgt = (by1 - by0) * self.month_bars[i] * self.alpha
            sel = i == self.month
            c = ORANGE if sel else (0.55, 0.36, 0.20)
            dl.add_rect_filled(ImVec2(bx0 + i * step, by1 - hgt), ImVec2(bx0 + i * step + step * 0.6, by1),
                               self.col(c, 1 if sel else 0.55), 3)
            self.text(dl, bx0 + i * step + step * 0.3, by1 + 4, MONTHS[i][0], 10, TEXT if sel else MUTED, align=0.5)

        # ---- Day card ----
        dy = self.card_fade(1)
        x, y = left + sw + gap, top + dy
        self.card(dl, x, y, sw, row1_h, "Day", "grid", f"1 - {max_day}")
        imgui.set_cursor_screen_pos(ImVec2(x + 14, y + 52))
        imgui.set_next_item_width(sw - 28)
        _, self.day = imgui.slider_int("##day", self.day, 1, max_day)
        self.text(dl, x + 14, y + row1_h - 62, ordinal(self.day), 34)
        self.text(dl, x + 14, y + row1_h - 26, "day of month", 12, MUTED)
        # Mini calendar of the month, Monday first
        first = day_of_week(self.year, m, 1)
        gx0, gy0 = x + sw * 0.45, y + 96
        pitch_x, pitch_y = (sw * 0.55 - 16) / 7, 11
        for d in range(1, max_day + 1):
            cell = first + d - 1
            cxp, cyp = gx0 + (cell % 7) * pitch_x, gy0 + (cell // 7) * pitch_y
            if d == self.day:
                c, a = ORANGE, 1.0
            elif d < self.day:
                c, a = (0.55, 0.36, 0.20), 0.6
            else:
                c, a = (1, 1, 1), 0.12
            dl.add_rect_filled(ImVec2(cxp, cyp), ImVec2(cxp + pitch_x * 0.7, cyp + 7), self.col(c, a), 2)

        # ---- Year card ----
        dy = self.card_fade(2)
        x, y = left + 2 * (sw + gap), top + dy
        self.card(dl, x, y, sw, row1_h, "Year", "bars", "Nearby years")
        imgui.set_cursor_screen_pos(ImVec2(x + 14, y + 52))
        imgui.set_next_item_width(min(130, sw * 0.45))
        _, self.year = imgui.input_int("##year", self.year, 1, 10)
        self.year = clamp(self.year, MIN_YEAR, MAX_YEAR)
        self.text(dl, x + 14, y + row1_h - 62, str(self.year), 34)
        self.text(dl, x + 14, y + row1_h - 26, "Leap year" if calendar.isleap(self.year) else "Common year", 12, MUTED)
        bx0, bx1 = x + sw * 0.55, x + sw - 16
        by0, by1 = y + 56, y + row1_h - 22
        step = (bx1 - bx0) / 9
        for i in range(9):
            yy = self.year + i - 4
            if MIN_YEAR <= yy <= MAX_YEAR:
                dd = min(self.day, calendar.monthrange(yy, m)[1])
                target = (day_of_week(yy, m, dd) + 1) / 7
            else:
                target = 0
            self.year_bars[i] = approach(self.year_bars[i], target, dt, 7)
            hgt = (by1 - by0) * self.year_bars[i] * self.alpha
            sel = i == 4
            c = AMBER if sel else (0.62, 0.45, 0.22)
            dl.add_rect_filled(ImVec2(bx0 + i * step, by1 - hgt), ImVec2(bx0 + i * step + step * 0.55, by1),
                               self.col(c, 1 if sel else 0.5), 3)

        # ---- Year progress card ----
        dy = self.card_fade(3)
        x, y = left, top + row1_h + gap + dy
        self.card(dl, x, y, bw, row2_h, "Year Progress", "wave", "Day of year")
        self.doy_disp = approach(self.doy_disp, doy, dt, 5)
        num = str(round(self.doy_disp))
        self.text(dl, x + 16, y + 44, num, 30, ORANGE)
        self.text(dl, x + 22 + self.text_w(num, 30), y + 58, f"of {days_in_year} days", 13, MUTED)
        self.waves(dl, x + bw * 0.45, x + bw - 18, y + 66, 13, 1.6, 0)
        stats = [("Week", str(date.isocalendar()[1])), ("Quarter", f"Q{(m - 1) // 3 + 1}"),
                 ("Progress", f"{doy / days_in_year:.0%}")]
        for i, (lbl, val) in enumerate(stats):
            self.stat(dl, x + 16 + i * (bw - 32) / 3, y + row2_h - 46, lbl, val)

        # ---- From today card ----
        dy = self.card_fade(4)
        x, y = left + bw + gap, top + row1_h + gap + dy
        self.card(dl, x, y, bw, row2_h, "From Today", "clock", "Distance")
        self.diff_disp = approach(self.diff_disp, abs(diff), dt, 5)
        num = f"{round(self.diff_disp):,}"
        self.text(dl, x + 16, y + 44, num, 30, ORANGE)
        phrase = "days ago" if diff < 0 else "days ahead" if diff > 0 else "that's today"
        self.text(dl, x + 22 + self.text_w(num, 30), y + 58, phrase, 13, MUTED)
        self.waves(dl, x + bw * 0.45, x + bw - 18, y + 66, 13, 2.2, 2.0)
        ad = abs(diff)
        stats = [("Years", f"{ad / 365.2425:,.1f}"), ("Months", f"{ad / 30.44:,.0f}"), ("Weeks", f"{ad // 7:,}")]
        for i, (lbl, val) in enumerate(stats):
            self.stat(dl, x + 16 + i * (bw - 32) / 3, y + row2_h - 46, lbl, val)

        # ---- Weekday gauge card ----
        dy = self.card_fade(5)
        x, y, gh = gx, top + dy, row1_h + gap + row2_h
        if self.pulse > 0:
            for i in range(3):
                g = (i + 1) * 4 * self.pulse
                dl.add_rect(ImVec2(x - g, y - g), ImVec2(x + gw + g, y + gh + g), self.col(ORANGE, 0.25 * self.pulse), 18 + g, 2)
        self.card(dl, x, y, gw, gh, "Weekday", "gauge", "Result")
        # Weekday chips
        chip_w = (gw - 28) / 7
        for i in range(7):
            ccx = x + 14 + chip_w * (i + 0.5)
            sel = i == wd
            dl.add_circle_filled(ImVec2(ccx, y + 72), min(14, chip_w * 0.42), self.col(ORANGE if sel else (1, 1, 1), 1 if sel else 0.07), 32)
            self.text(dl, ccx, y + 64, WEEKDAYS[i][0], 13, (1, 1, 1) if sel else MUTED, align=0.5)
        # Gauge
        self.gauge = approach(self.gauge, (wd + 1) / 7, dt, 4)
        gcx, gcy = x + gw / 2, y + gh - 92
        R = min(gw * 0.40, 130)
        self.text(dl, gcx, gcy - R - 26, "Day of the week", 12, MUTED, align=0.5)
        n = 49
        for i in range(n):
            u = i / (n - 1)
            ang = math.pi + math.pi * u
            on = u <= self.gauge + 1e-6
            c = mix(AMBER, ORANGE, u) if on else (1, 1, 1)
            r0 = R * (0.80 if i % 8 == 0 else 0.84)
            dl.add_line(ImVec2(gcx + math.cos(ang) * r0, gcy + math.sin(ang) * r0),
                        ImVec2(gcx + math.cos(ang) * R, gcy + math.sin(ang) * R),
                        self.col(c, 1 if on else 0.18), 3 if on else 2)
        dl.path_arc_to(ImVec2(gcx, gcy), R + 8, math.pi, math.tau, 64)
        dl.path_stroke(self.col((1, 1, 1), 0.10), 1)
        tip = math.pi + math.pi * self.gauge
        dl.add_circle_filled(ImVec2(gcx + math.cos(tip) * (R + 8), gcy + math.sin(tip) * (R + 8)), 4, self.col(AMBER), 16)

        name = WEEKDAYS[wd]
        self.text(dl, gcx, gcy - 50, name, 34 + 4 * self.pulse, TEXT, align=0.5)
        self.text(dl, gcx, gcy - 10, f"Day {wd + 1} of 7", 13, MUTED, align=0.5)
        verb = "is" if diff == 0 else "was" if diff < 0 else "will be"
        self.text(dl, gcx, y + gh - 58, f"{MONTHS[m - 1]} {self.day}, {self.year}", 16, align=0.5)
        self.text(dl, gcx, y + gh - 36, f"{verb} a {name}", 13, MUTED, align=0.5)

        imgui.get_style().alpha = 1.0
        imgui.end()

    def reveal(self):
        """Replay the gauge sweep and count-up animations."""
        self.gauge = 0.0
        self.doy_disp = 0.0
        self.diff_disp = 0.0
        self.pulse = 1.0


def setup_style():
    style = imgui.get_style()
    style.frame_rounding = 10
    style.grab_rounding = 8
    style.popup_rounding = 12
    style.window_border_size = 0
    style.frame_border_size = 1
    style.popup_border_size = 1
    style.frame_padding = ImVec2(10, 7)
    style.item_spacing = ImVec2(8, 8)
    style.grab_min_size = 16

    C = imgui.Col_
    colors = {
        C.text: (*TEXT, 1.0),
        C.text_disabled: (*MUTED, 1.0),
        C.frame_bg: (1.0, 1.0, 1.0, 0.05),
        C.frame_bg_hovered: (1.0, 1.0, 1.0, 0.09),
        C.frame_bg_active: (1.0, 1.0, 1.0, 0.12),
        C.border: (1.0, 1.0, 1.0, 0.09),
        C.button: (1.0, 1.0, 1.0, 0.07),
        C.button_hovered: (*ORANGE, 0.80),
        C.button_active: (*ORANGE, 1.0),
        C.slider_grab: (*ORANGE, 1.0),
        C.slider_grab_active: (*AMBER, 1.0),
        C.popup_bg: (0.10, 0.09, 0.085, 0.98),
        C.header: (*ORANGE, 0.35),
        C.header_hovered: (*ORANGE, 0.55),
        C.header_active: (*ORANGE, 0.75),
        C.text_selected_bg: (*ORANGE, 0.35),
        C.nav_cursor: (*ORANGE, 0.8),
        C.scrollbar_grab: (1.0, 1.0, 1.0, 0.15),
        C.scrollbar_bg: (0, 0, 0, 0),
    }
    for idx, c in colors.items():
        style.set_color_(idx, ImVec4(*c))


def main():
    app = App()
    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = "Day of the Week Finder"
    params.app_window_params.window_geometry.size = (1280, 820)
    params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.no_default_window
    params.fps_idling.enable_idling = False  # keep animations running
    params.callbacks.setup_imgui_style = setup_style
    params.callbacks.show_gui = app.gui
    immapp.run(params)


if __name__ == "__main__":
    main()
