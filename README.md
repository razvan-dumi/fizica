# Examify

A single-screen exam practice demo. Shows one multiple-choice question at a time;
after you answer, the correct choice is highlighted (and your wrong pick, if any).
Click **Următoarea →** for the next one. Questions are shuffled per session and shown
with no repeats; once you reach the end the deck reshuffles and loops — effectively
infinite practice. Each question keeps its stable index (`#id`), shown in the header.

## Run it

```
node server.js
```

Then open the printed URL:

- On this PC: `http://localhost:8888`
- From a phone/tablet on the **same Wi-Fi**: `http://<this-PC-LAN-IP>:8888`
  (the server prints the exact address, e.g. `http://192.168.x.x:8888`)

The server is zero-dependency (Node built-ins only). On Windows, allow the firewall
prompt for Node on **private** networks so other devices can connect.
Change the port with `PORT=3000 node server.js`.

> Open it via the server, not by double-clicking `index.html` — the app fetches
> `questions.json` over HTTP, which a `file://` page can't do.

## Deploy to GitHub Pages

The app is fully static and uses relative paths, so it runs on GitHub Pages as-is.
A workflow at [.github/workflows/deploy.yml](.github/workflows/deploy.yml) publishes
only the runtime files (`index.html`, `styles.css`, `app.js`, `questions.json`) — not
`mock.docx`, `server.js`, or the extraction script.

One-time setup:

1. Create a repo on GitHub and push this folder:
   ```
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```
2. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Every push to `main` (or `master`) builds and deploys automatically. The live URL
   appears in the Actions run and under Settings → Pages, typically
   `https://<you>.github.io/<repo>/`.

`server.js` is only for local/LAN use; GitHub Pages doesn't run it.

## Files

| File             | Purpose                                                         |
| ---------------- | --------------------------------------------------------------- |
| `index.html`     | The single screen                                               |
| `styles.css`     | Styling (card, choice states, responsive)                       |
| `app.js`         | Quiz logic: load JSON, shuffle, reveal answer, loop             |
| `questions.json` | 245 questions: `{ id, exam, question, choices[], correctIndex }`|
| `server.js`      | Zero-dependency LAN static server                               |

## How the questions were extracted

The source is `mock.docx`. A `.docx` is a zip of XML with real text, so no OCR/vision is
needed — [_extract_docx.py](_extract_docx.py) reads `word/document.xml` directly. The
correct answer in each question is the choice with a **blue shading** (`w:shd` fill
`9EC4E7`); other shading colors are stray noise.

The document holds **three exam sections** with inconsistent formatting (some choices are
numbered lists, some are manual `a)`/`b)` text, some stems are glued to their first
choice), so the parser groups by content: a stem ends in `:`/`?`, and the lines after it
are its choices. Open-ended blocks and image captions are skipped, and Section C's
duplicated questions are deduped. Each question gets a single stable global `id` (1–245)
for display and for the non-repeat/loop logic; the source exam is kept in the `exam` field.

Regenerate `questions.json` from the docx with:

```
python _extract_docx.py
```
