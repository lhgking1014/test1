# test1

## Timer showcase
- Impact clock face with AM/PM emphasis, millisecond readout, and punchy tick/minute animations.
- Inline language toggle (Korean, English, Japanese) rewrites labels and accessibility copy on the fly.
- Clickable world map with major cities that retarget the clock and highlight day versus night.
- Dynamic day/night terminator sweeps across the map in sync with real UTC time.
- Timezone label shows the city, IANA identifier, and precise GMT offset.

## Getting started
1. Open `timer/index.html` in your browser.
2. Click the language pill to cycle through the supported languages.
3. Hover or tap on a city marker to check whether it is currently in day or night, then click to lock that timezone into the clock.

## Customisation tips
- Add more cities by extending the `cities` array in `timer/timer.js` with coordinates (0–100 for X/Y), the IANA timezone, and display names per language.
- Tweak the animation styles, day/night rules, or gradients from `timer/styles.css` to match your branding.
- The layout responds down to tablet widths; adjust the grid or spacing tokens in the `.app` ruleset if you need a denser mobile experience.
