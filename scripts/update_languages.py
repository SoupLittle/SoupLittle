#!/usr/bin/env python3

"""
=============================================================
 LANGUAGE STACK GENERATOR
=============================================================

This script looks at the languages used across your GitHub
repositories and generates:

    assets/language-stack.svg

The SVG is then displayed in your README.

IMPORTANT:
-------------------------------------------------------------
You normally DO NOT edit language-stack.svg manually.

Instead:

    update_languages.py
            ↓
    language-stack.svg
            ↓
         README.md


The script is intentionally heavily commented so that you can
change the design yourself later without having to understand
the entire program.

=============================================================
"""


# =============================================================
# IMPORTS
# =============================================================

import json
import os
import urllib.parse
import urllib.request

from pathlib import Path


# =============================================================
# EASY SETTINGS
# =============================================================
#
# This is the section I recommend you look at first if you
# want to customize something later.
#
# Most visual changes can be made further down in the file.
# =============================================================


# -------------------------------------------------------------
# Where the generated SVG will be saved.
# -------------------------------------------------------------

OUTPUT_FILE = Path(
    "assets/language-stack.svg"
)


# -------------------------------------------------------------
# How many languages should appear?
#
# You asked for FIVE.
#
# Change this to 4, 6, 7, etc. if you ever want to.
# -------------------------------------------------------------

NUMBER_OF_LANGUAGES = 5


# -------------------------------------------------------------
# GitHub repositories that should NOT be counted.
#
# The profile repository itself is normally excluded because
# otherwise README/configuration files can distort the result.
#
# Add more repository names here if there are repositories
# you don't want included.
# -------------------------------------------------------------

EXCLUDED_REPOSITORIES = {
    "SoupLittle",
}


# -------------------------------------------------------------
# C and C++ are combined into one displayed language.
#
# This is useful for your ESP32 / embedded projects because
# GitHub may otherwise give C and C++ two separate rows.
#
# If you don't want this behavior, remove this later.
# -------------------------------------------------------------

COMBINE_C_AND_CPP = True


# =============================================================
# COLOUR PALETTE
# =============================================================
#
# This is where you can change the overall look.
#
# The colors are deliberately kept close to the vintage
# cream / terracotta / olive palette from the design.
#
# If you want to experiment, THIS is one of the easiest places
# to start.
# =============================================================


# -------------------------------------------------------------
# Main background colour.
# -------------------------------------------------------------

PAPER = "#f1e2bd"


# -------------------------------------------------------------
# Cream paper colour.
# -------------------------------------------------------------

PAPER = "#f1e2bd"


# -------------------------------------------------------------
# Main terracotta / orange-red.
# -------------------------------------------------------------

TERRACOTTA = "#c95030"


# -------------------------------------------------------------
# Darker red used for outlines and small details.
# -------------------------------------------------------------

DARK_TERRACOTTA = "#8b3f2c"


# -------------------------------------------------------------
# Brown used for text.
# -------------------------------------------------------------

BROWN = "#5d4935"


# -------------------------------------------------------------
# Muted cream used for footer text.
# -------------------------------------------------------------

LIGHT_CREAM = "#f5e7c5"


# -------------------------------------------------------------
# Empty portion of the language bars.
# -------------------------------------------------------------

EMPTY_BAR = "#dfcfaa"


# -------------------------------------------------------------
# Individual language colors.
#
# You can change these independently.
# -------------------------------------------------------------

LANGUAGE_COLORS = {

    "JavaScript": "#d5a83c",

    "Python": "#6f795b",

    "HTML": "#c66a43",

    "CSS": "#b9633d",

    "C / C++": "#5f715c",

    "Shell": "#547a75",

    "TypeScript": "#4d7770",

    "Java": "#9b6549",

    "C#": "#657653",

    "Go": "#527b76",

    "Rust": "#895d45",

    "PHP": "#756b79",

    "Ruby": "#a95747",

    "Swift": "#c76b43",

    "Kotlin": "#80654f",

    "Dart": "#557b76",

    "Jupyter Notebook": "#9b7650",
}


# -------------------------------------------------------------
# If a language isn't listed above, the script will use one
# of these colors automatically.
# -------------------------------------------------------------

