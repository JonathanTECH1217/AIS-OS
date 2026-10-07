"""The words of a song fitted to its recording, for Dictation Sheet.

Given a sound file (or captured sound) and the words as they are sung, line by line, this finds where every word is
sung: the start of each syllable, where it stops sounding, and the beats of the song. It leans on tools other people
built for exactly this:

- torchaudio's wav2vec2 speech model and its forced alignment (fitting a known text to a recording, sound by sound)
- the CMU pronouncing dictionary, a real syllable list, for how many syllables a word has
- librosa for the beats and the tempo

Run by the local server (serve.py) in a background job; `python align.py song.mp3 words.txt` runs it by hand and prints
what it found. First use downloads the speech model (about 360 MB) into torch's cache.
"""
import json
import re
import sys
import threading
import time

import numpy as np

SR = 16000            # the speech model listens at 16 kHz
FPS = 100             # loudness frames a second, as the app's own curves
CHUNK_SEC = 20        # the recording is fed to the model in pieces this long
VOWELS = "aeiouy"

_state = {"model": None, "labels": None, "dictionary": None, "cmu": None, "lock": threading.Lock()}


def _log(progress, stage, frac):
    if progress:
        try:
            progress(stage, float(frac))
        except Exception:
            pass


# ---------- sound ----------
def load_audio(path):
    """Any sound file (mp3, wav, flac, ogg, m4a where the system can read it) as mono float32 at 16 kHz."""
    import librosa
    y, sr = librosa.load(path, sr=SR, mono=True)
    return y.astype(np.float32)


def from_pcm(samples, rate):
    """Captured mono samples at the sound card's rate, as mono float32 at 16 kHz."""
    import librosa
    x = np.asarray(samples, dtype=np.float32)
    if rate != SR:
        x = librosa.resample(x, orig_sr=rate, target_sr=SR)
    return x.astype(np.float32)


# ---------- the speech model ----------
def _model():
    with _state["lock"]:
        if _state["model"] is None:
            import torch
            import torchaudio
            torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
            bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
            model = bundle.get_model().eval()
            labels = bundle.get_labels()
            _state["model"] = model
            _state["labels"] = labels
            _state["dictionary"] = {c: i for i, c in enumerate(labels)}
        return _state["model"], _state["labels"], _state["dictionary"]


