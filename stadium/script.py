# Episode 2: how 5G finds your phone in a stadium of 50,000 people.
SCENES = [
    ("hook", [
        "Fifty thousand people. One stadium. Everyone filming the same goal, at the exact same second.",
        "So how does the network find your phone in that crowd?",
    ]),
    ("pizza", [
        "A cell tower's bandwidth is like a pizza. Every phone gets a slice.",
        "Fifty thousand phones? That's a very thin slice.",
    ]),
    ("smallcells", [
        "So stadiums cheat. Instead of one big tower, they hide hundreds of small antennas under seats, on railings, and in the roof.",
        "Each one covers just a few sections. And every one of them gets a whole pizza.",
    ]),
    ("sweep", [
        "Then 5G does something wild. The antenna fires narrow beams in different directions, one after another, like a lighthouse.",
        "Your phone reports which beam hit it hardest. Now the antenna knows exactly where to aim.",
    ]),
    ("mimo", [
        "With dozens of tiny antenna elements, it can aim separate beams at different people, at the same time, on the same frequency.",
    ]),
    ("scheduler", [
        "And a scheduler hands out tiny time slots, less than a millisecond each, so everyone gets a turn.",
    ]),
    ("outro", [
        "That's how your goal video uploads. Most of the time.",
        "Follow for more tech nobody explains.",
    ]),
]

CAPTIONS = {
    "Fifty thousand": "50,000",
}

# Timed moments: name -> (scene, line index, offset seconds, sound effect)
MARKS = {
    "goal": ("hook", 0, 2.6, "cheer"),
    "lock": ("sweep", 1, 2.2, "blip"),
    "stall": ("outro", 0, 2.0, None),
}
