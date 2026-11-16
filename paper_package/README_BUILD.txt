Build Instructions for ECG Calibration Manuscript
===================================================

Paper Title: How Much Labelled Rest is Needed? Leak-Free Baseline Calibration for Single-Lead ECG Stress Detection on WESAD
Author: Mukesh Yadav (JSS Academy of Technical Education, Noida, India)

Package Structure:
------------------
  main.tex          - Main LaTeX source document (IEEEtran conference format)
  IEEEtran.cls      - IEEEtran LaTeX document class
  numbers.tex       - Generated LaTeX macros for all quantitative figures
  tables/           - LaTeX table fragments (\input into main.tex)
    tab_ml_benchmark.tex
    tab_calibration_length.tex
    tab_ablation.tex
    tab_thresholds.tex
    tab_hw_profile.tex
  figures/          - Only figures referenced in the manuscript
    DEMO_Pan_Tompkins_QRS_Detection.png
    FINAL_ROC_Curve.png
    FINAL_Personalized_Feature_Ablation.png
    FIG_Hardware_Testbed_Composite.png
    FIG_Dashboard_SinglePage_M4D_Descrambled.png
  refs.bib          - Cleaned BibTeX bibliography file
  main.pdf          - Pre-compiled camera-ready PDF (6 pages)

Compilation Options:
--------------------

Option A: Standard 4-step TeX toolchain (pdflatex + bibtex)
  1. pdflatex main.tex
  2. bibtex main
  3. pdflatex main.tex
  4. pdflatex main.tex

Option B: Automated latexmk
  latexmk -pdf main.tex

Option C: Standalone Tectonic
  tectonic main.tex

Requirements:
-------------
  - TeX distribution: TeX Live 2022+, MacTeX 2022+, or MiKTeX 22.0+
  - Required packages: IEEEtran (cls), cite, amsmath, amssymb, amsfonts,
    algorithmic, graphicx, textcomp, xcolor, booktabs, multirow, url,
    microtype, xspace.