def emissions(wave, progress=None):
    """Log-probabilities of every letter at every 20 ms frame, over the whole recording, fed in pieces."""
    import torch
    model, labels, _ = _model()
    n = len(wave)
    step = CHUNK_SEC * SR
    outs = []
    with torch.inference_mode():
        for i in range(0, n, step):
            piece = torch.from_numpy(wave[i:i + step])
            if len(piece) < SR // 2:
                piece = torch.nn.functional.pad(piece, (0, SR // 2 - len(piece)))
            em, _ = model(piece[None])
            outs.append(torch.log_softmax(em[0], dim=-1))
            _log(progress, "listening", min(1.0, (i + step) / n))
    em = torch.cat(outs, dim=0)
    frame_sec = n / SR / em.shape[0]
    return em, frame_sec


# ---------- words and syllables ----------
def clean_word(w):
    """The letters the model knows: A to Z and the apostrophe, upper case; None when nothing is left."""
    w = w.upper().replace("’", "'")
    w = re.sub(r"[^A-Z']", "", w)
    w = w.strip("'")
    return w or None


def _cmu():
    if _state["cmu"] is None:
        try:
            import cmudict
            _state["cmu"] = cmudict.dict()
        except Exception:
            _state["cmu"] = {}
    return _state["cmu"]


def vowel_groups(word):
    """Spans of the vowel letters in a word (lower case)."""
    return [(m.start(), m.end()) for m in re.finditer(r"[%s]+" % VOWELS, word.lower())]


def syllable_count(word):
    """How many syllables a word has: the dictionary's vowel sounds, else the vowel groups less a silent final e."""
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return 1
    cmu = _cmu()
    for key in (w, w.rstrip("'"), w[:-2] if w.endswith("'s") else None):
        if key and key in cmu:
            phones = cmu[key][0]
            n = sum(1 for p in phones if p and p[-1].isdigit())
            if key != w and w.endswith("'s") and re.search(r"(s|z|x|ch|sh)$", key):
                n += 1  # "faces" has one more than "face"
            return max(1, n)
    g = vowel_groups(w)
    n = len(g)
    if n >= 2 and w.endswith("e") and g[-1] == (len(w) - 1, len(w)):
        n -= 1
    return max(1, n)


DIGRAPHS = ("th", "sh", "ch", "ph", "wh", "ck", "ng", "qu", "gh")


def _pyphen():
    if "pyphen" not in _state:
        try:
            import pyphen
            _state["pyphen"] = pyphen.Pyphen(lang="en_US")
        except Exception:
            _state["pyphen"] = None
    return _state["pyphen"]


def split_syllables(word):
    """A word cut into its syllables, as many as the dictionary hears. The hyphenation word list cuts it first
    ("some-one", "emp-ty"); when its count matches, that is the answer. Else the cuts fall between vowel groups, a lone
    consonant going to the next syllable and a cluster splitting after its first letter (a digraph like th or ck kept
    whole); the count is made to match by dropping a silent final e, merging the closest groups, or splitting the
    widest. Returns the pieces of the word as typed."""
    n = syllable_count(word)
    low = word.lower()
    if n <= 1:
        return [word]
    hy = _pyphen()
    if hy is not None:
        core = re.sub(r"[^a-z']", "", low)
        pieces = hy.inserted(core).split("-")
        if len(pieces) == n and all(pieces):
            return _cut_like(word, pieces)
    groups = vowel_groups(low)
    if len(groups) < 1:
        return [word]
    if len(groups) > n and low.endswith("e") and groups[-1] == (len(low) - 1, len(low)):
        groups = groups[:-1]
    while len(groups) > n:
        # merge the two groups closest to each other
        best, bi = None, 0
        for i in range(len(groups) - 1):
            gap = groups[i + 1][0] - groups[i][1]
            if best is None or gap < best:
                best, bi = gap, i
        groups[bi] = (groups[bi][0], groups[bi + 1][1])
        del groups[bi + 1]
    while len(groups) < n:
        # split the widest group in two (a diphthong the dictionary hears as two)
        wi = max(range(len(groups)), key=lambda i: groups[i][1] - groups[i][0])
        a, b = groups[wi]
        if b - a < 2:
            break
        mid = (a + b) // 2
        groups[wi:wi + 1] = [(a, mid), (mid, b)]
    cuts = []
    for i in range(len(groups) - 1):
        a_end, b_start = groups[i][1], groups[i + 1][0]
        cons = b_start - a_end
        if cons <= 1:
            cuts.append(a_end)
        elif low[a_end:a_end + 2] in DIGRAPHS:
            cuts.append(a_end if cons == 2 else a_end + 2)
        else:
            cuts.append(a_end + 1)
    out, start = [], 0
    for c in cuts:
        out.append(word[start:c])
        start = c
    out.append(word[start:])
    return [p for p in out if p]


def transcript(lines):
    """The lines' words as the model reads them: one token string with | between words, and for every word its line,
    its text as typed, its cleaned form and where its letters sit in the token string. Words with no letters (a lone
    comma, a musical note sign) are kept with the word before them so no syllable is lost."""
    words = []
    tokens = []
    for li, line in enumerate(lines):
        for raw in str(line).split():
            cw = clean_word(raw)
            if not cw:
                if words and words[-1]["line"] == li:
                    words[-1]["text"] += " " + raw
                continue
            if tokens:
                tokens.append("|")
            start = len(tokens)
            tokens.extend(list(cw))
            words.append({"line": li, "text": raw, "clean": cw, "tok0": start, "tok1": len(tokens)})
    return "".join(tokens), words


# ---------- loudness, for where a syllable stops ----------
def voice_env(wave):
    """The voice band's loudness, 100 frames a second, in the app's own units (log1p of 100 x RMS)."""
    from scipy.signal import butter, sosfilt
    sos = butter(4, [250, 3500], btype="band", fs=SR, output="sos")
    v = sosfilt(sos, wave).astype(np.float32)
    hop = SR // FPS
    n = len(v) // hop
    seg = v[:n * hop].reshape(n, hop)
    rms = np.sqrt(np.mean(seg * seg, axis=1))
    return np.log1p(100.0 * rms).astype(np.float32)


def sung_end(env, t_on, t_limit, floor):
    """Where a syllable sung at t_on stops sounding: the first 50 ms below floor + 0.4 x (its body - floor), looked for
    from 60 ms after the onset up to t_limit. The body is the loudest 50 ms of the first 150 ms."""
    k_on = int(round(t_on * FPS))
    w = 5
    if k_on < 0 or k_on >= len(env):
        return t_limit
    peak = -1e9
    for j in range(k_on, min(len(env) - w, k_on + 15)):
        m = float(env[j:j + w].mean())
        if m > peak:
            peak = m
    if peak < 0 or peak - floor < 0.25:
        return t_limit
    thr = floor + 0.4 * (peak - floor)
    k_lim = int(round(t_limit * FPS))
    run = 0
    for q in range(k_on + 6, min(len(env), k_lim)):
        run = run + 1 if env[q] < thr else 0
        if run >= w:
            return (q - w + 1) / FPS
    return t_limit


# ---------- the singer out of the mix ----------
def separate_vocals(wave, progress=None):
    """The singer alone, pulled out of the mix by Demucs (htdemucs) when it is installed; else the mix as it is.
    16 kHz mono in and out. Returns (sound, separated, why)."""
    try:
        import torch
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
    except Exception as exc:
        return wave, False, "Demucs is not installed (%s)" % exc
    import librosa
    _log(progress, "separating", 0.0)
    with _state["lock"]:
        if _state.get("demucs") is None:
            _state["demucs"] = get_model("htdemucs").eval()
        model = _state["demucs"]
    sr_m = int(model.samplerate)
    x = librosa.resample(wave, orig_sr=SR, target_sr=sr_m).astype(np.float32)
    mix = torch.from_numpy(np.stack([x, x]))[None]
    ref = mix.mean(0)
    mean, std = float(ref.mean()), float(ref.std()) + 1e-8
    mix = (mix - mean) / std
    with torch.inference_mode():
        out = apply_model(model, mix, device="cpu", shifts=0, split=True, overlap=0.25, progress=False)[0]
    out = out * std + mean
    voc = out[list(model.sources).index("vocals")].mean(0).numpy().astype(np.float32)
    voc16 = librosa.resample(voc, orig_sr=sr_m, target_sr=SR).astype(np.float32)
    if len(voc16) < len(wave):
        voc16 = np.pad(voc16, (0, len(wave) - len(voc16)))
    _log(progress, "separating", 1.0)
    return voc16[:len(wave)], True, ""


# ---------- beats ----------
def tempo_from_stamps(tempo, stamps):
    """Between the tracker's tempo and its simple ratios (half, double, three quarters, four thirds, two thirds, three
    halves), the one whose bar (four beats) fits the spacing of the sung lines best: the lines of a song sit one, two
    or four bars apart (a chorus at 78 bpm has a line every bar; a tracker on its riff said 104)."""
    if not stamps or len(stamps) < 6:
        return tempo / 2 if tempo > 135 else tempo
    ts = sorted(stamps)
    gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1) if 1.2 <= ts[i + 1] - ts[i] <= 13]
    if len(gaps) < 4:
        return tempo / 2 if tempo > 135 else tempo
    hist = {}
    for g in gaps:
        k = round(g * 4) / 4
        hist[k] = hist.get(k, 0) + 1
    top = sorted(hist.items(), key=lambda kv: -kv[1])[:3]
    cands = [tempo * r for r in (1.0, 0.5, 2.0, 0.75, 4.0 / 3.0, 2.0 / 3.0, 1.5)]
    inrange = [c for c in cands if 50 <= c <= 135]
    if inrange:
        cands = inrange

    def cost(c):
        bar = 240.0 / c
        s = 0.0
        for g, n in top:
            r = g / bar
            s += n * min(abs(r - m) for m in (0.5, 1.0, 2.0, 4.0))
        return s

    best = min(cands, key=lambda c: (round(cost(c), 3), abs(c - tempo)))
    return float(best)


