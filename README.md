# Day of the Week Finder

A small Python app with a [Dear ImGui](https://github.com/ocornut/imgui) interface
(via [imgui-bundle](https://github.com/pthom/imgui_bundle)). Pick a month, day and
year and it tells you which day of the week that date falls on.

## Features
- Dark dashboard layout: icon sidebar, header with typing text, translucent cards
- One warm palette (near-black with orange and amber accents), no rainbow colors
- **Month** card: dropdown and a bar chart of month lengths
- **Day** card: slider (limited to the real month length, leap years included) and a mini calendar
- **Year** card: number input and bars showing the weekday of the same date in nearby years
- **Weekday** card: weekday chips and an animated tick gauge showing the result
- **Year Progress** and **From Today** cards: day-of-year, week, quarter and the distance from today
- Animations: staggered card entrance, gauge sweep, count-up numbers, flowing waves,
  a breathing background glow and drifting specks of light
- Weekday computed with Zeller's congruence (checked against Python's `datetime`)
- **Today** jumps to today's date; **Reveal Day** or **Enter** replays the reveal animation

## Run
```bash
pip install -r requirements.txt
python day_of_week.py
```
