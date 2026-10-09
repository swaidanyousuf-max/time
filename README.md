# Day of the Week Finder

A small Python app with a [Dear ImGui](https://github.com/ocornut/imgui) interface
(via [imgui-bundle](https://github.com/pthom/imgui_bundle)). Pick a month, day and
year and it tells you which day of the week that date falls on.

## Features
- Weekday computed with Zeller's congruence (checked against Python's `datetime`)
- Day slider limited to the real length of the month, leap years included
- Animated gradient background with floating glowing orbs
- Rainbow wavy title, pulsing button glow, card slide-in on launch
- Slot-machine weekday spin, an elastic "pop" when it lands, and a confetti burst
- The window shakes if the year is out of range (1 to 9999)
- **Today** button, and **Enter** reveals the day

## Run
```bash
pip install -r requirements.txt
python day_of_week.py
```