def smooth_beats(beats, win=9):
    """The tracker's beats with single slips taken out: every gap replaced by the middle value of the gaps around it,
    the sequence rebuilt from the first beat, then slid so it sits on the tracked beats on the whole."""
    if len(beats) < win + 2:
        return beats
    b = np.asarray(beats, dtype=float)
    gaps = np.diff(b)
    sm = np.empty_like(gaps)
    h = win // 2
    for i in range(len(gaps)):
        sm[i] = np.median(gaps[max(0, i - h):i + h + 1])
    nb = np.concatenate([[b[0]], b[0] + np.cumsum(sm)])
    nb += float(np.median(b - nb))
    return [round(float(x), 3) for x in nb]


VOTE_ON = (0.59, 0.24, 0.12, 0.06)    # a line starting on beat k: beat 1 is k, k+1 (a one-beat pickup), k+2, k+3
VOTE_OFF = (0.25, 0.60, 0.10, 0.05)   # a line starting between beats k and k+1: beat 1 is k+1 (a pickup), k, ...


def downbeat_votes(beats, starts, period):
    """Which beat of four the sung lines start on. A line starts on its downbeat most often, else as a pickup in the
    beat before it (on beat 4 or its "and"), now and then on beat 3, seldom on 2: each start hands out that much of a
    vote to the four classes (VOTE_ON for a start on a beat, VOTE_OFF for one between beats, blended across the
    middle of the beat), so a run of one-beat pickups no longer reads as a song whose beat 1 is beat 4. Four vote
    totals, or None with fewer than six lines."""
    if not starts or len(starts) < 6 or len(beats) < 8:
        return None
    votes = [0.0, 0.0, 0.0, 0.0]
    b = np.asarray(beats)
    for t in starts:
        i = int(np.searchsorted(b, t + 0.06) - 1)
        if i < 0:
            continue
        f = (t - b[i]) / period
        on = max(0.0, min(1.0, (0.5 - f) / 0.3))
        for j in range(4):
            votes[(i + j) % 4] += on * VOTE_ON[j] + (1.0 - on) * VOTE_OFF[j]
    return votes if sum(votes) >= 3 else None