FALLBACK_COLORS = [
    "#d5a83c",
    "#6f795b",
    "#c66a43",
    "#b9633d",
    "#5f715c",
    "#547a75",
]


# =============================================================
# GITHUB API
# =============================================================


def github_request(url, token=None):
    """
    Make a GET request to the GitHub API.

    We use GitHub's language API rather than trying to inspect
    every file ourselves.

    GitHub returns something roughly like:

        {
            "JavaScript": 123456,
            "Python": 45678,
            "HTML": 12345
        }

    The numbers represent bytes of code.
    """

    headers = {
        "Accept": (
            "application/vnd.github+json"
        ),

        "User-Agent": (
            "SoupLittle-language-stack"
        ),

        "X-GitHub-Api-Version": (
            "2022-11-28"
        ),
    }


    # ---------------------------------------------------------
    # GitHub Actions gives us a token.
    #
    # Using it gives us much better API limits than making
    # completely unauthenticated requests.
    # ---------------------------------------------------------

    if token:

        headers["Authorization"] = (
            f"Bearer {token}"
        )


    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )


    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:

        return json.loads(
            response.read().decode(
                "utf-8"
            )
        )


# =============================================================
# GET REPOSITORIES
# =============================================================


def get_all_repositories(
    username,
    token=None,
):
    """
    Get all repositories owned by the GitHub user.

    GitHub returns repositories in pages.
    We therefore keep requesting pages until there are no more.
    """

    repositories = []

    page = 1


    while True:

        # -----------------------------------------------------
        # Ask GitHub for up to 100 repositories at a time.
        # -----------------------------------------------------

        query = urllib.parse.urlencode(
            {
                "per_page": 100,
                "page": page,
                "type": "owner",
                "sort": "updated",
            }
        )


        url = (
            "https://api.github.com/users/"
            f"{urllib.parse.quote(username)}"
            f"/repos?{query}"
        )


        print(
            f"Fetching repository page {page}..."
        )


        data = github_request(
            url,
            token,
        )


        # -----------------------------------------------------
        # No repositories means we've reached the end.
        # -----------------------------------------------------

        if not data:
            break


        repositories.extend(data)


        # -----------------------------------------------------
        # If GitHub returned fewer than 100, this was the last
        # page.
        # -----------------------------------------------------

        if len(data) < 100:
            break


        page += 1


    return repositories


# =============================================================
# GET LANGUAGES FOR ONE REPOSITORY
# =============================================================


def get_repository_languages(
    owner,
    repository,
    token=None,
):
    """
    Ask GitHub which languages are used in one repository.

    Example response:

        {
            "JavaScript": 45000,
            "CSS": 12000,
            "HTML": 9000
        }
    """

    url = (
        "https://api.github.com/repos/"
        f"{urllib.parse.quote(owner)}/"
        f"{urllib.parse.quote(repository)}"
        "/languages"
    )


    try:

        return github_request(
            url,
            token,
        )

    except Exception as error:

        # -----------------------------------------------------
        # One broken/inaccessible repository should not stop
        # the entire language card from being generated.
        # -----------------------------------------------------

        print(
            f"Could not read languages for "
            f"{repository}: {error}"
        )

        return {}


# =============================================================
# COLLECT LANGUAGE DATA
# =============================================================


def calculate_language_totals(
    username,
    token=None,
):
    """
    Scan all repositories and add together their language
    byte counts.

    The result is a dictionary like:

        {
            "JavaScript": 123456,
            "Python": 45678,
            "HTML": 12345
        }

    At this stage we are dealing with BYTES, not percentages.
    """


    repositories = get_all_repositories(
        username,
        token,
    )


    totals = {}

    scanned_repositories = 0


    for repository in repositories:

        name = repository["name"]


        # -----------------------------------------------------
        # Don't count forks.
        #
        # Otherwise someone else's project that you forked
        # could affect your language statistics.
        # -----------------------------------------------------

        if repository.get(
            "fork",
            False,
        ):

            print(
                f"Skipping fork: {name}"
            )

            continue


        # -----------------------------------------------------
        # Don't count archived repositories.
        # -----------------------------------------------------

        if repository.get(
            "archived",
            False,
        ):

            print(
                f"Skipping archived: {name}"
            )

            continue


        # -----------------------------------------------------
        # Don't count repositories explicitly excluded above.
        # -----------------------------------------------------

        if name in EXCLUDED_REPOSITORIES:

            print(
                f"Skipping excluded: {name}"
            )

            continue


        print(
            f"Scanning: {name}"
        )


        languages = get_repository_languages(
            username,
            name,
            token,
        )


        # -----------------------------------------------------
        # Add each language's byte count to our running total.
        # -----------------------------------------------------

        for language, byte_count in (
            languages.items()
        ):

            if not isinstance(
                byte_count,
                int,
            ):

                continue


            totals[language] = (
                totals.get(
                    language,
                    0,
                )
                + byte_count
            )


        scanned_repositories += 1


    return (
        totals,
        scanned_repositories,
    )


