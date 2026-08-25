#!/usr/bin/env python3

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = Path("assets/language-stack.svg")

TOP_LANGUAGES = 5

LANGUAGE_COLORS = {
    "JavaScript": "#d5a83c",
    "TypeScript": "#4d7770",
    "Python": "#8b7352",
    "CSS": "#b9573d",
    "HTML": "#c66a43",
    "Java": "#a85d42",
    "C": "#65715c",
    "C++": "#8c5b49",
    "C#": "#68785b",
    "Go": "#547a75",
    "Rust": "#865b42",
    "PHP": "#756b79",
    "Ruby": "#a95747",
    "Kotlin": "#8c684d",
    "Swift": "#c76b43",
    "Shell": "#56684d",
    "Dart": "#557b76",
    "Vue": "#64805c",
    "Jupyter Notebook": "#9b7650",
}

EXCLUDED_REPOSITORIES = {
    "SoupLittle",
}


# ============================================================
# GITHUB API
# ============================================================

def github_request(url, token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SoupLittle-language-stack",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def get_all_repositories(username, token=None):
    repositories = []
    page = 1

    while True:
        query = urllib.parse.urlencode({
            "per_page": 100,
            "page": page,
            "type": "owner",
            "sort": "updated",
        })

        url = (
            f"https://api.github.com/users/"
            f"{urllib.parse.quote(username)}/repos?{query}"
        )

        print(f"Fetching repositories page {page}...")

        data = github_request(url, token)

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_repository_languages(owner, repo, token=None):
    url = (
        f"https://api.github.com/repos/"
        f"{urllib.parse.quote(owner)}/"
        f"{urllib.parse.quote(repo)}/languages"
    )

    try:
        return github_request(url, token)

    except Exception as error:
        print(
            f"Could not read languages for {repo}: {error}"
        )
        return {}


# ============================================================
# LANGUAGE CALCULATION
# ============================================================

def calculate_languages(username, token=None):
    repositories = get_all_repositories(
        username,
        token,
    )

    totals = {}
    scanned = 0

    for repository in repositories:

        name = repository["name"]

        if repository.get("fork", False):
            print(f"Skipping fork: {name}")
            continue

        if repository.get("archived", False):
            print(f"Skipping archived repository: {name}")
            continue

        if name in EXCLUDED_REPOSITORIES:
            print(f"Skipping excluded repository: {name}")
            continue

        print(f"Scanning: {name}")

        languages = get_repository_languages(
            username,
            name,
            token,
        )

        for language, byte_count in languages.items():

            if not isinstance(byte_count, int):
                continue

            totals[language] = (
                totals.get(language, 0)
                + byte_count
            )

        scanned += 1

    total_bytes = sum(totals.values())

    if total_bytes == 0:
        return [], scanned

    sorted_languages = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    results = []

    for language, byte_count in sorted_languages:

        percentage = (
            byte_count / total_bytes
        ) * 100

        results.append({
            "name": language,
            "bytes": byte_count,
            "percentage": percentage,
        })

    return results, scanned


# ============================================================
# SVG HELPERS
# ============================================================

def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def language_color(language, index):
    if language in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[language]

    fallback_colors = [
        "#d5a83c",
        "#4d7770",
        "#8b7352",
        "#b9573d",
        "#c66a43",
        "#65715c",
        "#865b42",
    ]

    return fallback_colors[
        index % len(fallback_colors)
    ]


def format_percentage(value):
    if value > 0 and value < 0.1:
        return "<0.1%"

    return f"{value:.1f}%"


# ============================================================
# LANGUAGE ROWS
# ============================================================

def generate_language_rows(languages):

    rows = []

    top_languages = languages[:TOP_LANGUAGES]

    if not top_languages:
        return ""

    # IMPORTANT:
    #
    # The bar represents the REAL percentage.
    #
    # 74% -> 74% of the available bar width
    # 20% -> 20% of the available bar width
    # 5%  -> 5% of the available bar width
    #
    # We DO NOT normalize against the largest language.

    bar_max_width = 857

    # More vertical room than before.
    row_start_y = 330
    row_spacing = 62

    for index, language in enumerate(top_languages):

        name = escape_xml(
            language["name"]
        )

        percentage = language["percentage"]

        color = language_color(
            language["name"],
            index,
        )

        # REAL percentage-based width.
        bar_width = (
            percentage / 100
        ) * bar_max_width

        # Make tiny percentages visible.
        if percentage > 0:
            bar_width = max(
                bar_width,
                8,
            )

        y = (
            row_start_y
            + (index * row_spacing)
        )

        rows.append(f"""
      <!-- {name} -->

      <circle
        cx="66"
        cy="{y + 10}"
        r="7"
        fill="{color}"
      />

      <text
        x="86"
        y="{y + 15}"
        font-family="Arial, sans-serif"
        font-size="15"
        font-weight="bold"
        letter-spacing="1"
        fill="#24382b"
      >{name.upper()}</text>

      <text
        x="943"
        y="{y + 15}"
        text-anchor="end"
        font-family="Courier New, monospace"
        font-size="14"
        font-weight="bold"
        fill="#24382b"
      >{format_percentage(percentage)}</text>

      <!-- Background bar -->
      <rect
        x="86"
        y="{y + 27}"
        width="{bar_max_width}"
        height="13"
        rx="6.5"
        fill="#dfcfaa"
      />

      <!-- Actual percentage bar -->
      <rect
        x="86"
        y="{y + 27}"
        width="{bar_width:.1f}"
        height="13"
        rx="6.5"
        fill="{color}"
      />
""")

    return "\n".join(rows)


# ============================================================
# SVG
# ============================================================

def generate_svg(languages, repository_count):

    rows = generate_language_rows(
        languages
    )

    if not rows:
        rows = """
      <text
        x="86"
        y="350"
        font-family="Georgia, serif"
        font-size="24"
        font-weight="bold"
        fill="#24382b"
      >
        Nothing growing yet...
      </text>
"""

    return f"""<svg
  width="1000"
  height="760"
  viewBox="0 0 1000 760"
  xmlns="http://www.w3.org/2000/svg"
>

  <defs>

    <!-- Vintage paper grain -->
    <pattern
      id="paper"
      width="80"
      height="80"
      patternUnits="userSpaceOnUse"
    >
      <circle
        cx="8"
        cy="12"
        r="1.2"
        fill="#6f5138"
        opacity=".10"
      />

      <circle
        cx="42"
        cy="25"
        r="1"
        fill="#6f5138"
        opacity=".08"
      />

      <circle
        cx="67"
        cy="61"
        r="1.3"
        fill="#6f5138"
        opacity=".09"
      />

      <circle
        cx="22"
        cy="70"
        r=".8"
        fill="#6f5138"
        opacity=".08"
      />

      <path
        d="M4 43l2 1M55 8l2-1M72 36l1 2"
        stroke="#6f5138"
        opacity=".07"
      />
    </pattern>

    <!-- Footer texture -->
    <pattern
      id="dots"
      width="18"
      height="18"
      patternUnits="userSpaceOnUse"
    >
      <circle
        cx="2"
        cy="2"
        r="1.1"
        fill="#f6e9ca"
        opacity=".22"
      />
    </pattern>

    <clipPath id="round">
      <rect
        x="18"
        y="18"
        width="964"
        height="724"
        rx="18"
      />
    </clipPath>

  </defs>


  <!-- Outer dark green -->
  <rect
    width="1000"
    height="760"
    fill="#24382b"
  />


  <g clip-path="url(#round)">

    <!-- Paper -->
    <rect
      x="18"
      y="18"
      width="964"
      height="724"
      fill="#f1e2bd"
    />

    <rect
      x="18"
      y="18"
      width="964"
      height="724"
      fill="url(#paper)"
    />


    <!-- Vintage frame -->
    <rect
      x="18"
      y="18"
      width="964"
      height="724"
      fill="none"
      stroke="#c95231"
      stroke-width="7"
      opacity=".8"
    />


    <!-- Sun -->
    <circle
      cx="865"
      cy="112"
      r="76"
      fill="#d9a83c"
      opacity=".18"
    />

    <circle
      cx="865"
      cy="112"
      r="52"
      fill="#d9a83c"
      opacity=".15"
    />

    <g
      stroke="#c95231"
      stroke-width="5"
      opacity=".16"
    >
      <path d="M865 20V55"/>
      <path d="M865 169V204"/>
      <path d="M773 112H808"/>
      <path d="M922 112H957"/>
      <path d="M800 47L825 72"/>
      <path d="M905 152L930 177"/>
      <path d="M930 47L905 72"/>
      <path d="M825 152L800 177"/>
    </g>


    <!-- Header -->
    <text
      x="58"
      y="67"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="17"
      font-weight="bold"
      letter-spacing="3"
      fill="#b64b2d"
    >
      MY DIGITAL GARDEN
    </text>

    <text
      x="58"
      y="91"
      font-family="Arial, sans-serif"
      font-size="11"
      letter-spacing="2"
      fill="#6d5038"
    >
      A SMALL ARCHIVE OF WHAT I BUILD
    </text>

    <text
      x="944"
      y="70"
      text-anchor="end"
      font-family="Courier New, monospace"
      font-size="11"
      letter-spacing="1"
      fill="#6d5038"
    >
      EST. 2023
    </text>


    <!-- Divider -->
    <path
      d="
        M58 111
        C120 106 160 115 220 110
        S330 113 390 109
        S510 113 570 109
        S700 114 760 109
        S850 113 944 109
      "
      fill="none"
      stroke="#b64b2d"
      stroke-width="2"
      opacity=".65"
    />


    <!-- Title -->
    <text
      x="55"
      y="185"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="68"
      font-weight="900"
      letter-spacing="-3"
      fill="#c95030"
      stroke="#7b3f2d"
      stroke-width="1"
    >
      LANGUAGE
    </text>

    <text
      x="55"
      y="250"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="68"
      font-weight="900"
      letter-spacing="-3"
      fill="#c95030"
      stroke="#7b3f2d"
      stroke-width="1"
    >
      STACK
    </text>

    <text
      x="60"
      y="281"
      font-family="Courier New, monospace"
      font-size="13"
      fill="#6d5038"
      letter-spacing="1"
    >
      WHAT'S GROWING IN MY REPOSITORIES
    </text>


    <!-- Flower -->
    <g transform="translate(875 230)">
      <circle
        cx="0"
        cy="-18"
        r="13"
        fill="#d7a53a"
      />

      <circle
        cx="17"
        cy="-6"
        r="13"
        fill="#d7a53a"
      />

      <circle
        cx="11"
        cy="14"
        r="13"
        fill="#d7a53a"
      />

      <circle
        cx="-11"
        cy="14"
        r="13"
        fill="#d7a53a"
      />

      <circle
        cx="-17"
        cy="-6"
        r="13"
        fill="#d7a53a"
      />

      <circle
        cx="0"
        cy="0"
        r="8"
        fill="#c95030"
      />
    </g>


    <!-- ================================================== -->
    <!-- LANGUAGE ROWS -->
    <!-- ================================================== -->

    {rows}


    <!-- ================================================== -->
    <!-- FOOTER -->
    <!-- ================================================== -->

    <path
      d="M18 650H982V742H18Z"
      fill="#c95030"
    />

    <rect
      x="18"
      y="650"
      width="964"
      height="92"
      fill="url(#dots)"
    />

    <text
      x="58"
      y="682"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="23"
      font-weight="bold"
      fill="#f5e7c5"
    >
      MADE WITH CURIOSITY
    </text>

    <text
      x="58"
      y="709"
      font-family="Courier New, monospace"
      font-size="11"
      letter-spacing="1"
      fill="#f5e7c5"
      opacity=".9"
    >
      CULTIVATED ACROSS {repository_count} GITHUB REPOSITORIES
    </text>

    <text
      x="942"
      y="704"
      text-anchor="end"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="29"
      font-weight="bold"
      font-style="italic"
      fill="#f5e7c5"
    >
      ✦
    </text>

  </g>


  <!-- Outer border -->
  <rect
    x="18"
    y="18"
    width="964"
    height="724"
    rx="18"
    fill="none"
    stroke="#f1e2bd"
    stroke-width="3"
    opacity=".8"
  />

</svg>
"""


# ============================================================
# MAIN
# ============================================================

def main():

    username = (
        os.environ.get("GITHUB_USERNAME")
        or os.environ.get("GITHUB_REPOSITORY_OWNER")
    )

    if not username:
        raise RuntimeError(
            "GITHUB_USERNAME or GITHUB_REPOSITORY_OWNER "
            "is required."
        )

    token = os.environ.get("GITHUB_TOKEN")

    print()
    print("============================================")
    print("        RETRO LANGUAGE STACK")
    print("============================================")
    print()

    print(f"GitHub user: {username}")
    print()

    languages, repository_count = calculate_languages(
        username,
        token,
    )

    print()
    print("Languages discovered:")
    print()

    for language in languages:
        print(
            f"{language['name']:25}"
            f"{language['percentage']:7.2f}%"
        )

    print()
    print(
        f"Repositories scanned: "
        f"{repository_count}"
    )
    print()

    svg = generate_svg(
        languages,
        repository_count,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        svg,
        encoding="utf-8",
    )

    print(
        f"Generated: {OUTPUT_FILE}"
    )
    print()


if __name__ == "__main__":
    main()