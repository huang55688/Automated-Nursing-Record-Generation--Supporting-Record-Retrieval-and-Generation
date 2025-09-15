import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import cohen_kappa_score
from scipy.stats import kendalltau

# --- 0. 資料區 -------------------------------------------------
# 0-1 向量（20 筆）— 1=挑中, 0=未挑
expert1_select = np.array([1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,1])
expert2_select = np.array([1,1,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0])
system_select  = np.array([1,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,1])

# --- 1. Cohen’s Kappa -----------------------------------------
k1 = cohen_kappa_score(system_select, expert1_select)
k2 = cohen_kappa_score(system_select, expert2_select)

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(
    ['System vs Expert 1', 'System vs Expert 2'],
    [k1, k2],
    color=['#4C72B0', '#55A868'],
    edgecolor='black'
)

# 加上數值標籤
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5), textcoords='offset points',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

# 美化圖表
ax.set_ylim(0, 1.1)
ax.set_ylabel("Kappa Value", fontsize=14)
ax.set_title("Cohen's Kappa – Selection Consistency", fontsize=16, fontweight='bold')
ax.tick_params(axis='x', labelsize=12)
ax.tick_params(axis='y', labelsize=12)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.show()

# --- 2. Kendall’s τ ------------------------------------------
# 固定要比對的 6 筆記錄：1, 2, 3, 15, 16, 18
target_records = [1, 2, 3, 15, 16, 18]

# 名次轉換（沒選的就給最後一名，這邊給 6）
def build_rank(ranking_dict, target_list, max_rank=6):
    return [ranking_dict.get(i, max_rank) for i in target_list]

# 建立排序字典
system_rank_dict = {15:1, 2:2, 18:3, 1:4, 16:5}
expert1_rank_dict = {15:1, 18:2, 1:3, 2:4, 16:5}
expert2_rank_dict = {15:1, 2:2, 1:3, 18:4, 3:5}

# 將指定6筆記錄的排序取出，若未選則補6
system_rank = build_rank(system_rank_dict, target_records)
expert1_rank = build_rank(expert1_rank_dict, target_records)
expert2_rank = build_rank(expert2_rank_dict, target_records)

# --- 繪圖函式 ------------------------------------------
def scatter_kendall(sys, exp, label, *, color='C0', marker='o', line_color=None):
    if line_color is None:
        line_color = color
    tau, p = kendalltau(sys, exp)
    plt.figure()
    plt.scatter(sys, exp, c=color, marker=marker, edgecolors='black')
    mn, mx = min(sys + exp), max(sys + exp)
    plt.plot([mn, mx], [mn, mx], '--', color=line_color)
    plt.title(f"{label}\nKendall τ = {tau:.2f}, p = {p:.3f}")
    plt.xlabel("System Rank")
    plt.ylabel("Expert Rank")
    plt.tight_layout()
    plt.show()

# 第一張圖：System vs Expert 1（固定6筆）
scatter_kendall(system_rank, expert1_rank,
                "System vs Expert 1",
                color='#4C72B0', marker='o')

# 第二張圖：System vs Expert 2（固定6筆）
scatter_kendall(system_rank, expert2_rank,
                "System vs Expert 2",
                color='#55A868', marker='s')