# =============================================================
# COMBINE C + C++
# =============================================================


def combine_cpp_and_c(
    totals,
):
    """
    Combine C and C++ into:

        C / C++

    This is especially useful for your ESP32 work.

    For example:

        C      10,000 bytes
        C++    20,000 bytes

    becomes:

        C / C++    30,000 bytes

    If you decide you want C and C++ separately later, simply
    change:

        COMBINE_C_AND_CPP = True

    to:

        COMBINE_C_AND_CPP = False
    """


    if not COMBINE_C_AND_CPP:

        return totals


    c_bytes = totals.get(
        "C",
        0,
    )


    cpp_bytes = totals.get(
        "C++",
        0,
    )


    # ---------------------------------------------------------
    # Nothing to combine.
    # ---------------------------------------------------------

    if (
        c_bytes == 0
        and cpp_bytes == 0
    ):

        return totals


    # ---------------------------------------------------------
    # Create the combined language.
    # ---------------------------------------------------------

    totals["C / C++"] = (
        c_bytes
        + cpp_bytes
    )


    # ---------------------------------------------------------
    # Remove the original individual entries so they don't
    # appear as separate languages.
    # ---------------------------------------------------------

    totals.pop(
        "C",
        None,
    )

    totals.pop(
        "C++",
        None,
    )


    return totals


# =============================================================
# CONVERT BYTES → PERCENTAGES
# =============================================================


def calculate_percentages(
    totals,
):
    """
    Convert byte counts into percentages.

    Example:

        JavaScript = 740 bytes
        Python     = 140 bytes
        HTML       = 120 bytes

    Total = 1000 bytes

    becomes:

        JavaScript = 74%
        Python     = 14%
        HTML       = 12%

    IMPORTANT:
    ----------------------------------------------------------
    We calculate percentages against the TOTAL of ALL
    languages.

    We do NOT divide by the largest language.

    That is what caused your original 74% bar to visually
    become a 100% bar.
    """


    total_bytes = sum(
        totals.values()
    )


    if total_bytes <= 0:

        return []


    languages = []


    for language, byte_count in (
        totals.items()
    ):

        percentage = (
            byte_count
            / total_bytes
        ) * 100


        languages.append(
            {
                "name": language,

                "bytes": byte_count,

                "percentage": percentage,
            }
        )


    # ---------------------------------------------------------
    # Sort by REAL percentage.
    #
    # Highest percentage first.
    #
    # This is the important difference from the earlier
    # preferred-language version.
    # ---------------------------------------------------------

    languages.sort(
        key=lambda item: item[
            "percentage"
        ],
        reverse=True,
    )


    return languages


# =============================================================
# SELECT THE SIX DISPLAY LANGUAGES
# =============================================================


def select_display_languages(
    languages,
):
    """
    Pick the six largest languages.

    Because 'languages' has already been sorted from highest
    percentage to lowest, this is very simple.

    This means the card ALWAYS shows:

        #1 largest
        #2
        #3
        #4
        #5
        #6 smallest

    among your meaningful languages.

    No hard-coded ordering is used.
    """


    return languages[
        :NUMBER_OF_LANGUAGES
    ]


# =============================================================
# XML / SVG TEXT SAFETY
# =============================================================


