#!/usr/bin/env python3
"""Génère les pages statiques multilingues pour chaque application.

Usage : python3 build.py

Entrées :
  apps.json          liste des applications (id, name, repo)
  i18n/<locale>.json chaînes traduites, mêmes clés que i18n/en-US.json
  templates/*.html   gabarits

Sorties (commitées, servies par GitHub Pages) :
  index.html                        liste des applications
  <app>/index.html                  choix de langue (+ redirection automatique)
  <app>/assistant.html              redirection vers la langue du navigateur
  <app>/privacy.html                redirection vers la langue du navigateur
  <app>/<locale>/index.html
  <app>/<locale>/assistant.html
  <app>/<locale>/privacy.html
"""
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(ROOT, "i18n")
TPL = os.path.join(ROOT, "templates")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def load_locales():
    ref = flatten(json.load(open(os.path.join(I18N, "en-US.json"), encoding="utf-8")))
    locales = {}
    errors = []
    for name in sorted(os.listdir(I18N)):
        if not name.endswith(".json"):
            continue
        code = name[:-5]
        data = flatten(json.load(open(os.path.join(I18N, name), encoding="utf-8")))
        missing = set(ref) - set(data)
        extra = set(data) - set(ref)
        if missing or extra:
            errors.append(f"{code}: clés manquantes {sorted(missing)} / en trop {sorted(extra)}")
        for k, v in ref.items():
            for ph in re.findall(r"\{[a-z_]+\}", v):
                if k in data and ph not in data[k]:
                    errors.append(f"{code}: {k} ne contient pas {ph}")
        locales[code] = data
    if errors:
        print("Erreurs de traduction :", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    return locales


def render(template, values):
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise KeyError(f"clé de gabarit inconnue : {key}")
        return values[key]
    return re.sub(r"\{\{([a-zA-Z0-9_.]+)\}\}", sub, template)


def localize(strings, app, locale, cfg):
    """Échappe les chaînes et remplit les placeholders {app}, {date}, liens."""
    esc_app = html.escape(app["name"])
    issues_url = app["repo"].rstrip("/") + "/issues"
    issues_link = f'<a href="{issues_url}">{html.escape(strings["common.github_issues"])}</a>'
    privacy_link = f'<a href="privacy.html">{html.escape(strings["assistant.cannot_2_link"])}</a>'
    out = {}
    for k, v in strings.items():
        v = html.escape(v, quote=False).replace('"', "&quot;")
        v = v.replace("{app}", esc_app).replace("{date}", cfg["updated"])
        v = v.replace("{issues_link}", issues_link).replace("{privacy_link}", privacy_link)
        out[k] = v
    out["app"] = esc_app
    out["repo"] = app["repo"]
    out["repo_text"] = app["repo"].replace("https://", "")
    out["issues"] = issues_url
    out["issues_text"] = issues_url.replace("https://", "")
    out["root"] = "../../"
    return out


def alternates(cfg, app, page, locales):
    base = f'{cfg["base_url"]}/{app["id"]}'
    lines = [f'  <link rel="alternate" hreflang="{c}" href="{base}/{c}/{page}">' for c in locales]
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{base}/{cfg["default_locale"]}/{page}">')
    return "\n".join(lines)


def language_list(locales, page, current):
    items = []
    for code, s in locales.items():
        label = html.escape(s["name"])
        if code == current:
            items.append(f'      <li><strong>{label}</strong></li>')
        else:
            items.append(f'      <li><a href="../{code}/{page}" hreflang="{code}" lang="{code}">{label}</a></li>')
    return "\n".join(items)


REDIRECT = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} – {app}</title>
  <link rel="stylesheet" href="{root}assets/style.css">
{alternates}
  <script>
  (function () {{
    var available = {available};
    var fallback = "{fallback}";
    var langs = (navigator.languages || [navigator.language || ""]).map(String);
    var target = null;
    for (var i = 0; i < langs.length && !target; i++) {{
      var l = langs[i];
      if (available.indexOf(l) >= 0) {{ target = l; break; }}
      var base = l.split("-")[0];
      if (/^zh/i.test(l)) {{
        var zh = /hant|tw|hk|mo/i.test(l) ? "zh-Hant" : "zh-Hans";
        if (available.indexOf(zh) >= 0) {{ target = zh; break; }}
      }}
      for (var j = 0; j < available.length; j++) {{
        if (available[j].split("-")[0].toLowerCase() === base.toLowerCase()) {{ target = available[j]; break; }}
      }}
    }}
    location.replace((target || fallback) + "/{page}");
  }})();
  </script>
