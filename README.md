# Design System Foundation

The foundation layer of the ANTZ design system: tokens, general components and documentation. Vanilla HTML/CSS, with no build step.

## What's here

| File | What it is |
| --- | --- |
| `tokens.css` | Primitives (raw palette, type, space, radii, motion) and semantic tokens, with light and dark themes. |
| `components.css` | Every general component, using tokens only: buttons, fields, selection controls, chips, badges, status, avatars, icon tiles, cards, rows, alerts, toasts, tooltips, menus, dialogs, progress, table, skeleton and empty state, app bar, side nav and dock. Then the components from the Figma file (see below). |
| `index.html` | The documentation site: foundations (with live WCAG contrast checks and colour guardrails), components with variants and states, voice and words. |
| `colors.json` | Every colour token, light and dark, in the W3C design-tokens (DTCG) format. [Download it](colors.json). |
| `tools/colors.py` | Builds `colors.json`, checks it against `tokens.css`, and works out the contrast table in Colour guardrails. No dependencies. |

Run it locally:

```sh
cd "design-system-foundation" && python3 -m http.server 8092 --bind 127.0.0.1
# then open http://localhost:8092/
```

## Using it

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="design-system-foundation/tokens.css">
<link rel="stylesheet" href="design-system-foundation/components.css">
```

- Use only semantic tokens in your own CSS: `--color-surface`, `--color-text-muted`, `--space-4`, `--radius-lg`, `--shadow-sm`, `--duration-base`, `--ease-standard`. Primitives such as `--green-700` exist only to build those.
- Theme: dark follows the OS (`prefers-color-scheme`). Force a theme with `<html data-theme="light">` or `data-theme="dark"`.
- Accent hues are a categorical set for avatars, icon tiles and chart series: `--hue-{green|teal|sky|coral|amber|violet|navy}`, each with `-soft` (fill) and `-ink` (text). Example: `<span class="tile-icon" style="--c: var(--hue-coral)">`.
- Icons are a 24px outline sprite inside `index.html` (`<svg class="icon"><use href="#i-bell"/></svg>`). Copy the `<symbol>`s you need. Lucide matches the drawing style if you need more.
- Breakpoints: mobile under 600px, tablet 600 to 1023px, desktop 1024px and up (`--bp-tablet`, `--bp-desktop`; `--bp-wide` 1280px). CSS variables can't go in media queries, so use the numbers. App layouts use container queries instead: put them in `.shell-host` and the tab bar becomes a side rail, `.split` goes to two columns and `.card-grid` to 2, then 3 to 4 columns as the container grows.
- Motion: cards lift and press, rise into view with a stagger, count their figures up once and crossfade them on period changes; the status rail grows in. Every duration and distance is a token (`--duration-enter`, `--duration-count`, `--stagger`, `--motion-lift`, `--motion-press`, `--motion-rise`), and `prefers-reduced-motion` sets them to zero.
- Colour: `colors.json` mirrors the tokens. After changing a colour token, run `python3 tools/colors.py build`, then `check`, then `html` to refresh the contrast table.

## Sections from the Figma file

Four sections of `index.html` come from the local Figma file `Antz Design System.fig`, from its pages "Foundational Components (atoms)", "Pattern components (molecules)", "Stats cards" and "screens". They were redesigned onto these tokens rather than copied: Figma's nine colour "types" map to the accent, the status colours and the accent hues, and photos are replaced by tinted placeholders.

- **Foundation components:** only what was missing. Button tones (`.btn--tint`, `.btn--line`, `.btn--info`, `.btn--warning`, `.btn--gradient`), icon-button tones, `.fab`, field icons and the floating label (`.input-group`, `.field--float`, `.field__help`), the pill search bar (`.search--pill`), option groups (`.fieldset`), pill and person chips, line and figure tabs (`.segmented--line`, `.segmented--stat`) and the bottom navigation (`.tabbar`). A table at the top of the section maps every Figma component to its class.
- **Pattern components:** mobile top bar and action bar, post card, attachments (drop zone and file tiles), priority picker, lists, date picker, animal card with sex tags, and a ring progress.
- **Stat cards:** stat figures, key insights, the insights summary, the site card and the day, week and month switch.
- **Screens:** six 390px phone frames (Home, Housing, Choose people, Add task, New request, Set a date), built only from the components above.

Status accents sit inside the box, never on its outer edge: a 4px rounded rail beside the text block (`.rail`, applied automatically by `.row--alert`, `.post--important` and `.animal--mortality`; colour via `--rail-color` or `.rail--success|warning|info`). Every section of `index.html` ends with a Do / Don't block (`.dd`), some with a small "wrong" example.

Tones take a `--c` custom property set to an `-ink` token, for example `style="--c: var(--hue-teal-ink)"`, so text on tints passes AA in both themes. 26 icons were added to the sprite in the same outline style.

## Where the values came from

- **Look:** ANTZ Home Style 6 (`antz-home-style-2.vercel.app/style-6`, read 9 Nov 2026). Its CSS is inline in the page. The fonts (Inter 300–700, Google Fonts), the palette (lime #52F990, lime-ink #006D35, deep #00512A, board #DDEFE4 / #EAF5EE, ink #0E1512, coral #FA6140, teal #00ABAB, sky #00AFD6, navy #1F415B, charcoal #26252F), the type sizes, radii, shadows (`--sh`), easing (`cubic-bezier(.2,.7,.2,1)`), gradients and breakpoints were all taken from that CSS.
- **Structure:** modelled on Shopify Polaris (foundations → tokens → components → patterns → content), GitHub Primer (functional colour tokens with light and dark from one set of names), Atlassian (surface and elevation tokens, guidance per component) and GOV.UK (plain words, do/don't, accessible by default). All four are on alexpate/awesome-design-systems.

## Derived (not on Style 6)

- **Dark theme:** all of it.
- **Text colours that pass AA:** muted text #5F6B67, because Style 6's #7A8684 is only 3.8:1. Also coral-700 #C2401F for danger text and buttons, amber-800 #8A5A00 for warning text, sky-800 #006E85 for info text, and teal-700 #007A7A.
- **Input border:** #879590, which reaches 3:1. Style 6 uses a fainter #DCE6E1 border on a filled field.
- **Focus ring:** sky-700 #0089A8. Style 6's ring uses sky-500, which is 2.6:1 on white.
- **Also new:** status colour sets and the accent hues (violet-600 and navy-100 are new).

## Open questions

1. **Side nav:** light (Style 6) or deep green? Both are built.
2. **Blue and teal feature cards:** white text on them fails AA for small text. Keep them for big figures only, or drop them?
3. **Colours from Material 3:** Style 6 says its colours come from MD3_Antz, and there is also an `antzdesignsystem` skill with M3 role tokens. Should these tokens be mapped onto those M3 roles?
4. **Brand colours per organisation:** should the accent tokens be overridable per organisation?
