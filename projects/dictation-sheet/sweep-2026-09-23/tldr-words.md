# words

## Tested
- `words-t1.js` (from `words-t1.template.js` + `words_gen.py`, real LRC in `blurry.lrc.json`): parseLrc, syllableTexts, parseLyrics, wordsToNotes on all 60 timed lines; blind Place words (fake link + fake /lyrics with the real LRC); records vs drawn heads per line (barEvents + notePiecesAt, as the drawing does at L1315); alignLines over the song. `words_check1.py` compares each line with my sung count (output `words-t1.out.txt`).
- `words-t2.js`: 95 words (apostrophes, caps, -ed/-es, typed hyphens, numbers, punctuation, word tags), headers, blank/CRLF/tab lines, parseLrc stamp forms.
- `words-t3.js`: wordsToNotes merge rule, noUndo, `state.prefs.side`. `words-t4.js` + `words-t4b.js`: alignLines (same text, extra line, headers, repeats, blanks, long songs, the real flow with a hyphenated word). `words-t5.js` on `words_pagereal.py` (pagecheck without the virtual clock; performance.now is frozen under it, all timings read 0.0).

## Findings
- high (user report 1): the DATA is right. "You could be my someone, you could be my scene" is one timed line and gives 11 records ("some-one" from the dictionary), 6 for the phrase; the fill leaves every line's count unchanged (55 lines, identical before/after). The 8 heads are written pieces: a crafted line You@0x2 could@2x2 be@4x2 my@7x3 some@14x4 one@18x2 gives 6 records and 8 heads: my = 16th+8th (starts on an odd 16th, cut at the beat, notePiecesAt L845), some = 8th + carry over the barline (barEvents L860). Same pattern as the screenshot (a 16th beamed to "be", an untexted 8th, a tie over the barline). The blind fill puts onsets every 3 slots (You@1 could@4 be@7 my@10 some@13 ...), so that line draws 15 heads for 11 records; whole song 480 records vs ~600 heads.
- medium: splitter on the real song: 17 of 55 lines off (total 480 notes vs 479 sung only because errors cancel). Too many: shoved > sho-ved, showed > sho-wed, messed > mes-sed, there's > the-re's, real > re-al. Too few: everything's > every-thing's (2 for 3), everyone('s) > every-one (2 for 3), everybody's > every-body's (2 for 4), nobody > no-body (2 for 3), imagine > imag-ine (2 for 3). Wrong: "Nobo-," > "Nobo" + "," (a note whose lyric is a comma). Sweep: loved, lived, walked, jumped, takes, makes, where's all 2 for 1; twenty-one, ex-girlfriend, co-operate keep typed pieces whole (2 for 3/3/4); "—", "...", "&", "(x2)" each become a note; "[Chorus] la la" typed in the panel sings "[Cho-rus]". Right: you're don't I'm I'll 'Cause ’Cause, ALL CAPS, numbers (one note), someone, oceans, very, away, preoccupied, obscene, stumble, blank/CRLF/tab lines, headers.
- medium: `<mm:ss.xx>` word tags leak: parseLrc strips only `[..]` (L2827); "<00:23.09> Everything's <00:23.60> so <00:24.10> blurry" gives 8 notes, 3 of them tags. lrclib entries can carry them. Also `[00:23:50]` is dropped and "Well [I] know" loses "[I]".
- medium: alignLines drops one line on long songs when any pair is inexact: dp rows are Float32Array (L2839) but the traceback wants |dp - (diag + sim)| < 1e-6 (L2844); the rounding gap reaches 3.8e-6 past a total of 32. 70 lines with sim 0.7 in line 1 lose line 64 (0.6/0.9 lose line 32; 130 lines lose 64 or 128). Reachable today: a hyphenated LRC word ("Oh-oh-oh") gives lineText "Ohohoh" (hy pieces join with no space) vs wordsOf "oh oh oh", sim 0.667, and line 64 of 70 is unplaced (words-t4b). Blurry itself: 55 pairs, all sim 1, in order, only the 5 blank stamps unpaired.
- medium-low: wordsToNotes merge is by line index and syllable index (L959-963): a "[Verse]" header added above keeps 0 of 14 notes, a word added at the start of a line 0 of 6, an old rest record in the line 1 of 7. Kept notes keep len/dot/xs but get the fresh quarter position: 5 of 7 half notes overlap the next note (data says 8 slots, the drawing clips to 4). noUndo: stack 3 -> 3 (without it +1). It always sets `state.prefs.side = false`, also on the Place words path (quiet + noUndo), so Place words closes the Words panel. Unchanged lines keep their objects and bars; same text changes nothing.
- low: `lineText` is not on `__ds` (mirrored in the scripts). `syllableTexts('')` returns one empty syllable (parseLyrics skips blanks, so harmless).
- perf, fine: syllableTexts 55 lines / 405 words 1.4 ms (Hyphenator 23 us a word), parseLyrics 0.9 ms (550 lines 4.9 ms), wordsToNotes with render 209 ms (326 ms on a merge), alignLines 56x60 12 ms, 550x550 860 ms (textSim re-tokenizes every cell).

## Root causes
- vowelSplit L884: the silent final e is dropped only when the last vowel group is a bare trailing "e"; "ed", "es", "e's" endings keep it (sho-ved, ta-kes, the-re's).
- splitWord L907-910: any dictionary answer with 2+ pieces is final; the TeX patterns give orthographic compound breaks (every-thing, no-body, imag-ine, re-al) and no piece is re-checked for several vowel groups. Hyphenator leaves "every" whole, so the vowel fallback (e-ve-ry) only shows on the bare word.
- syllableTexts L920: a typed hyphen splits on every "-", keeps any non-empty piece (so ","), never splits pieces further; splitWord L905 returns letterless tokens as notes.
- parseLrc L2825-2827: stamp regex needs "mm:ss(.xx)", bracket strip only. alignLines L2839/L2844: Float32 table vs 1e-6 tolerance. wordsToNotes L959-963: index matching, `keep.pos = y.pos` only.
- Heads > records: notePiecesAt L845 cuts a note starting on an odd 16th at the beat; barEvents L860 carries a note over the barline. The fill (evenSpans step = 0.85*window/K, quantizeSpans) lands onsets on odd 16ths.

## Overlaps
- timing/place words: blind spread and voice onsets on odd sixteenths make every second note two heads; snapping blind onsets to the 8th grid would halve it.
- notation: the tie between the two pieces of "my" is not visible in the screenshot (heads 12 px apart); check buildEventNotes ties pieces of one event. Chip strip is right (one chip per word group, 5 chips).
- tempo (report 3): the blind path returns grid null, so bpm/time stay by design (toast says so); not a words matter.

## Fixes
- vowelSplit: treat a final e-group as silent when the tail is e, ed, es, e's or e’s, except -ed after t/d (want-ed) and -es after s, z, x, c, g, ch, sh (fa-ces).
- splitWord: after the dictionary, re-split any piece of 4+ letters that still has 2+ vowel groups (no-bo-dy, i-mag-ine), plus a small exceptions map for lyric words (every 2, everything 3, everyone 3, everybody 4, real 1, fire 1, hour 1).
- syllableTexts: glue a piece or token without a letter or digit onto the syllable before it; treat a trailing hyphen as no break and run the word through splitWord ("Nobo-," > No-bo,); optionally split typed pieces of 2+ vowel groups.
- parseLrc: also strip `<\d+:\d+(?:\.\d+)?>`; accept `[mm:ss:xx]`. alignLines: Float64Array rows (one-line change; the Float64 mirror pairs all 70).
- wordsToNotes: match lines by text (skip headers), then syllables by text in order; when a kept note gets a fresh position, reset len/dot/xs too (or lay positions from kept lengths); give autoPlaceWords an opts.keepSide.

## Confidence
High on the words findings (all reproduced in the page on the real LRC). High on the 8-heads mechanism (crafted line matches the screenshot exactly; the user's exact slots are inferred). Medium on how often the Float32 drop bites (needs a hyphenated word early and 32+ lines).