def downbeat_low(wave, beats):
    """The low band's loudness (kick and bass) around each beat, by class of four: beat 1 carries the most in most
    songs, beat 3 next."""
    from scipy.signal import butter, sosfilt
    sos = butter(4, 150, btype="low", fs=SR, output="sos")
    low = np.abs(sosfilt(sos, wave)).astype(np.float32)
    win = int(0.05 * SR)
    cls = [[], [], [], []]
    for i, b in enumerate(beats):
        c = int(b * SR)
        seg = low[max(0, c - win):c + win]
        if len(seg):
            cls[i % 4].append(float(seg.mean()))
    return [float(np.mean(c)) if c else 0.0 for c in cls]


def downbeat_harmony(wave, beats, period):
    """How much the harmony changes going into each beat, by class of four: chords change on beat 1 far more often
    than on the others. The twelve pitch classes' strength (chroma) is taken over each beat, and the change into a
    beat is one minus the cosine similarity of its chroma to the beat before's."""
    import librosa
    hop = 512
    chroma = librosa.feature.chroma_stft(y=wave, sr=SR, hop_length=hop)
    n = chroma.shape[1]
    frames = np.clip(librosa.time_to_frames(np.asarray(beats), sr=SR, hop_length=hop), 0, max(0, n - 1))
    per = max(1, int(round(period * SR / hop)))
    cols = []
    for i in range(len(beats)):
        f0 = int(frames[i])
        f1 = int(frames[i + 1]) if i + 1 < len(beats) else min(n, f0 + per)
        cols.append(np.median(chroma[:, f0:max(f0 + 1, f1)], axis=1))
    cls = [[], [], [], []]
    for i in range(1, len(cols)):
        a, b = cols[i - 1], cols[i]
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        if na < 1e-6 or nb < 1e-6:
            continue
        cls[i % 4].append(1.0 - float(np.dot(a, b) / (na * nb)))
    return [float(np.mean(c)) if c else 0.0 for c in cls]


