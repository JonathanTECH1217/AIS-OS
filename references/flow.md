# Monarc Flow

Talk instead of type, in any app. Built 2026-10-03 as a stand-in for Wispr Flow that runs only on this laptop. Why it is built this way: `decisions/log.md`, 2026-10-03.

## Use it

| Do this | What happens |
|---|---|
| Hold **Ctrl+Win** and talk | A small dark pill shows at the bottom of the screen with moving bars. |
| Let go | Three dots while it writes, then the words land where the cursor is, about 1 second later. |
| Tap **Space** while holding | Hands-free: a lock shows on the pill and you can let go. Press **Ctrl+Win** again to stop. |
| **Esc** while holding or hands-free | The take is thrown away. |
| A quick tap of Ctrl+Win | Nothing. |
| Ctrl+Win plus another key (Ctrl+Win+Left) | The take is dropped and the key works as normal. |

**No text box?** When the cursor isn't in a text box (the desktop, a web page with no box picked), the words also show in a dark card above the taskbar. Click anywhere on it to copy them. It stays 5 seconds, then fades over 1.5 seconds; while your mouse is on it, it stays. Clicking it never takes the cursor from the window you were in. To tell a text box apart, Monarc Flow asks Windows' accessibility layer (UI Automation, what screen readers use) the moment you let go. If an app doesn't answer in time, that counts as "not sure", and the card shows to be safe. Each take's answer is in the log ("cursor in a text box: yes / no / not sure").

Say these out loud:
- **"Scratch that"**, on its own: takes out the sentence before it.
- **"New line"** or **"New paragraph"**, between pauses: a line break. "A new line of speakers" stays as words.

The pill also says:
- "Didn't catch that": sound came in, but no speech.
- "Mic is silent: check its mute or plug": the mic sent almost nothing. Usually the cable's mute switch is on or the plug is half out. Windows' own mute is a different setting.
- "No microphone".
- "Loading, one moment": the first few seconds after it starts.

## The tray icon

The green **F** by the clock. Right-click it for:
- **Microphone**: the Windows default, or pick one.
- **Sounds**: the soft clicks when it starts and stops listening.
- **Copy last dictation**: the last take, back on the clipboard. Use it when the words didn't land, for example in a window run as administrator, which won't take keys from a normal program.
- **Open word list**, **Open history**.
- **Start with Windows**, **Quit**.

## Make it write a word right

Open the word list (tray, or `projects/flow/words.json`) and add a line under `fixes`: what it wrote on the left, what you want on the right.

```json
"pack edge": "Pakedge",
```

Case doesn't matter on the left. It matches whole words only. It counts from the next take; no restart needed.

## What it does to the words

Parakeet, the speech model Studio uses, writes the words with periods, commas, and capitals. Then fixed rules, in order (`scripts/flow_clean.py`):

1. Take out um, uh, er, erm, ah, and hmm. "Like" and "you know" stay.
2. Take out stutters ("I I think"). Real doubles stay ("had had", "that that", "very, very").
3. "Scratch that".
4. "New line" and "new paragraph".
5. The word list.
6. No em dashes: " — " becomes ", ".
7. Spacing, a capital "I", a capital at each sentence start, and one space at the end so the next take joins on.

It does not reword a clumsy sentence. Nothing leaves the laptop.

## Settings

`projects/flow/config.json`. The tray changes the first two.

| Setting | Default | Meaning |
|---|---|---|
| `mic` | `""` | `""` is the Windows default; otherwise the mic's name |
| `sounds` | `true` | the soft clicks |
| `space_after` | `true` | one space after each take |
| `min_hold_seconds` | `0.3` | a hold shorter than this is a tap and does nothing |
| `tail_ms` | `200` | listens this long after you let go, for the end of the last word |
| `restore_clipboard_ms` | `400` | when your clipboard is put back after the paste |
| `one_go_seconds` | `15` | a take up to this long is written in one go when you let go |
| `pause_cut_seconds` | `0.8` | longer takes are cut at pauses this long and written while you talk |
| `min_piece_seconds` | `6` | the shortest piece a long take is cut into |
| `max_take_minutes` | `10` | a take ends by itself after this |
| `threads` | `4` | processor cores Parakeet uses |

A settings change needs a restart: `pythonw scripts/flow.pyw --restart`.

## Files and commands

- `scripts/flow.pyw`: the program. `--install` (icon, sounds, Desktop and Startup shortcuts, then starts it), `--check` (the mic's name and the test clip timed), `--restart`, `--quit`.
- `scripts/flow_keys.py`: the Ctrl+Win hold. It sends one blank key (0xE8) when a hold starts so Start doesn't open.
- `scripts/flow_mic.py`: the mic (opened only while you hold) and the take.
- `scripts/flow_clean.py`: the rules. Try one: `python scripts/flow_clean.py "um so I I think"`.
- `scripts/flow_paste.py`: clipboard, Ctrl+V, and putting your clipboard back. Takes are kept out of the Win+V clipboard history.
- `scripts/flow_pill.py`: the pill and the copy card.
- `scripts/flow_focus.py`: is the cursor in a text box (UI Automation through `comtypes`, installed 2026-10-03).
- `~/.monarc/flow-history.jsonl`: every take (time, seconds, what Parakeet heard, what was pasted), the last 1,000. Not in git.
- `~/.monarc/flow.log`: start, stop, paste times, and errors.

## Tests

`python projects/flow/tests/run.py` (or name some: `rules speech long card keys`).

The `card` test moves your mouse onto the card for about 2 seconds and clicks it, then puts the mouse back.

The `keys` test presses real keys into a small test window for about 20 seconds. It stops your running copy first and starts it again after. It stops early if the test window loses focus.

Results on 2026-10-03: 47 passed. Words landed 0.93 s after letting go of an 8.8 s hold. A 50 s hands-free take was out 0.68 s after it ended.

## Licenses

Parakeet TDT 0.6B v2 is CC-BY-4.0 (credit NVIDIA), as in `references/studio.md`.
