# Agouti Simulator

A dependency-free, isometric Game of Life playground. Live cells are rendered as cat emoji (`🐈`), while empty tiles remain a quiet diamond grid.

Open `index.html` directly in a browser, or serve this directory with any static server:

```sh
python3 -m http.server 8080
```

The simulation uses Conway's classic Moore-neighborhood rules. The board supports finite or wrapping edges, mouse placement, keyboard navigation, generation stepping, play/pause, speed, randomization, clearing, and three built-in patterns.