def downbeat_of(wave, beats, period, starts):
    """Which beat of four is beat 1, from three readings put together: where the sung lines start (weight 1), the low
    band on the beats (0.7) and the harmonic change into the beats (0.7). Each reading's four class scores are set to
    mean 0 and spread 1, then scaled by how clear that reading is (the margin of its best class over its runner-up,
    against their sum), so a flat reading says little and a clear one speaks up; the class with the biggest total is
    beat 1. sure is the total's margin over the runner-up against what full agreement of the readings that spoke
    would give: readings that contradict each other leave it low, and the page then does not act on it. Returns
    (phase, sure, cues) with the raw class scores of each reading."""
    cues = {}
    votes = downbeat_votes(beats, starts, period)
    if votes:
        cues["lines"] = (1.0, votes)
    if len(beats) >= 8:
        try:
            cues["low"] = (0.7, downbeat_low(wave, beats))
        except Exception:
            pass
        try:
            cues["harmony"] = (0.7, downbeat_harmony(wave, beats, period))
        except Exception:
            pass
    total = np.zeros(4)
    spoke = 0.0  # the weight that had something to say: each reading's weight times how clear it was
    for w, v in cues.values():
        a = np.asarray(v, dtype=float)
        sd = float(a.std())
        if not (sd > 1e-9):
            continue
        srt = sorted(a, reverse=True)
        clear = max(0.0, (srt[0] - srt[1]) / (abs(srt[0]) + abs(srt[1]) + 1e-9))
        total += w * clear * (a - a.mean()) / sd
        spoke += w * clear
    if spoke < 0.05:
        return 0, 0.0, {k: [round(float(x), 4) for x in v] for k, (w, v) in cues.items()}
    order = sorted(range(4), key=lambda k: -total[k])
    sure = max(0.0, min(1.0, float(total[order[0]] - total[order[1]]) / (1.5 * spoke)))
    return int(order[0]), round(sure, 2), {k: [round(float(x), 4) for x in v] for k, (w, v) in cues.items()}


def beats_of(wave, progress=None, stamps=None, starts=None):
    """The beats of the song in seconds, its tempo, and which beat of four is the downbeat (0 to 3): librosa's tracker
    for the pulse, the sung lines' spacing to pick the right tempo among its ratios, the grid smoothed against slips,
    and the downbeat from where the lines start together with the low band and the chord changes (downbeat_of).
    starts: where the lines are sung (the fit's own line starts); without them the lyric stamps, 0.15 s late, vote."""
    import librosa
    hop = 256
    onset = librosa.onset.onset_strength(y=wave, sr=SR, hop_length=hop)
    tempo, frames = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=hop, start_bpm=100, tightness=100)
    tempo = float(np.atleast_1d(tempo)[0])
    chosen = tempo_from_stamps(tempo, stamps)
    if abs(chosen - tempo) > 0.5:
        _, frames = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=hop, bpm=chosen, tightness=100)
    beats = librosa.frames_to_time(frames, sr=SR, hop_length=hop).astype(float).tolist()
    raw = list(beats)
    beats = smooth_beats(beats)
    _log(progress, "beats", 1.0)
    period = float(np.median(np.diff(beats))) if len(beats) > 2 else 60.0 / chosen
    if not starts and stamps:
        starts = [s + 0.15 for s in stamps]  # the voice comes in a little after the stamp
    phase, sure, cues = downbeat_of(wave, beats, period, starts)
    return {"beats": beats, "rawBeats": raw, "tempo": round(60.0 / period, 2), "trackerTempo": round(tempo, 2), "phase": phase, "phaseSure": sure, "phaseCues": cues}


