# rumdl short help



ashed@mediastation:~/.local/bin$ ./rumdl --help

## A fast Markdown linter written in Rust (Ru(st) MarkDown Linter)

Usage: rumdl [OPTIONS] <COMMAND>

Commands:
  check                  Lint Markdown files and print warnings/errors
  fmt                    Format Markdown files and apply fixes with formatter-style exit codes
  init                   Initialize a new configuration file
  rule                   Show information about a rule or list all rules
  explain                Explain a rule with detailed information and examples
  config                 Show configuration or query a specific key
  server                 Start the Language Server Protocol server
  schema                 Generate or check JSON schema for rumdl.toml
  code-block-tools-docs  Generate or check the built-in code-block-tools docs table
  import                 Import and convert markdownlint configuration files
  vscode                 Install the rumdl VS Code extension
  completions            Generate shell completion scripts
  clean                  Clear the cache
  version                Show version information
  help                   Print this message or the help of the given subcommand(s)

## Options:
      --color <COLOR>
          Control colored output

          [default: auto]
          [possible values: auto, always, never]

  -c, --config <CONFIG_OPTION>
          Path to a configuration file, or an inline TOML override.

          May be passed multiple times. Each value is either a path to a TOML configuration file or an inline `KEY = VALUE` snippet that overrides configuration options at the highest precedence:

          - Rule option: `--config 'MD013.line-length = 20'` - Global option: `--config 'line-length = 20'` - Explicit global section: `--config 'global.line-length = 20'`

          At most one value may be a file path; the rest must be inline TOML. Inline overrides remain in effect when combined with `--no-config` /`--isolated` (the file path is rejected, but inline values still apply).

      --no-config
          Ignore all configuration files and use built-in defaults (--isolated is also accepted)

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version

ashed@mediastation:~/.local/bin$