def escape_xml(value):
    """
    Escape characters that have special meaning in XML.

    This prevents a language name containing something unusual
    from breaking the SVG.
    """

    return (
        str(value)
        .replace(
            "&",
            "&amp;",
        )
        .replace(
            "<",
            "&lt;",
        )
        .replace(
            ">",
            "&gt;",
        )
        .replace(
            '"',
            "&quot;",
        )
        .replace(
            "'",
            "&apos;",
        )
    )


# =============================================================
# LANGUAGE COLOUR
# =============================================================


def get_language_colour(
    language,
    index,
):
    """
    Return the colour assigned to a language.

    If you add a language to the SVG that isn't in our colour
    dictionary, a fallback colour is automatically selected.
    """


    if language in LANGUAGE_COLORS:

        return LANGUAGE_COLORS[
            language
        ]


    return FALLBACK_COLORS[
        index
        % len(FALLBACK_COLORS)
    ]


# =============================================================
# PERCENTAGE DISPLAY
# =============================================================


def format_percentage(
    percentage,
):
    """
    Format the number shown on the right side of each row.

    Examples:

        74.2389 → 74.2%
        14.0000 → 14.0%
        0.0432  → <0.1%
    """


    if (
        percentage > 0
        and percentage < 0.1
    ):

        return "<0.1%"


    return (
        f"{percentage:.1f}%"
    )


# =============================================================
# LANGUAGE ROW GENERATOR
# =============================================================


def generate_language_rows(
    languages,
):
    """
    Generate the SVG elements for the six language rows.

    This is one of the BEST places to experiment with the
    appearance of the card.

    Things you can easily change:

        row_start_y
        row_spacing
        bar_max_width
        bar_height
        text sizes
        circle sizes

    ----------------------------------------------------------

    IMPORTANT:

    The bar width is calculated like this:

        percentage / 100 * bar_max_width

    So:

        100% = full bar
         75% = 75% bar
         50% = half bar
         10% = small bar

    This means the visual bar represents the actual percentage.
    """


    if not languages:

        return ""


    rows = []


    # ---------------------------------------------------------
    # Maximum width of the empty language bar.
    #
    # Increase this if you want longer bars.
    # ---------------------------------------------------------

    bar_max_width = 720


    # ---------------------------------------------------------
    # First language row.
    #
    # Increase this number to move the whole language section
    # further down.
    # ---------------------------------------------------------

    row_start_y = 400


    # ---------------------------------------------------------
    # Vertical distance between language rows.
    #
    # Increase this if you want more breathing room.
    # ---------------------------------------------------------

    row_spacing = 64


    # ---------------------------------------------------------
    # Height of each bar.
    # ---------------------------------------------------------

    bar_height = 14


    for index, language in enumerate(
        languages
    ):

        language_name = language[
            "name"
        ]


        percentage = language[
            "percentage"
        ]


        # -----------------------------------------------------
        # Make the language name XML-safe.
        # -----------------------------------------------------

        safe_name = escape_xml(
            language_name
        )


        # -----------------------------------------------------
        # Choose this language's colour.
        # -----------------------------------------------------

        colour = get_language_colour(
            language_name,
            index,
        )


        # -----------------------------------------------------
        # Calculate the actual bar width.
        #
        # THIS MUST use / 100.
        #
        # Do NOT change this to:
        #
        #     percentage / max_percentage
        #
        # because that would turn the largest language into
        # a visually full bar again.
        # -----------------------------------------------------

        bar_width = (
            percentage
            / 100
        ) * bar_max_width


        # -----------------------------------------------------
        # Tiny percentages can otherwise become invisible.
        #
        # Give anything above zero a minimum width.
        # -----------------------------------------------------

        if percentage > 0:

            bar_width = max(
                bar_width,
                8,
            )


        # -----------------------------------------------------
        # Calculate vertical position.
        # -----------------------------------------------------

        y = (
            row_start_y
            + index * row_spacing
        )


        # -----------------------------------------------------
        # Create the SVG for this language.
        # -----------------------------------------------------

        rows.append(
            f"""
    <!-- ================================================ -->
    <!-- LANGUAGE ROW {index + 1}: {safe_name} -->
    <!-- ================================================ -->

    <!-- Small coloured dot -->
    <circle
      cx="70"
      cy="{y + 8}"
      r="7"
      fill="{colour}"
    />

    <!-- Language name -->
    <text
      x="92"
      y="{y + 13}"
      font-family="Arial, sans-serif"
      font-size="16"
      font-weight="bold"
      letter-spacing="1"
      fill="{BROWN}"
    >{safe_name.upper()}</text>

    <!-- Percentage -->
    <text
      x="930"
      y="{y + 13}"
      text-anchor="end"
      font-family="Courier New, monospace"
      font-size="14"
      font-weight="bold"
      fill="{BROWN}"
    >{format_percentage(percentage)}</text>

    <!-- Empty / background part of bar -->
    <rect
      x="92"
      y="{y + 25}"
      width="{bar_max_width}"
      height="{bar_height}"
      rx="7"
      fill="{EMPTY_BAR}"
    />

    <!-- Actual percentage -->
    <rect
      x="92"
      y="{y + 25}"
      width="{bar_width:.1f}"
      height="{bar_height}"
      rx="7"
      fill="{colour}"
    />
"""
        )


    return "\n".join(
        rows
    )