# ---------- the fit itself ----------
class Span:
    __slots__ = ("start", "end", "score")

    def __init__(self, start, end, score):
        self.start, self.end, self.score = start, end, score


def fit_windows(em, lines, words, stamps, frame_sec):
    """Every line fitted inside its own window of the song: from a little before its stamp to a little after the next
    line's, so a stretch the model cannot hear (a solo, a shout) never drags the lines around it out of place. Lines with
    the same stamp share a window. Without stamps the whole song is one window. Returns one Span per letter of the
    transcript, in transcript order (frames of the whole recording), and each line's mean score."""
    import torch
    from torchaudio.functional import forced_align, merge_tokens
    _, _, dictionary = _model()
    T = em.shape[0]
    n = len(lines)
    if stamps and len(stamps) == n:
        order = sorted(range(n), key=lambda i: stamps[i])
        groups, cur = [], []
        for i in order:
            if cur and stamps[i] - stamps[cur[0]] > 0.05:
                groups.append(cur)
                cur = []
            cur.append(i)
        if cur:
            groups.append(cur)
        windows = []
        for gi, g in enumerate(groups):
            t0 = stamps[g[0]] - 0.4
            t1 = stamps[groups[gi + 1][0]] + 0.4 if gi + 1 < len(groups) else stamps[g[0]] + 12.0
            windows.append((sorted(g), t0, t1))
    else:
        windows = [(list(range(n)), 0.0, T * frame_sec)]
    # one slot per position of the whole transcript (the | between words stay empty)
    spans = [None] * (max(w["tok1"] for w in words) if words else 0)
    line_scores = {}
    for lis, t0, t1 in windows:
        ws = [w for w in words if w["line"] in lis]
        if not ws:
            continue
        toks = []
        slots = []
        for w in ws:
            if toks:
                toks.append("|")
            slots.append((len(toks), w))
            toks.extend(list(w["clean"]))
        need = int(len(toks) * 1.3) + 12
        f0 = max(0, int(t0 / frame_sec))
        f1 = min(T, int(t1 / frame_sec) + 1)
        # a window too short for its letters is widened on both sides
        while f1 - f0 < need and (f0 > 0 or f1 < T):
            f0 = max(0, f0 - 10)
            f1 = min(T, f1 + 10)
        if f1 - f0 < len(toks) + 2:
            continue
        targets = torch.tensor([[dictionary[c] for c in toks]], dtype=torch.int32)
        try:
            aligned, scores = forced_align(em[f0:f1][None], targets, blank=0)
        except Exception:
            continue
        got = merge_tokens(aligned[0], scores[0].exp())
        if len(got) != len(toks):
            continue
        for at, w in slots:
            k = w["tok1"] - w["tok0"]
            for q in range(k):
                sp = got[at + q]
                spans[w["tok0"] + q] = Span(f0 + sp.start, f0 + sp.end, float(sp.score))
        for li in lis:
            sc = [spans[q].score for w in ws if w["line"] == li for q in range(w["tok0"], w["tok1"]) if spans[q] is not None]
            line_scores[li] = float(np.mean(sc)) if sc else 0.0
    return spans, line_scores


