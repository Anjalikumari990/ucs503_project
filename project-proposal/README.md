# Adaptive Continuous Authentication — Proposal

[Read the proposal](main.pdf). The editable source is [main.tex](main.tex).

The proposal includes the project name first, standard headings without template side notes, and three workflow/architecture diagrams. The original submitted author list is retained. Current prototype behavior and future extensions are distinguished in the text.

Build from the repository root with XeLaTeX (run twice for PDF navigation):

```sh
mkdir -p /tmp/ucs503-proposal-build
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/ucs503-proposal-build project-proposal/main.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/ucs503-proposal-build project-proposal/main.tex
cp /tmp/ucs503-proposal-build/main.pdf project-proposal/main.pdf
```

The existing `code/Proposal.tex` and `code/Proposal.pdf` copies are synchronized with this revision for compatibility. Keep them synchronized when revising the proposal.
