FIXME TODO write this readme

# Some notes on the tests in the `tests/` directory


We detect the badness in all of the following arxiv papers. This list
was taken from https://arxiv.org/pdf/2507.06185, which is the paper
"Hidden Prompts in Manuscripts Exploit AI-Assisted Peer Review". It
should be noted that the current implementation yields false positives
when run on 2507.06185v1.pdf, except when regex splitting is used
(with nlp diffing and analysis).

(Unfortunately, regex splitting misses the badness in one of the bad
examples below. So at this stage, we don't make regex splitting the
default.)

2212.08983v2.pdf
2403.08142v2.pdf
2406.17241v3.pdf
2406.17253v2.pdf
2407.16803v3.pdf
2408.13940v3.pdf
2501.08667v1.pdf
2501.13461v1.pdf
2502.19918v2.pdf
2505.11718v1.pdf
2505.15075v1.pdf
2505.16211v1.pdf
2506.00418v1.pdf
2506.01324v1.pdf
2506.03074v1.pdf
2506.11111v1.pdf
2506.13901v1.pdf

2505.15075v1.pdf has benign prompts in the paper text, highlighting
why just looking for prmopts in papers is insufficient.

2505.11718v1.pdf is even a paper about building an LLM-based automated
peer reviewer!

For 2406.17253v2.pdf, 2506.11111v1.pdf and 2505.16211v1.pdf we detect
one (of many) hidden LLM instructions in the paper, when using the nlp
analysis method with the default bad phrases list. This shows the
limitations of that analysis method and/or the default bad phrases
list.