# ---------- the whole job ----------
def align(wave, lines, progress=None, want_beats=True, stamps=None, separate=True):
    """lines: the words as sung, one string per line; stamps: each line's start in seconds of the recording (from the
    timed lyrics), or None. Returns {ok, words: [{line, text, start, end, syllables: [{text, start, end, score}]}],
    lines: [{index, text, start, end, score}], beats, tempo, phase, phaseSure, separated, frameSec}. Times in seconds
    of the recording."""
    text, words = transcript(lines)
    if not words:
        return {"ok": False, "why": "no words with letters in them"}
    if stamps is not None and len(stamps) != len(lines):
        stamps = None
    voice, separated, sep_why = (separate_vocals(wave, progress) if separate else (wave, False, "not asked"))
    _log(progress, "listening", 0.0)
    em, frame_sec = emissions(voice, progress)
    _log(progress, "fitting", 0.0)
    spans, line_scores = fit_windows(em, lines, words, stamps, frame_sec)
    missing = sorted(set(w["line"] for w in words if any(spans[q] is None for q in range(w["tok0"], w["tok1"]))))
    if missing:
        return {"ok": False, "why": "the fit could not place lines %s" % [m + 1 for m in missing[:8]]}
    _log(progress, "fitting", 1.0)
    env = voice_env(voice)
    # every word's syllables, each with the frames of its letters; the end from the loudness, never past the next start
    out_words = []
    for w in words:
        pieces = split_syllables(w["clean"])
        syls = []
        at = w["tok0"]
        for p in pieces:
            k = len(p)
            first, last = spans[at], spans[at + k - 1]
            syls.append({"text": p, "t0": first.start * frame_sec, "t1": (last.end) * frame_sec, "score": float(np.mean([spans[q].score for q in range(at, at + k)]))})
            at += k
        # the syllables' text as typed, so the sheet shows the word as written (the cleaned form only differs in case
        # and stripped marks): the typed word is cut at the same letter counts where it can be
        typed = re.sub(r"\s.*$", "", w["text"])
        typed_pieces = _cut_like(typed, pieces)
        for s, tp in zip(syls, typed_pieces):
            s["text"] = tp
        out_words.append({"line": w["line"], "text": w["text"], "syllables": syls})
    # ends: where the voice stops, bounded by the next syllable's start
    flat = [s for w in out_words for s in w["syllables"]]
    for i, s in enumerate(flat):
        nxt = flat[i + 1]["t0"] if i + 1 < len(flat) else s["t0"] + 2.0
        limit = min(nxt, s["t0"] + 2.0)
        k0 = max(0, int((s["t0"] - 0.3) * FPS))
        k1 = min(len(env), int((limit + 0.3) * FPS) + 1)
        floor = float(np.percentile(env[k0:k1], 10)) if k1 > k0 else 0.0
        end = sung_end(env, s["t0"], limit, floor)
        s["start"] = round(s["t0"], 3)
        s["end"] = round(max(s["t0"] + 0.05, end), 3)
        del s["t0"], s["t1"]
    for w in out_words:
        w["start"] = w["syllables"][0]["start"]
        w["end"] = w["syllables"][-1]["end"]
    out_lines = []
    for li, line in enumerate(lines):
        ws = [w for w in out_words if w["line"] == li]
        if ws:
            out_lines.append({"index": li, "text": line, "start": ws[0]["start"], "end": ws[-1]["end"], "score": round(line_scores.get(li, 0.0), 3)})
    res = {"ok": True, "words": out_words, "lines": out_lines, "frameSec": frame_sec, "separated": separated, "separateWhy": sep_why}
    if want_beats:
        # the lines' sung starts vote for the downbeat where the fit heard them; a line it could not hear falls
        # back to its lyric stamp
        line_starts = []
        for L in out_lines:
            if L["score"] >= 0.15:
                line_starts.append(L["start"])
            elif stamps is not None:
                line_starts.append(stamps[L["index"]] + 0.15)
        try:
            res.update(beats_of(wave, progress, stamps, line_starts or None))
        except Exception as exc:
            res["beatsWhy"] = str(exc)
    return res


def _cut_like(typed, pieces):
    """The typed word (with its capitals and apostrophes) cut into as many pieces as the cleaned word, at the matching
    letters; marks that were stripped stay with the piece before them."""
    if len(pieces) <= 1:
        return [typed]
    out, ti = [], 0
    letters = re.compile(r"[A-Za-z']")
    for pi, p in enumerate(pieces):
        need = len(p.replace("'", "")) if pi < len(pieces) - 1 else None
        if need is None:
            out.append(typed[ti:])
            break
        got, start = 0, ti
        while ti < len(typed) and got < need:
            if letters.match(typed[ti]) and typed[ti] != "'":
                got += 1
            ti += 1
        out.append(typed[start:ti])
    return [o for o in out if o] or [typed]


