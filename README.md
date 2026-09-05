# What is this `cuda_lint_rumdl`

`cuda_lint_rumdl` - is a linter for CudaLint plugin. 


## What is this Cuda Text

Cuda Text is a cross-platform text editor, written in Object Pascal language using the Lazarus IDE, with a focus on performance and a broad featureset, which includes:

- [Syntax highlighting for 300+ languages](https://wiki.freepascal.org/CudaText#List_of_lexers)
- [Multi-carets](https://wiki.freepascal.org/CudaText#Multi-carets), [multi-selections](https://wiki.freepascal.org/CudaText#Multi-selections)
- [Code folding](https://wiki.freepascal.org/CudaText#Folding)
- [Code-tree](https://wiki.freepascal.org/CudaText#Code-Tree) (list of functions/classes/etc., if lexer-supported)
- [Search/replace](https://wiki.freepascal.org/CudaText#Dialog_Find/Replace) with [regular expressions](https://wiki.freepascal.org/CudaText#Regular_expressions)

- [Command palette](https://wiki.freepascal.org/CudaText#Command_Palette)
- [Configuration files in JSON](https://wiki.freepascal.org/CudaText#Configuration)
- [Interface- and syntax-themes](https://wiki.freepascal.org/CudaText#Color_themes)
- [Support for many encodings](https://wiki.freepascal.org/CudaText#Encodings)
- Based on the [ATSynEdit](https://wiki.freepascal.org/ATSynEdit) engine
- [Extensibility via Python add-ons](https://wiki.freepascal.org/CudaText#Add-ons), e.g. [LSP](http://www.wikipedia.org/wiki/Language_Server_Protocol) support

- Built-in HTML and CSS auto-completion
- HTML tag completion with `Tab`
- HTML tooltips on mouse-over
- Hex color code underlining
- Viewer for picture files (jpeg, png, gif, bmp, ico, webp)

https://wiki.freepascal.org/CudaText

---

## How it works

This linter (`cuda_lint_rumdl`) lint markdown files and adds support for markdown lexer. 
It uses `rumdl` callbacks.

`rumdl` - A high-performance Markdown linter, written in `Rust`.


## How to install `rumdl`.

To install `rumdl` on Windows, download `rumdl.exe` from [rumdl GitHub releases](https://github.com/rvben/rumdl/releases) and place it in `tools/rumdl` folder inside CudaText profile directory. Check your ability to run this binary file from this place.


To install `rumdl` on Linux: type in terminal `sudo curl -LsSf https://github.com/rvben/rumdl/blob/main/scripts/rumdl-action.sh | sh`

To install `rumdl` on macOS: type in terminal `brew install rumdl`.


## How to configure `rumdl`

Access configuration via menu: `Options > Settings-plugins > rumdl > Config`
Access fix command via menu: `Plugins > rumdl > Fix current file`
Access fix command with unsafe flag via menu: `Plugins > rumdl > Fix current file (unsafe)`
Access format command via menu: `Plugins > rumdl > Format current file`
Access help via menu: `Options > Settings-plugins > rumdl > Help`

To customize rules, create `settings/rumdl_config.json` with:

```json
{
      "ignore": (
        "MD013",  # Line length (can be restrictive)
        "MD033",  # Inline HTML (often needed for badges/formatting)
        "MD041",  # First line heading (README might start with badges)
    ),
    "select": (
        "MD001",  # Heading increment
        "MD003",  # Heading style
        "MD004",  # List style
        "MD022",  # Blanks around headings
        "MD025",  # Single title
        "MD032",  # Blanks around lists
        "MD047",  # Single trailing newline
    )
}
```
`rumdl` automatically reads `pyproject.toml` or `rumdl.toml` from your project directory.
Plugin select/ignore settings take precedence over project configuration.
