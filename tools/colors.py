#!/usr/bin/env python3
"""Colour tooling for the Design System Foundation. No dependencies.

  python3 tools/colors.py build      write colors.json from tokens.css (W3C DTCG format)
  python3 tools/colors.py check      compare colors.json with tokens.css; exit 1 on any mismatch
  python3 tools/colors.py contrast   print WCAG ratios for the approved pairs, light and dark
  python3 tools/colors.py html       rewrite the contrast table in pages/colour-guardrails.html

Run from the design-system-foundation folder.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(HERE, 'tokens.css')
JSON_OUT = os.path.join(HERE, 'colors.json')
INDEX = os.path.join(HERE, 'pages', 'colour-guardrails.html')  # holds the contrast table
def whole(pattern, text, flags=0):
    """Match the whole string."""
    return re.match('(?:%s)\\Z' % pattern, text, flags)


DECL = re.compile(r'(--[a-z0-9-]+)\s*:\s*([^;]+);')


# ── Parsing ──────────────────────────────────────────────────────────────
def blocks(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    def body(start):
        depth, i = 0, css.index('{', start)
        for j in range(i, len(css)):
            if css[j] == '{': depth += 1
            elif css[j] == '}':
                depth -= 1
                if depth == 0: return css[i + 1:j]
    root = body(css.index(':root {'))
    media = body(css.index('@media (prefers-color-scheme: dark)'))
    forced = body(css.index(':root[data-theme="dark"]'))
    for b in (root, media, forced):
        assert b is not None
    # the media block wraps a selector; take its inner body
    media = media[media.index('{') + 1:media.rindex('}')]
    hc = [m.start() for m in re.finditer(r'prefers-contrast|data-contrast', css)]
    return dict(DECL.findall(root)), dict(DECL.findall(media)), dict(DECL.findall(forced)), bool(hc)


def themes():
    light, media, forced, has_contrast = blocks(open(TOKENS).read())
    assert media == forced, 'dark blocks differ: ' + str(set(media.items()) ^ set(forced.items()))
    dark = dict(light); dark.update(forced)
    return light, dark, set(forced), has_contrast


def resolve(name, theme, seen=()):
    v = theme[name].strip()
    m = whole(r'var\((--[a-z0-9-]+)\)', v)
    if m:
        assert m.group(1) not in seen
        return resolve(m.group(1), theme, seen + (name,))
    return v


def ref_of(name, theme):
    m = whole(r'var\((--[a-z0-9-]+)\)', theme[name].strip())
    return m.group(1) if m else None


def parse_color(v):
    """Return (r, g, b, a) 0-255/0-1 or None."""
    v = v.strip()
    if v in ('#fff', '#FFF'): v = '#FFFFFF'
    m = whole(r'#([0-9a-fA-F]{6})', v)
    if m:
        h = m.group(1); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = whole(r'#([0-9a-fA-F]{3})', v)
    if m:
        h = m.group(1); return tuple(int(c * 2, 16) for c in h) + (1.0,)
    m = whole(r'rgba?\(([^)]*)\)', v)
    if m:
        p = [x.strip() for x in m.group(1).split(',')]
        return (int(p[0]), int(p[1]), int(p[2]), float(p[3]) if len(p) > 3 else 1.0)
    return None


def to_hex(c):
    h = '#%02X%02X%02X' % c[:3]
    return h if c[3] >= 1 else h + '%02X' % round(c[3] * 255)


def color_tokens(theme):
    out = {}
    for n in theme:
        c = parse_color(resolve(n, theme))
        if c: out[n] = c
    return out


# ── Grouping and descriptions ────────────────────────────────────────────
PRIMITIVE_FAMILIES = ['green', 'mint', 'neutral', 'charcoal', 'coral', 'teal', 'sky', 'amber', 'violet', 'navy']
SEMANTIC_DESC = {
    '--color-bg-app': 'Page background (the board)', '--color-bg-canvas': 'Main canvas panel',
    '--color-surface': 'Cards, header, panels', '--color-surface-raised': 'Menus, dialogs, popovers',
    '--color-surface-sunken': 'Rows and groups inside a card', '--color-surface-muted': 'Filled controls, segmented track',
    '--color-surface-hover': 'Row and item hover', '--color-surface-selected': 'Selected card or option',
    '--color-surface-inverse': 'Toasts, tooltips', '--color-surface-strong': 'Charcoal feature card',
    '--color-overlay': 'Scrim behind dialogs', '--color-glass': 'Frosted dock fill', '--color-glass-border': 'Frosted dock edge',
    '--color-text': 'Primary text', '--color-text-secondary': 'Secondary text, labels', '--color-text-muted': 'Meta, captions (AA)',
    '--color-text-placeholder': 'Input placeholders', '--color-text-disabled': 'Disabled text (exempt from AA)',
    '--color-text-inverse': 'Text on inverse surfaces', '--color-text-on-accent': 'Text on the accent fill',
    '--color-text-on-strong': 'Text on charcoal and deep green fills', '--color-text-link': 'Links',
    '--color-border': 'Hairlines, card outlines', '--color-border-subtle': 'Dividers inside cards',
    '--color-border-strong': 'Outline buttons, choice cards', '--color-border-input': 'Field borders (3:1)',
    '--color-accent': 'Primary action, selected', '--color-accent-hover': 'Primary hover', '--color-accent-pressed': 'Primary pressed',
    '--color-accent-soft': 'Secondary button, active nav', '--color-accent-soft-hover': 'Secondary hover',
    '--color-accent-text': 'Accent-coloured text', '--color-accent-bright': 'Lime: bars, tags, highlights; never text on white',
    '--color-focus': 'Focus ring', '--color-focus-glow': 'Focus glow around fields', '--color-disabled-bg': 'Disabled control fill',
}
STATUS_PART = {'bg': 'fill', 'text': 'text', 'solid': 'solid fill', 'on-solid': 'text on the solid fill', 'border': 'border', 'hover': 'solid hover'}


def describe(n):
    if n in SEMANTIC_DESC: return SEMANTIC_DESC[n]
    m = whole(r'--color-(success|warning|danger|info|neutral)-(.+)', n)
    if m: return '%s %s' % (m.group(1).capitalize(), STATUS_PART.get(m.group(2), m.group(2)))
    m = whole(r'--color-signal-(.+)', n)
    if m: return '%s signal: dots, bars, icons (non-text, 3:1)' % m.group(1).capitalize()
    m = whole(r'--hue-([a-z]+)(-soft|-ink)?', n)
    if m:
        part = {None: 'base: icon colour, chart series', '-soft': 'soft fill', '-ink': 'text on the soft fill'}[m.group(2)]
        return 'Accent hue %s, %s' % (m.group(1), part)
    m = whole(r'--([a-z]+)-(\d+)', n)
    if m: return 'Primitive %s %s. Build semantic tokens from it; not for components.' % (m.group(1), m.group(2))
    return n


def semantic_group(n):
    if re.match(r'--color-(bg|surface|overlay|glass)', n): return 'surface'
    if n.startswith('--color-text'): return 'text'
    if n.startswith('--color-border'): return 'border'
    if n.startswith('--color-accent'): return 'accent'
    if re.match(r'--color-(success|warning|danger|info|neutral)-', n): return 'status'
    if n.startswith('--color-signal'): return 'signal'
    if re.match(r'--color-(focus|disabled)', n): return 'state'
    if n.startswith('--hue-'): return 'hue'
    return 'other'


def token(n, c, theme):
    t = {'$type': 'color', '$value': to_hex(c), '$description': describe(n),
         '$extensions': {'com.antz.css': {'var': n}}}
    r = ref_of(n, theme)
    if r: t['$extensions']['com.antz.css']['ref'] = r
    return t


def build():
    light, dark, dark_names, has_contrast = themes()
    lc, dc = color_tokens(light), color_tokens(dark)
    prim = {k: v for k, v in lc.items() if not k.startswith(('--color-', '--hue-'))}
    doc = {'$description': 'Colour tokens of the ANTZ Design System Foundation, generated from tokens.css by tools/colors.py. '
                           'Names match the CSS custom properties without the leading dashes. Light is the default theme; '
                           'dark applies with prefers-color-scheme: dark or data-theme="dark". There are no high- or medium-contrast themes yet.',
           'primitive': {}, 'light': {}, 'dark': {}}
    for fam in PRIMITIVE_FAMILIES:
        g = {k[2:]: token(k, v, light) for k, v in prim.items() if whole(r'--%s-\d+' % fam, k)}
        if g: doc['primitive'][fam] = dict({'$description': 'Primitive %s ramp' % fam}, **g)
    leftover = [k for k in prim if not any(whole(r'--%s-\d+' % f, k) for f in PRIMITIVE_FAMILIES)]
    assert not leftover, leftover
    for name, cmap, theme in (('light', lc, light), ('dark', dc, dark)):
        for k, v in cmap.items():
            if k in prim: continue
            grp = semantic_group(k)
            doc[name].setdefault(grp, {})[k[2:]] = token(k, v, theme)
    with open(JSON_OUT, 'w') as f:
        json.dump(doc, f, indent=2); f.write('\n')
    n = sum(1 for _ in walk(doc))
    print('wrote colors.json: %d tokens (%d primitives, light and dark semantic sets)' % (n, len(prim)))


def walk(node, path=()):
    for k, v in node.items():
        if k.startswith('$'): continue
        if isinstance(v, dict) and '$value' in v: yield path + (k,), v
        elif isinstance(v, dict): yield from walk(v, path + (k,))


def check():
    light, dark, _, _ = themes()
    lc, dc = color_tokens(light), color_tokens(dark)
    prim = {k for k in lc if not k.startswith(('--color-', '--hue-'))}
    doc = json.load(open(JSON_OUT))
    seen = {'primitive': {}, 'light': {}, 'dark': {}}
    errors = []
    for path, t in walk(doc):
        css = t.get('$extensions', {}).get('com.antz.css', {}).get('var')
        if t.get('$type') != 'color': errors.append('%s: $type is not color' % '.'.join(path))
        if not t.get('$description'): errors.append('%s: no $description' % '.'.join(path))
        if css != '--' + path[-1]: errors.append('%s: name does not match %s' % ('.'.join(path), css))
        seen[path[0]][css] = t['$value']
    for scope, cmap, names in (('primitive', lc, prim), ('light', lc, set(lc) - prim), ('dark', dc, set(dc) - prim)):
        for n in sorted(names):
            if n not in seen[scope]: errors.append('%s: %s missing from JSON' % (scope, n)); continue
            want = to_hex(cmap[n])
            if seen[scope][n].upper() != want.upper(): errors.append('%s: %s is %s in JSON, %s in CSS' % (scope, n, seen[scope][n], want))
        for n in seen[scope]:
            if n not in names: errors.append('%s: %s in JSON but not in CSS' % (scope, n))
    total = sum(len(v) for v in seen.values())
    if errors:
        print('FAIL: %d problems' % len(errors)); print('\n'.join(errors)); sys.exit(1)
    print('OK: %d tokens in colors.json match tokens.css (%d primitive, %d light, %d dark); both dark blocks agree.'
          % (total, len(seen['primitive']), len(seen['light']), len(seen['dark'])))


# ── Contrast ─────────────────────────────────────────────────────────────
def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def colors_of(token_name, theme):
    """A token's colour, or every stop of a gradient token (worst case is used)."""
    v = resolve(token_name, theme)
    c = parse_color(v)
    if c: return [c]
    return [parse_color(h) for h in re.findall(r'#[0-9A-Fa-f]{6}', v)]


