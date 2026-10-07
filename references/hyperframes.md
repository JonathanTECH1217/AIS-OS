# HyperFrames and the tools like it (read 2026-10-06)

Jonathan, 2026-10-06, for the Loom B and A skill: "We want to search the internet for things like hyper frames." This is what was found, in one page. The Loom B and A skill runs today on ffmpeg and Playwright, which are on this laptop; HyperFrames is the step up and waits on one install.

## HyperFrames

- What it is: HeyGen's open-source framework that turns HTML, CSS, and JavaScript into an MP4. A video is a folder of web files with timing attributes on the elements (`data-start`, `data-duration`, tracks); GSAP, CSS, Lottie, and Three.js animations are seeked frame by frame in headless Chrome and encoded by ffmpeg, so the same source gives the same file every time. Apache-2.0, no per-render fee, no account needed for local renders.
- Built for coding agents: `npx skills add heygen-com/hyperframes` installs its skills into Claude Code (also a plugin for Claude Code, Cursor, Copilot, Gemini CLI). The agent writes the HTML; `npx hyperframes preview` shows it; `npx hyperframes render --output video.mp4` makes the file. Its docs have a workflow for exactly this skill's job: "Add captions or repackage footage" and "Editing existing videos" with editor verbs (trim, move, swap), and "Captions and talking-head footage".
- Needs: Node.js 22 or newer, a Chrome or Edge, ffmpeg. This laptop has Edge and ffmpeg and no Node (checked 2026-10-06). One line puts Node on: `winget install OpenJS.NodeJS.LTS` (free). Installing is his call (social content rule: no install without a go). The docs name Mac and Linux for the Studio app; the CLI is Node and runs on Windows.
- What it would add to Loom B and A over ffmpeg: real motion on each change (the headline sliding to the middle instead of fading, the button's words morphing, the picture crossfading in place), lower thirds and a title in Monarc's type, and the edits written as HTML the clone can read back and change. Also a hosted MCP for rendering in the cloud if a laptop render ever gets slow.
- Sources: https://github.com/hyperframes/hyperframes, https://hyperframes.heygen.com/introduction, https://hyperframes.heygen.com/quickstart, https://hyperframes.heygen.com/llms.txt (the full index), https://themenonlab.blog/blog/heygen-hyperframes-video-as-code.

## The others

| Tool | What it is | Fit for Loom B and A |
|---|---|---|
| Remotion | React components rendered to video; the most used code-to-video tool; source-available license (free for one person, paid for companies over a size) | Same job as HyperFrames with React instead of plain HTML; also needs Node. HyperFrames' docs carry a Remotion-to-HyperFrames port guide. No reason to pick it over HyperFrames here |
| Revideo / Motion Canvas | TypeScript animation on a canvas; Revideo adds headless rendering; folded into Midrender (a commercial editor) in 2026 | Explainer animation, not footage with a voice over it. Pass |
| Diffusion Studio | Open-source agent-first editor, JSX compositions, Mac-centered | Mac first. Pass for now |
| ButterCut (`npx vibeindex add barefootford/buttercut`) | A Claude Code skill that reads footage and a transcript and writes a timeline for Final Cut, Premiere, or Resolve; it does not render | He does not cut in those; Monarc Studio is his editor. Pass |
| "video-editing" skill (affaan-m/everything-claude-code) | A Claude Code skill: transcribe, plan cuts, run ffmpeg, polish in Descript or CapCut | The same method `scripts/social_content.py` already runs (Parakeet, a plan, ffmpeg). Nothing to add |
| Creatomate, Shotstack | Hosted JSON-template render APIs, paid | A spend for what ffmpeg does free. Pass |
| Loom's own API | Loom's GraphQL answers with the MP4 and the transcript with segment times; third-party scrapers (Apify) wrap it | `social_content.py fetch` already pulls the MP4 and makes its own word-timed transcript with Parakeet, which is finer than Loom's segments. Nothing to add |

Sources: https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026, https://voyager.so/blog/hyperframes-alternatives, https://vibeindex.ai/skills/barefootford/buttercut/cut, https://www.claudepluginhub.com/skills/affaan-m-everything-claude-code/video-editing, https://apify.com/automation-lab/loom-scraper.

## The decision this page waits on

Node on this laptop, so HyperFrames can be tried on one Loom B and A piece against the ffmpeg cut. Free; about five minutes; his go.
