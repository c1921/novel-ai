# Project instructions

This is a Chinese fiction project.

Use the globally installed `novel` CLI for AI writing tasks backed by your configured OpenAI-compatible API provider. Do not assume the CLI source code exists inside this repository.

## Commands

- Check configuration before generation:
  `novel config doctor`
- Polish a chapter:
  `novel polish <chapter-file>`
- Continue a chapter:
  `novel continue <chapter-file>`
- Rewrite a chapter:
  `novel rewrite <chapter-file> --instruction "<instruction>"`
- Summarize a chapter:
  `novel summarize <chapter-file>`
- Preview context:
  `novel context <chapter-file> --mode <mode>`

## Rules

- Never overwrite files in `chapters/`.
- Write AI-generated prose into `drafts/`.
- Write summaries into `summaries/`.
- Use `--dry-run` when you need to inspect the final prompt.
- Use `--json` when another tool needs machine-readable output.