HUES = ['green', 'teal', 'sky', 'coral', 'amber', 'violet', 'navy']
# (fg, bg, kind, use). kind: text = 4.5 normal / 3 large; ui = 3; exempt = disabled text
PAIRS = [
    ('--color-text', '--color-surface', 'text', 'Body text on cards'),
    ('--color-text', '--color-bg-app', 'text', 'Text on the board'),
    ('--color-text', '--color-surface-muted', 'text', 'Text in filled controls'),
    ('--color-text-secondary', '--color-surface', 'text', 'Labels'),
    ('--color-text-secondary', '--color-surface-sunken', 'text', 'Labels in rows'),
    ('--color-text-muted', '--color-surface', 'text', 'Meta and captions'),
    ('--color-text-muted', '--color-surface-sunken', 'text', 'Meta in rows'),
    ('--color-text-muted', '--color-surface-muted', 'text', 'Meta in filled controls'),
    ('--color-text-muted', '--color-bg-canvas', 'text', 'Meta on the canvas'),
    ('--color-text-muted', '--color-bg-app', 'text', 'Meta on the board'),
    ('--color-text-placeholder', '--color-surface', 'text', 'Placeholders'),
    ('--color-text-link', '--color-surface', 'text', 'Links'),
    ('--color-accent-text', '--color-surface', 'text', 'Accent text, selected labels'),
    ('--color-accent-text', '--color-accent-soft', 'text', 'Secondary button, active nav'),
    ('--color-text-on-accent', '--color-accent', 'text', 'Primary button'),
    ('--color-text-on-accent', '--color-accent-hover', 'text', 'Primary button, hover'),
    ('--color-success-text', '--color-success-bg', 'text', 'Success chip and alert'),
    ('--color-warning-text', '--color-warning-bg', 'text', 'Warning chip and alert'),
    ('--color-danger-text', '--color-danger-bg', 'text', 'Danger chip and alert'),
    ('--color-info-text', '--color-info-bg', 'text', 'Info chip and alert'),
    ('--color-neutral-text', '--color-neutral-bg', 'text', 'Neutral status chip'),
    ('--color-success-text', '--color-surface', 'text', 'Success hint text'),
    ('--color-warning-text', '--color-surface', 'text', 'Warning hint text'),
    ('--color-danger-text', '--color-surface', 'text', 'Error text'),
    ('--color-info-text', '--color-surface', 'text', 'Info text'),
    ('--color-success-on-solid', '--color-success-solid', 'text', 'Solid success'),
    ('--color-warning-on-solid', '--color-warning-solid', 'text', 'Warning button, high priority'),
    ('--color-danger-on-solid', '--color-danger-solid', 'text', 'Danger button, emergency'),
    ('--color-info-on-solid', '--color-info-solid', 'text', 'Info button, normal priority'),
    ('--color-text-inverse', '--color-surface-inverse', 'text', 'Toasts, tooltips'),
    ('--color-text-on-strong', '--color-surface-strong', 'text', 'Charcoal card'),
    ('--color-text-on-strong', '--gradient-deep', 'text', 'Text on the deep green fill (every stop)'),
    ('--color-accent-bright', '--gradient-deep', 'text', 'Lime figures on the deep green fill (every stop)'),
    ('--color-text-on-strong', '--gradient-green', 'text', 'Not approved for small text: move it to --gradient-deep'),
] + [('--hue-%s-ink' % h, '--hue-%s-soft' % h, 'text', 'Tinted chip, tag or avatar') for h in HUES] \
  + [('--hue-%s-ink' % h, '--color-surface', 'text', 'Hue text on a card') for h in HUES] \
  + [('--hue-%s' % h, '--color-surface', 'ui', 'Chart series, icon in a tile') for h in HUES] + [
    ('--color-border-input', '--color-surface', 'ui', 'Field border'),
    ('--color-focus', '--color-surface', 'ui', 'Focus ring on cards'),
    ('--color-focus', '--color-bg-canvas', 'ui', 'Focus ring on the canvas'),
    ('--color-accent', '--color-surface', 'ui', 'Selected control, switch on'),
    ('--color-signal-success', '--color-surface', 'ui', 'Success dot, bar or rail'),
    ('--color-signal-warning', '--color-surface', 'ui', 'Warning dot, bar or rail'),
    ('--color-signal-danger', '--color-surface', 'ui', 'Danger dot, bar or rail'),
    ('--color-signal-info', '--color-surface', 'ui', 'Info dot, bar or rail'),
    ('--color-text-disabled', '--color-surface', 'exempt', 'Disabled text (exempt from WCAG)'),
]


