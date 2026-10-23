# Voice-over script, grouped by scene. Each scene is a list of lines.
SCENES = [
    ("hook", [
        "You're on a train doing three hundred kilometers per hour, doom scrolling.",
        "Your phone is jumping between cell towers every minute or so. And you never notice.",
        "So how does it not drop?",
    ]),
    ("cells", [
        "The network is a giant grid of cells. Each tower covers its own patch.",
        "As you move, you leave one cell, and enter the next.",
    ]),
    ("measure", [
        "Your phone never stops listening. It measures the signal from its current tower, and from the neighbors too.",
        "Then it reports those numbers back to the network.",
    ]),
    ("graph", [
        "When a neighbor beats your current tower by a few decibels, and stays ahead for a moment, the network decides.",
        "Handover time!",
    ]),
    ("handover", [
        "The new tower gets everything ready first. It reserves a slot, just for you.",
        "The old tower forwards your data across, so nothing gets lost.",
        "Then your phone jumps. The gap is only a few tens of milliseconds. Faster than a blink.",
    ]),
    ("train", [
        "High speed trains make this harder. You cross a cell in seconds, and the speed even shifts the radio frequency. That's the Doppler effect.",
        "So rail lines get towers right along the tracks, with long stretched cells. And many trains carry repeaters that boost the signal inside.",
    ]),
    ("outro", [
        "So when your call drops? Blame the tunnel, not the handover.",
        "Follow for more tech nobody explains.",
    ]),
]

# On-screen captions (same lines, but how they should be shown).
CAPTIONS = {
    "doom scrolling": "doomscrolling",
}
