#!/bin/bash
cd /home/yzk/my_arxiv
source /home/yzk/anaconda3/etc/profile.d/conda.sh
conda activate arxiv
python arxiv_search.py -d 2026-04-14 -l