# =============================================================
# SVG GENERATOR
# =============================================================


def generate_svg(
    languages,
    repository_count,
):
    """
    Build the complete SVG image.

    This is basically the HTML/CSS equivalent of the image
    you're designing, except SVG can be displayed directly
    inside your GitHub README.
    """


    language_rows = (
        generate_language_rows(
            languages
        )
    )


    # ---------------------------------------------------------
    # If there are no languages, show a friendly message.
    # ---------------------------------------------------------

    if not language_rows:

        language_rows = """
    <text
      x="92"
      y="420"
      font-family="Georgia, serif"
      font-size="24"
      font-weight="bold"
      fill="#5d4935"
    >
      Nothing growing yet...
    </text>
"""


    # ---------------------------------------------------------
    # IMPORTANT DESIGN SETTINGS
    # ---------------------------------------------------------
    #
    # The SVG is deliberately tall enough for:
    #
    #   Header
    #   About section
    #   Six language rows
    #   Quote
    #   Three feature areas
    #   Footer
    #
    # If you add more sections later, increase HEIGHT.
    # ---------------------------------------------------------

    WIDTH = 1000

    HEIGHT = 940


    # ---------------------------------------------------------
    # Footer position.
    #
    # If you make the language rows taller, move this down.
    # ---------------------------------------------------------

    FOOTER_Y = 855


    return f"""<svg
  width="{WIDTH}"
  height="{HEIGHT}"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  xmlns="http://www.w3.org/2000/svg"
>

  <!-- ===================================================== -->
  <!-- DEFINITIONS                                            -->
  <!-- ===================================================== -->

  <defs>

    <!-- --------------------------------------------------- -->
    <!-- Paper texture                                        -->
    <!-- --------------------------------------------------- -->

    <pattern
      id="paperTexture"
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


    <!-- --------------------------------------------------- -->
    <!-- Footer dot texture                                   -->
    <!-- --------------------------------------------------- -->

    <pattern
      id="footerDots"
      width="18"
      height="18"
      patternUnits="userSpaceOnUse"
    >

      <circle
        cx="2"
        cy="2"
        r="1.1"
        fill="#f6e9ca"
        opacity=".20"
      />

    </pattern>


    <!-- --------------------------------------------------- -->
    <!-- Rounded clipping area                                -->
    <!-- --------------------------------------------------- -->

    <clipPath id="roundedCard">

      <rect
        x="20"
        y="20"
        width="960"
        height="{HEIGHT - 40}"
        rx="22"
      />

    </clipPath>

  </defs>


  <!-- ===================================================== -->
  <!-- OUTER BACKGROUND                                      -->
  <!-- ===================================================== -->

  <rect
    width="{WIDTH}"
    height="{HEIGHT}"
    fill="{PAPER}"
  />


  <!-- ===================================================== -->
  <!-- CARD                                                   -->
  <!-- ===================================================== -->

  <g clip-path="url(#roundedCard)">

    <!-- --------------------------------------------------- -->
    <!-- Main cream paper                                    -->
    <!-- --------------------------------------------------- -->

    <rect
      x="20"
      y="20"
      width="960"
      height="{HEIGHT - 40}"
      fill="{PAPER}"
    />

    <!-- Paper grain -->
    <rect
      x="20"
      y="20"
      width="960"
      height="{HEIGHT - 40}"
      fill="url(#paperTexture)"
    />


    <!-- =================================================== -->
    <!-- HEADER                                               -->
    <!-- =================================================== -->

    <text
      x="55"
      y="70"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="22"
      font-weight="bold"
      letter-spacing="3"
      fill="{TERRACOTTA}"
    >
      MY DIGITAL GARDEN
    </text>


    <text
      x="57"
      y="94"
      font-family="Courier New, monospace"
      font-size="11"
      letter-spacing="1.5"
      fill="{BROWN}"
    >
      BUILD · LEARN · AUTOMATE
    </text>


    <text
      x="945"
      y="72"
      text-anchor="end"
      font-family="Courier New, monospace"
      font-size="11"
      letter-spacing="1"
      fill="{BROWN}"
    >
      EST. 2023
    </text>


    <!-- Hand-drawn divider -->
    <path
      d="
        M55 115
        C130 110 190 118 260 113
        S390 117 470 112
        S620 117 700 113
        S830 117 945 112
      "
      fill="none"
      stroke="{TERRACOTTA}"
      stroke-width="2"
      opacity=".7"
    />


    <!-- =================================================== -->
    <!-- ABOUT / INTRO                                       -->
    <!-- =================================================== -->

    <text
      x="55"
      y="180"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="62"
      font-weight="900"
      letter-spacing="-3"
      fill="{TERRACOTTA}"
    >
      ABOUT ME
    </text>


    <text
      x="58"
      y="220"
      font-family="Courier New, monospace"
      font-size="13"
      fill="{BROWN}"
      letter-spacing="1"
    >
      A PASSIONATE DEVELOPER · MAKER · PROBLEM SOLVER
    </text>


    <!-- --------------------------------------------------- -->
    <!-- Small decorative flower                             -->
    <!-- --------------------------------------------------- -->

    <g transform="translate(900 175)">

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
        fill="{TERRACOTTA}"
      />

    </g>


    <!-- =================================================== -->
    <!-- LANGUAGE STACK                                      -->
    <!-- =================================================== -->

    <text
      x="55"
      y="300"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="53"
      font-weight="900"
      letter-spacing="-2"
      fill="{TERRACOTTA}"
    >
      LANGUAGE
    </text>


    <text
      x="55"
      y="352"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="53"
      font-weight="900"
      letter-spacing="-2"
      fill="{TERRACOTTA}"
    >
      STACK
    </text>


    <text
      x="58"
      y="375"
      font-family="Courier New, monospace"
      font-size="11"
      fill="{BROWN}"
      letter-spacing="1"
    >
      WHAT'S GROWING IN MY REPOSITORIES
    </text>


    <!-- --------------------------------------------------- -->
    <!-- The six automatically generated rows go here.       -->
    <!-- --------------------------------------------------- -->

    {language_rows}


    <!-- =================================================== -->
    <!-- DIVIDER                                             -->
    <!-- =================================================== -->

    <path
      d="M55 {FOOTER_Y - 55} H945"
      stroke="{TERRACOTTA}"
      stroke-width="2"
      opacity=".7"
    />


    <!-- =================================================== -->
    <!-- SMALL DEVELOPER QUOTE                               -->
    <!-- =================================================== -->

    <text
      x="55"
      y="{FOOTER_Y - 25}"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="18"
      font-style="italic"
      fill="{BROWN}"
    >
      “Build things. Break things. Learn from both.”
    </text>


    <!-- =================================================== -->
    <!-- FOOTER                                              -->
    <!-- =================================================== -->

    <rect
      x="20"
      y="{FOOTER_Y}"
      width="960"
      height="{HEIGHT - FOOTER_Y}"
      fill="{TERRACOTTA}"
    />


    <!-- Footer texture -->
    <rect
      x="20"
      y="{FOOTER_Y}"
      width="960"
      height="{HEIGHT - FOOTER_Y}"
      fill="url(#footerDots)"
    />


    <text
      x="55"
      y="{FOOTER_Y + 42}"
      font-family="Georgia, 'Times New Roman', serif"
      font-size="24"
      font-weight="bold"
      fill="{LIGHT_CREAM}"
    >
      MADE WITH CURIOSITY
    </text>


    <text
      x="55"
      y="{FOOTER_Y + 67}"
      font-family="Courier New, monospace"
      font-size="11"
      letter-spacing="1"
      fill="{LIGHT_CREAM}"
      opacity=".9"
    >
      CULTIVATED ACROSS {repository_count} GITHUB REPOSITORIES
    </text>


    <!-- Decorative star -->
    <text
      x="935"
      y="{FOOTER_Y + 55}"
      text-anchor="middle"
      font-family="Georgia, serif"
      font-size="30"
      fill="{LIGHT_CREAM}"
    >
      ✦
    </text>

  </g>


  <!-- ===================================================== -->
  <!-- OUTER BORDER                                          -->
  <!-- ===================================================== -->

  <rect
    x="20"
    y="20"
    width="960"
    height="{HEIGHT - 40}"
    rx="22"
    fill="none"
    stroke="{LIGHT_CREAM}"
    stroke-width="3"
    opacity=".9"
  />

</svg>
"""


