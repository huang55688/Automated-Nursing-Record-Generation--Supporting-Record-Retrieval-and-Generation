import matplotlib.pyplot as plt
import pandas as pd

# 設置中文字體
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Noto Sans CJK TC', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# -------------------- 挑選與排序資料 --------------------
record_ids = list(range(1, 21))

# ✅ MICU選取項目
expert_1_sel = [1, 2, 15, 16, 18]
expert_2_sel = [1, 2, 3, 15, 18]
system_sel   = [1, 2, 15, 16, 18]

# ✅ MICU排序名次
expert_1_rank = {15: 1, 18: 2, 1: 3, 2: 4, 16: 5}
expert_2_rank = {15: 1, 2: 2, 1: 3, 18: 4, 3: 5}
system_rank   = {15: 1, 2: 2, 18: 3, 1: 4, 16: 5}

# -------------------- 建立 DataFrame --------------------
df = pd.DataFrame({
    '專家一': [1 if i in expert_1_sel else 0 for i in record_ids],
    '專家二': [1 if i in expert_2_sel else 0 for i in record_ids],
    '系統'  : [1 if i in system_sel   else 0 for i in record_ids]
}, index=[str(i) for i in record_ids])

# -------------------- 繪製堆疊長條圖 --------------------
fig, ax = plt.subplots(figsize=(12, 6))
bars = df.plot(kind='bar', stacked=True, ax=ax,
               color=["#8da0cb", "#fc8d62", "#66c2a5"])

ax.set_title("專家問卷結果", fontsize=16)
ax.set_xlabel("記錄", fontsize=12)
ax.set_ylabel("選擇票數", fontsize=12)
ax.set_yticks(range(0, 4, 1))
ax.set_xticklabels(df.index, rotation=0)
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.legend(title="來源")

# 容器順序與 DataFrame column 順序一致
rank_dicts = [expert_1_rank, expert_2_rank, system_rank]

for container, rank_dict in zip(bars.containers, rank_dicts):
    for idx, rect in enumerate(container):  # idx 對應到 record_ids[idx]
        record = record_ids[idx]
        if rect.get_height() == 0:
            continue  # 沒選中的 bar 不標
        rank = rank_dict.get(record, None)
        if rank is not None:
            ax.text(rect.get_x() + rect.get_width() / 2,
                    rect.get_y() + rect.get_height() / 2,
                    str(rank),
                    ha='center', va='center',
                    color='white', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.tight_layout(rect=[0, 0.05, 1, 1])  # ↓ 底部 5% 留白
fig.text(0.5, 0.01, "※ 柱內白字 = 各來源對該記錄的排序名次",
         ha='center', va='bottom', fontsize=10)
plt.show()