</head>
<body>
  <header><h1>{app}</h1></header>
  <main>
    <h2>{title}</h2>
    <ul class="languages">
{links}
    </ul>
  </main>
  <footer>{app} · <a href="{repo}">{source}</a></footer>
</body>
</html>
"""


def build_redirect(cfg, app, page, locales, title):
    links = "\n".join(
        f'      <li><a href="{c}/{page}" hreflang="{c}" lang="{c}">{html.escape(s["name"])}</a></li>'
        for c, s in locales.items()
    )
    return REDIRECT.format(
        title=html.escape(title),
        app=html.escape(app["name"]),
        root="../",
        alternates=alternates(cfg, app, page, locales),
        available=json.dumps(list(locales)),
        fallback=cfg["default_locale"],
        page=page,
        links=links,
        repo=app["repo"],
        source=html.escape(locales[cfg["default_locale"]]["common.source"]),
    )


ROOT_INDEX = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Assistant &amp; Privacy</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header><h1>Assistant &amp; Privacy</h1></header>
  <main>
{cards}
  </main>
  <footer><a href="https://github.com/regemathieu-hue/atelier-fichier">Source code on GitHub</a></footer>
</body>
</html>
"""


def main():
    cfg = json.load(open(os.path.join(ROOT, "apps.json"), encoding="utf-8"))
    locales = load_locales()
    page_tpl = read(os.path.join(TPL, "page.html"))
    bodies = {
        "index.html": read(os.path.join(TPL, "index.body.html")),
        "assistant.html": read(os.path.join(TPL, "assistant.body.html")),
        "privacy.html": read(os.path.join(TPL, "privacy.body.html")),
    }
    count = 0
    cards = []
    for app in cfg["apps"]:
        app_dir = os.path.join(ROOT, app["id"])
        if os.path.isdir(app_dir):
            shutil.rmtree(app_dir)
        for code, strings in locales.items():
            values = localize(strings, app, code, cfg)
            for page, body_tpl in bodies.items():
                values["language_list"] = language_list(locales, page, code)
                values["alternates"] = alternates(cfg, app, page, locales)
                if page == "assistant.html":
                    values["title"] = values["assistant.title"]
                    values["description"] = values["assistant.what_p"]
                elif page == "privacy.html":
                    values["title"] = values["privacy.title"]
                    values["description"] = values["privacy.intro"]
                else:
                    values["title"] = values["index.title"]
                    values["description"] = values["index.intro"]
                values["page_title"] = values["title"] if values["app"] in values["title"] else f'{values["title"]} – {values["app"]}'
                values["body"] = render(body_tpl, values)
                write(os.path.join(app_dir, code, page), render(page_tpl, values))
                count += 1
        default = locales[cfg["default_locale"]]
        write(os.path.join(app_dir, "index.html"),
              build_redirect(cfg, app, "index.html", locales, default["index.choose_language"]))
        write(os.path.join(app_dir, "assistant.html"),
              build_redirect(cfg, app, "assistant.html", locales, default["nav.assistant"]))
        write(os.path.join(app_dir, "privacy.html"),
              build_redirect(cfg, app, "privacy.html", locales, default["nav.privacy"]))
        count += 3
        name = html.escape(app["name"])
        cards.append(
            f'    <div class="card"><p><strong>{name}</strong><br>\n'
            f'      <a href="{app["id"]}/assistant.html">Assistant</a> · '
            f'<a href="{app["id"]}/privacy.html">Privacy Policy</a> · '
            f'<a href="{app["id"]}/index.html">Languages</a></p></div>'
        )
    write(os.path.join(ROOT, "index.html"), ROOT_INDEX.format(cards="\n".join(cards)))
    print(f"{count} pages générées pour {len(cfg['apps'])} application(s) et {len(locales)} langue(s).")


if __name__ == "__main__":
    main()
