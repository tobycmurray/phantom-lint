# PhantomLint

Detect unwanted, hidden text in PDF documents.

## Download

Clone this git repository.

## Installation

Change to the directory where you cloned this repository.
We recommend using a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Package

```
pip install -e .
```

The `-e` option installs the package in editable mode for development.

## Usage

```bash
phantomlint input_file.pdf --output output_directory/
```

Use the `-h` or `--help` options to get detailed usage information.

## How does PhantomLint work?

Essentially by comparing the text extracted from the document with
that obtained by rendering the document as a set of images and OCRing
those images. The key insight is that anything that is present in the
document but absent from the OCR is hidden text.

This avoids the brittleness of heuristic hidden-text identification
methods, such as searching for white text, which can easily fail
(for instance when an object has been inserted over black text to
obscure it).

## Examples

Example test cases, including real papers obtained from [arXiv](https://arxiv.org/), are
in the `tests/` directory.

### `bad` examples

Papers with unwanted hidden phrases are in the `tests/bad/` directory.
Many of those papers were taken from the list that appears in
https://arxiv.org/pdf/2507.06185, which is the paper
"Hidden Prompts in Manuscripts Exploit AI-Assisted Peer Review".

2505.15075v1.pdf has benign prompts in the paper text, highlighting
why just looking for prompts in paper text is insufficient.

2505.11718v1.pdf is even a paper about building an LLM-based automated
peer reviewer!

For 2406.17253v2.pdf, 2506.11111v1.pdf and 2505.16211v1.pdf we detect only
one (of many) hidden LLM instructions in the paper, when using the `nlp`
analysis method with the default bad phrases list. This shows the
limitations of that analysis method and/or the default bad phrases
list.

The `tests/bad/` directory contains other PDFs found via Google that
contain hidden text, designed to manipulate LLM analysis. This
includes candidate CVs posted publicly online.

### `good` examples

Test cases without unwanted hidden phrases are in the `tests/good/` directory.
This includes the aforementioned
https://arxiv.org/pdf/2507.06185, as well as some synthetic examples.

### synthetic examples

The `tests/` directory also contains synthetic test cases (both `good` and `bad),
including for
both single- and two-column documents, and utilising a range of strategies
for hiding unwanted text in the documents. These all begin with `fake_`,
to distinguish them from real examples.
