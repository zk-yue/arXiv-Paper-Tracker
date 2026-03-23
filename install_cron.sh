#!/bin/bash
# 安装定时任务脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_PATH="$HOME/anaconda3"

echo "安装arXiv论文检索定时任务..."
echo "脚本路径: $SCRIPT_DIR"

# 创建cron任务（每天早上9点执行）
# 使用conda环境运行
# 注意：如需启用LLM分析，请在命令后添加 -l 参数
CRON_JOB="0 9 * * * source $CONDA_PATH/etc/profile.d/conda.sh && conda activate arxiv && cd $SCRIPT_DIR && python arxiv_search.py >> $SCRIPT_DIR/cron.log 2>&1"

# 检查是否已存在
(crontab -l 2>/dev/null | grep -v "arxiv_search.py") | crontab -

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "定时任务已安装！"
echo "执行时间: 每天早上 9:00"
echo ""
echo "查看当前定时任务: crontab -l"
echo "查看日志: cat $SCRIPT_DIR/cron.log"
echo "手动运行: conda activate arxiv && python arxiv_search.py"