def evaluate():
    light, dark, _, _ = themes()
    rows = []
    for fg, bg, kind, use in PAIRS:
        res = []
        for theme in (light, dark):
            fgs, bgs = colors_of(fg, theme), colors_of(bg, theme)
            r = min(ratio(a, b) for a in fgs for b in bgs)
            res.append(r)
        rows.append((fg, bg, kind, use, res))
    return rows


def verdict(r, kind):
    if kind == 'ui': return {'UI 3:1': r >= 3}
    if kind == 'exempt': return {}
    return {'AA': r >= 4.5, 'AA large': r >= 3, 'UI 3:1': r >= 3}


def contrast():
    fails = 0
    for fg, bg, kind, use, (lr, dr) in evaluate():
        lv, dv = verdict(lr, kind), verdict(dr, kind)
        need = 'AA' if kind == 'text' else 'UI 3:1'
        bad = [t for t, v in (('light', lv), ('dark', dv)) if v and not v[need]]
        if bad: fails += 1
        print('%-28s on %-26s %-6s light %5.2f  dark %5.2f  %s' % (fg, bg, kind, lr, dr, ('FAIL ' + '+'.join(bad)) if bad else ''))
    print('pairs: %d, failing their target: %d' % (len(PAIRS), fails))


def html():
    def chips(r, kind):
        if kind == 'exempt': return '<span class="t-caption">Exempt</span>'
        return ' '.join('<span class="%s">%s</span>' % ('pass' if ok else 'fail', t) for t, ok in verdict(r, kind).items())
    out = []
    for fg, bg, kind, use, (lr, dr) in evaluate():
        bgcss = 'var(%s)' % bg
        if kind == 'ui':
            sample = '<span class="aa-sample" style="background:%s;box-shadow:inset 0 0 0 3px var(%s);color:var(--color-text)">UI</span>' % (bgcss, fg)
        else:
            sample = '<span class="aa-sample" style="background:%s;color:var(%s)">Aa</span>' % (bgcss, fg)
        out.append('<tr><td>%s</td><td><code>%s</code> on <code>%s</code><br><span class="t-caption">%s</span></td>'
                   '<td class="num"><b>%.2f</b></td><td>%s</td><td class="num"><b>%.2f</b></td><td>%s</td></tr>'
                   % (sample, fg, bg, use, lr, chips(lr, kind), dr, chips(dr, kind)))
    s = open(INDEX).read()
    a, b = '<!-- contrast-pairs:start -->', '<!-- contrast-pairs:end -->'
    i, j = s.index(a) + len(a), s.index(b)
    s = s[:i] + '\n' + '\n'.join(out) + '\n' + s[j:]
    open(INDEX, 'w').write(s)
    print('wrote %d rows into %s' % (len(out), os.path.relpath(INDEX, HERE)))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    {'build': build, 'check': check, 'contrast': contrast, 'html': html}[cmd]()