def hyphenated_lines(res, lines):
    """The lines as text with a hyphen inside every word the fit cut into syllables ("no-bo-dy"), so the sheet's own
    splitter makes exactly these syllables."""
    out = []
    for li, line in enumerate(lines):
        ws = [w for w in res["words"] if w["line"] == li]
        if not ws:
            out.append(str(line))
            continue
        out.append(" ".join("-".join(s["text"] for s in w["syllables"]) for w in ws))
    return out


# ---------- background job for the server ----------
class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.stage = "idle"
        self.frac = 0.0
        self.result = None
        self.error = ""
        self.started = 0.0
        self.running = False

    def status(self):
        with self.lock:
            return {"ok": True, "running": self.running, "stage": self.stage, "frac": round(self.frac, 3), "error": self.error, "done": self.result is not None, "seconds": round(time.time() - self.started, 1) if self.started else 0}

    def start(self, wave, lines, stamps=None):
        with self.lock:
            if self.running:
                return False
            self.running = True
            self.stage = "starting"
            self.frac = 0.0
            self.result = None
            self.error = ""
            self.started = time.time()

        def progress(stage, frac):
            with self.lock:
                self.stage = stage
                self.frac = frac

        def run():
            try:
                res = align(wave, lines, progress, stamps=stamps)
                if res.get("ok"):
                    res["hyphenated"] = hyphenated_lines(res, lines)
                with self.lock:
                    self.result = res
                    self.stage = "done"
                    self.frac = 1.0
            except Exception as exc:
                import traceback
                with self.lock:
                    self.error = "%s: %s" % (type(exc).__name__, exc)
                    self.stage = "failed"
                    self.result = {"ok": False, "why": self.error, "trace": traceback.format_exc()[-2000:]}
            with self.lock:
                self.running = False

        threading.Thread(target=run, daemon=True).start()
        return True


def available():
    """Whether the fitting can run here: the speech model library and the dictionary import."""
    try:
        import torch  # noqa: F401
        import torchaudio  # noqa: F401
        from torchaudio.functional import forced_align  # noqa: F401
        import librosa  # noqa: F401
        return True, ""
    except Exception as exc:
        return False, str(exc)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python align.py song.mp3 words.txt [out.json] [stamps.json] [--no-separate]")
        sys.exit(2)
    t0 = time.time()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    wave = load_audio(args[0])
    lines = [ln.strip() for ln in open(args[1], encoding="utf-8-sig") if ln.strip()]
    stamps = json.load(open(args[3], encoding="utf-8"))["stamps"] if len(args) > 3 else None
    res = align(wave, lines, lambda st, fr: print("  %s %3d%%" % (st, fr * 100), file=sys.stderr), stamps=stamps, separate="--no-separate" not in sys.argv)
    if not res.get("ok"):
        print("failed:", res.get("why"))
        sys.exit(1)
    res["hyphenated"] = hyphenated_lines(res, lines)
    print("tempo %s bpm (tracker %s), %d beats, downbeat class %s (sure %s), singer separated: %s %s, %.1f s of work" % (res.get("tempo"), res.get("trackerTempo"), len(res.get("beats", [])), res.get("phase"), res.get("phaseSure"), res.get("separated"), res.get("separateWhy", ""), time.time() - t0))
    for L in res["lines"]:
        print("line %2d  %6.2f-%6.2f  score %.2f  %s" % (L["index"] + 1, L["start"], L["end"], L["score"], L["text"][:40]))
    for w in res["words"]:
        print("%7.2f-%6.2f  %s" % (w["start"], w["end"], " ".join("%s(%.2f-%.2f %.2f)" % (s["text"], s["start"], s["end"], s["score"]) for s in w["syllables"])))
    if len(args) > 2:
        json.dump(res, open(args[2], "w", encoding="utf-8"), indent=1)
