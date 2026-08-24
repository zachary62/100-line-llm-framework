# NotebookLM: upload docs, get a podcast

Section 6.1. Three focused nodes replace the one impossible "make a podcast" prompt: find the surprising nuggets, write the banter, render the audio. Design in [docs/design.md](docs/design.md).

```mermaid
flowchart LR
    analyze[AnalyzeDocs] --> write[WriteScript] --> studio[AudioStudio]
```

```bash
python main.py
```

## Sample output

**Listen to it: [podcast.wav](podcast.wav)** — 72 seconds, two synthetic hosts, generated from the three sample docs. The script below is the exact conversation you'll hear.

```
Audio saved to podcast.wav
--- Podcast Script ---
Alex: Okay, I was looking over the latest company updates and honestly, some of these metrics are wild.
Jamie: Oh yeah? Hit me. What are we looking at—another boring earnings report?
Alex: Far from it! Q3 revenue spiked by a massive 20%, and get this—it was purely on the back of AI adoption.
Jamie: Wait, really? Twenty percent just from AI? That's a massive jump for one quarter.
Alex: Right? But hold on, because the risk report dropped at the same time and tells a totally different story.
Jamie: Uh oh, what's the catch? There's always a catch.
Alex: Despite all that strong financial growth, we have a surprisingly high rate of churn specifically within the enterprise segment.
Jamie: Wait, seriously? Enterprise clients are walking? That's huge—those are our biggest accounts!
Alex: I know, right? Maybe management is hoping our new perk will keep everyone happy.
Jamie: What perk? Are we getting free lunches or something?
Alex: Better. The company is officially offering 'unlimited coffee' as their headline-grabbing new employee benefit.
Jamie: Wait, really? Unlimited coffee? That definitely solves enterprise churn. Put it on my tab, I guess!
```
