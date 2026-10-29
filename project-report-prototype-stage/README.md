# Adaptive Continuous Authentication — Prototype Stage Report

[Read the two-page report](Adaptive_Continuous_Auth_Report_Prototype.pdf) · [Edit the LaTeX source](main.tex)

A two-page progress report organized into Introduction, Methodology and Design, Results and Evaluation, and Conclusion and Pending Work. It includes a completed-module table, observed outcomes, and three diagrams showing the implemented input paths, software checks and an actual idle-window result. All three team members are credited.

The structure is adapted from [Naman Arora’s PrivaLens prototype report](https://github.com/NamanArora2709/ucs503p-202627-privalens/blob/master/project-report-prototype-stage/PrivaLens_Report_Prototype.tex), whose LaTeX source was read on 13 September 2026. The wording, implementation and results describe this repository. Its short progress-report layout is distinct from the project proposal.

`main.pdf` is a synchronized copy for existing repository links. `Adaptive_Continuous_Auth_Report_Prototype.tex` and `main.tex` contain the same revised source.

Build from the repository root:

```sh
mkdir -p /tmp/ucs503-reference-report
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/ucs503-reference-report project-report-prototype-stage/main.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/ucs503-reference-report project-report-prototype-stage/main.tex
cp /tmp/ucs503-reference-report/main.pdf project-report-prototype-stage/Adaptive_Continuous_Auth_Report_Prototype.pdf
cp /tmp/ucs503-reference-report/main.pdf project-report-prototype-stage/main.pdf
```