# =============================================================
# MAIN PROGRAM
# =============================================================


def main():
    """
    Main entry point.

    GitHub Actions supplies:

        GITHUB_USERNAME
        GITHUB_TOKEN

    The script can also be run locally if those environment
    variables are supplied.
    """


    # ---------------------------------------------------------
    # Get the GitHub username.
    # ---------------------------------------------------------

    username = (
        os.environ.get(
            "GITHUB_USERNAME"
        )
        or os.environ.get(
            "GITHUB_REPOSITORY_OWNER"
        )
    )


    if not username:

        raise RuntimeError(
            "GITHUB_USERNAME or "
            "GITHUB_REPOSITORY_OWNER "
            "must be set."
        )


    # ---------------------------------------------------------
    # GitHub Actions automatically provides GITHUB_TOKEN.
    # ---------------------------------------------------------

    token = os.environ.get(
        "GITHUB_TOKEN"
    )


    print()
    print(
        "=========================================="
    )

    print(
        "       SOUPLITTLE LANGUAGE STACK"
    )

    print(
        "=========================================="
    )

    print()

    print(
        f"GitHub user: {username}"
    )

    print()


    # =========================================================
    # 1. COLLECT LANGUAGE DATA
    # =========================================================

    totals, repository_count = (
        calculate_language_totals(
            username,
            token,
        )
    )


    # =========================================================
    # 2. COMBINE C + C++
    # =========================================================

    totals = combine_cpp_and_c(
        totals
    )


    # =========================================================
    # 3. CALCULATE REAL PERCENTAGES
    # =========================================================

    languages = calculate_percentages(
        totals
    )


    # =========================================================
    # 4. TAKE THE TOP SIX
    # =========================================================

    display_languages = (
        select_display_languages(
            languages
        )
    )


    # =========================================================
    # DEBUG OUTPUT
    # =========================================================
    #
    # This is useful when the GitHub Action runs.
    #
    # You can look at the Action log and see exactly what
    # GitHub thinks your language percentages are.
    # =========================================================

    print()
    print(
        "All detected languages:"
    )

    print()


    for language in languages:

        print(
            f"  {language['name']:<20}"
            f"{language['percentage']:>7.2f}%"
        )


    print()
    print(
        "Languages shown on the card:"
    )

    print()


    for index, language in enumerate(
        display_languages,
        start=1,
    ):

        print(
            f"  {index}. "
            f"{language['name']:<18}"
            f"{language['percentage']:>7.2f}%"
        )


    print()


    # =========================================================
    # 5. GENERATE SVG
    # =========================================================

    svg = generate_svg(
        display_languages,
        repository_count,
    )


    # ---------------------------------------------------------
    # Make sure the assets directory exists.
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ---------------------------------------------------------
    # Write the generated SVG.
    # ---------------------------------------------------------

    OUTPUT_FILE.write_text(
        svg,
        encoding="utf-8",
    )


    print(
        f"Generated: {OUTPUT_FILE}"
    )

    print()


# =============================================================
# RUN SCRIPT
# =============================================================

if __name__ == "__main__":

    main()