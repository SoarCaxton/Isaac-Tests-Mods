import glob
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import re
import io
import numpy as np
from math import atan2, degrees

# 常量
door_keys = ["Left", "Up", "Right", "Down"]
direction_keys = ["Left", "Up-Left", "Up", "Up-Right", "Right", "Down-Right", "Down", "Down-Left"]

# 排序函数：先数字，再字母
def sort_key(exp_id):
    match = re.match(r"(\d+)([a-z]*)", exp_id)
    if match:
        num = int(match.group(1))
        suffix = match.group(2)
        return (num, suffix)
    else:
        return (float("inf"), exp_id)

# 方向相关函数（绘图使用）
def angle_cw(dx, dy):
    ang = degrees(atan2(dy, dx))   # 数学角度：右0，上90，左±180，下-90
    return -ang                    # 转为顺时针

def get_direction(angle):
    if (-180 <= angle < -157.5) or (157.5 <= angle <= 180):
        return "Left"
    elif -157.5 <= angle < -112.5:
        return "Up_Left"
    elif -112.5 <= angle < -67.5:
        return "Up"
    elif -67.5 <= angle < -22.5:
        return "Up_Right"
    elif -22.5 <= angle < 22.5:
        return "Right"
    elif 22.5 <= angle < 67.5:
        return "Down_Right"
    elif 67.5 <= angle < 112.5:
        return "Down"
    elif 112.5 <= angle < 157.5:
        return "Down_Left"
    return "Left"

colors = {
    "Left":"red","Up_Left":"orange","Up":"yellow","Up_Right":"green",
    "Right":"cyan","Down_Right":"blue","Down":"purple","Down_Left":"pink"
}

# 顺时针标注位置（与表格顺序一致）
label_pos = {
    "Left": (-5, 0),
    "Up_Left": (-4, 4),
    "Up": (0, 5),
    "Up_Right": (4, 4),
    "Right": (5, 0),
    "Down_Right": (4, -4),
    "Down": (0, -5),
    "Down_Left": (-4, -4),
}

def plot_grid(exp_id, probs):
    size = 13
    cx, cy = size // 2, size // 2
    fig, ax = plt.subplots(figsize=(4, 4))

    for x in range(size):
        for y in range(size):
            dx, dy = x - cx, y - cy
            if dx == 0 and dy == 0:
                ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor="white", edgecolor="black", linewidth=0.5))
                continue
            ang = angle_cw(dx, dy)
            dir_name = get_direction(ang)
            face = colors[dir_name]
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=face, edgecolor="black", linewidth=0.5))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(exp_id)

    for d, (x_off, y_off) in label_pos.items():
        val = probs.get(f"Dir_{d}", None)
        if val is not None:
            ax.text(cx + x_off, cy + y_off, f"{val * 100:.2f}%", fontsize=8, ha="center", va="center", color="black")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def plot_doors(exp_id, door_probs):
    fig, ax = plt.subplots(figsize=(2.4,2.4))
    ax.set_xlim(0,3)
    ax.set_ylim(0,3)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")

    positions = {
        "Up": (1,2),
        "Left": (0,1),
        "Right": (2,1),
        "Down": (1,0),
        "Center": (1,1)
    }

    for key, (x, y) in positions.items():
        if key == "Center":
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor="white", edgecolor="black", linewidth=0.8))
            ax.text(x + 0.5, y + 0.5, f"{exp_id}", ha="center", va="center", fontsize=10, color="black")
        else:
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor="#f0f0f0", edgecolor="black", linewidth=0.8))
            val = door_probs.get(key, 0.0)
            ax.text(x + 0.5, y + 0.5, f"{val * 100:.2f}%", ha="center", va="center", fontsize=9, color="black")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

# 与 df_prob 对应的方向列名列表（用于后续安全取值）
dir_cols = [f"Dir_{k.replace('-', '_')}" for k in direction_keys]

# 批处理当前目录下所有 .dat 文件
for dat_file in glob.glob("*.dat"):
    base_name = os.path.splitext(os.path.basename(dat_file))[0]
    out_file = f"{base_name}.xlsx"

    with open(dat_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_ids = sorted(data.keys(), key=sort_key)

    # -------- 第一页：实验数据 --------
    rows = []
    for exp_id in sorted_ids:
        exp = data[exp_id]
        row = {"ID": exp_id}
        for k in door_keys:
            row[f"Door_{k}"] = exp["Doors"].get(k, 0)
        row["Total"] = exp.get("Total", 0)
        for k in direction_keys:
            row[f"Dir_{k.replace('-', '_')}"] = exp["Directions"].get(k, 0)
        rows.append(row)

    df_data = pd.DataFrame(rows)

    # -------- 第二页：概率统计 --------
    df_prob = df_data.copy()
    # 防止除以0
    totals = df_data["Total"].replace(0, np.nan)
    for k in door_keys:
        df_prob[f"Door_{k}"] = df_data[f"Door_{k}"] / totals
    for k in direction_keys:
        df_prob[f"Dir_{k.replace('-', '_')}"] = df_data[f"Dir_{k.replace('-', '_')}"] / totals
    # 将 NaN 填为 0（例如 Total 为0 的行）
    df_prob[[f"Door_{k}" for k in door_keys] + dir_cols] = df_prob[[f"Door_{k}" for k in door_keys] + dir_cols].fillna(0)

    # -------- 第三页：方向与门的统计（分组均值/方差/标准差） --------
    df_norm = pd.DataFrame()
    df_norm["ID"] = df_prob["ID"]

    # 门的统计（忽略为0的列）
    door_cols = [f"Door_{k}" for k in door_keys]
    door_probs_nonzero = df_prob[door_cols].replace(0, np.nan)
    df_norm["Door_mean"] = door_probs_nonzero.mean(axis=1, skipna=True).fillna(0)
    for k in door_keys:
        col = f"Door_{k}"
        df_norm[f"{col}(%)"] = (df_prob[col] - df_norm["Door_mean"]) * 100
    df_norm["Door_var(%^2)"] = door_probs_nonzero.mul(100).var(axis=1, ddof=0, skipna=True).fillna(0)
    df_norm["Door_std(%)"] = np.sqrt(df_norm["Door_var(%^2)"])

    # 直角方向（Left, Up, Right, Down）
    dir_straight = [f"Dir_{k.replace('-', '_')}" for k in ["Left","Up","Right","Down"]]
    dir_straight_nonzero = df_prob[dir_straight].replace(0, np.nan)
    df_norm["Dir_straight_mean"] = dir_straight_nonzero.mean(axis=1, skipna=True).fillna(0)
    for col in dir_straight:
        df_norm[f"{col}(%)"] = (df_prob[col] - df_norm["Dir_straight_mean"]) * 100
    df_norm["Dir_straight_var(%^2)"] = dir_straight_nonzero.mul(100).var(axis=1, ddof=0, skipna=True).fillna(0)
    df_norm["Dir_straight_std(%)"] = np.sqrt(df_norm["Dir_straight_var(%^2)"])

    # 斜角方向（Up-Left, Up-Right, Down-Right, Down-Left）
    diag_keys = ["Up-Left","Up-Right","Down-Right","Down-Left"]
    dir_diagonal = [f"Dir_{k.replace('-', '_')}" for k in diag_keys]
    dir_diagonal_nonzero = df_prob[dir_diagonal].replace(0, np.nan)
    df_norm["Dir_diagonal_mean"] = dir_diagonal_nonzero.mean(axis=1, skipna=True).fillna(0)
    for col in dir_diagonal:
        df_norm[f"{col}(%)"] = (df_prob[col] - df_norm["Dir_diagonal_mean"]) * 100
    df_norm["Dir_diagonal_var(%^2)"] = dir_diagonal_nonzero.mul(100).var(axis=1, ddof=0, skipna=True).fillna(0)
    df_norm["Dir_diagonal_std(%)"] = np.sqrt(df_norm["Dir_diagonal_var(%^2)"])
    # 新增列：组合标准差 = sqrt(直角方向方差 + 斜角方向方差)
    df_norm["Dir_combined_std(%)"] = np.sqrt(df_norm["Dir_straight_var(%^2)"] + df_norm["Dir_diagonal_var(%^2)"])


    # 保持列顺序（存在性检查以防极端情况）
    ordered_cols = (
        ["ID", "Door_mean"]
        + [f"Door_{k}(%)" for k in door_keys]
        + ["Door_var(%^2)", "Door_std(%)",
        "Dir_straight_mean"]
        + [f"Dir_{k}(%)" for k in ["Left","Up","Right","Down"]]
        + ["Dir_straight_var(%^2)", "Dir_straight_std(%)",
        "Dir_diagonal_mean"]
        + [f"Dir_{k.replace('-', '_')}(%)" for k in ["Up-Left","Up-Right","Down-Right","Down-Left"]]
        + ["Dir_diagonal_var(%^2)", "Dir_diagonal_std(%)",
        "Dir_combined_std(%)"]   # 新增列放在最后
    )
    ordered_cols = [c for c in ordered_cols if c in df_norm.columns]
    df_norm = df_norm[ordered_cols]

    # -------- 保存到 Excel 并对统计列变色标注 --------
    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        df_data.to_excel(writer, sheet_name="实验数据", index=False)
        df_prob.to_excel(writer, sheet_name="概率统计", index=False)
        df_norm.to_excel(writer, sheet_name="均值偏差(%)方差", index=False)

        workbook = writer.book

        # 获取第三页 worksheet
        worksheet_norm = writer.sheets["均值偏差(%)方差"]

        # 定义高亮格式（可按需修改颜色）
        mean_fmt = workbook.add_format({'bg_color': '#FFF2CC'})   # 浅黄
        var_fmt  = workbook.add_format({'bg_color': '#FCE4D6'})   # 浅橙
        std_fmt  = workbook.add_format({'bg_color': '#E2EFDA'})   # 浅绿

        # 要高亮的列名集合（尽量与 df_norm 列名一致）
        highlight_means = [c for c in ["Door_mean", "Dir_straight_mean", "Dir_diagonal_mean"] if c in df_norm.columns]
        highlight_vars  = [c for c in ["Door_var(%^2)", "Dir_straight_var(%^2)", "Dir_diagonal_var(%^2)"] if c in df_norm.columns]
        highlight_stds  = [c for c in ["Door_std(%)", "Dir_straight_std(%)", "Dir_diagonal_std(%)", "Dir_combined_std(%)"] if c in df_norm.columns]

        # 还可以把单项偏差列也高亮为同一色系（可选）
        # 例如把所有 "(%)" 结尾的列标为淡蓝
        item_diff_fmt = workbook.add_format({'bg_color': '#D9EAF7'})
        item_diff_cols = [c for c in df_norm.columns if c.endswith("(%)") and c not in highlight_stds]

        # 应用格式：按列索引设置
        for col_name in highlight_means:
            col_idx = df_norm.columns.get_loc(col_name)
            worksheet_norm.set_column(col_idx, col_idx, None, mean_fmt)
        for col_name in highlight_vars:
            col_idx = df_norm.columns.get_loc(col_name)
            worksheet_norm.set_column(col_idx, col_idx, None, var_fmt)
        for col_name in highlight_stds:
            col_idx = df_norm.columns.get_loc(col_name)
            worksheet_norm.set_column(col_idx, col_idx, None, std_fmt)
        for col_name in item_diff_cols:
            col_idx = df_norm.columns.get_loc(col_name)
            worksheet_norm.set_column(col_idx, col_idx, None, item_diff_fmt)

        # -------- 新增一页：门概率图（同编号数字的实验排在同一行） --------
        worksheet_doors = workbook.add_worksheet("门概率图")
        writer.sheets["门概率图"] = worksheet_doors

        groups = {}
        for exp_id in sorted_ids:
            m = re.match(r"(\d+)", exp_id)
            num = m.group(1) if m else exp_id
            groups.setdefault(num, []).append(exp_id)

        row_height_unit = 10
        col_width_unit = 3

        group_index = 0
        for num, exp_ids in groups.items():
            r = group_index * row_height_unit
            for j, exp_id in enumerate(exp_ids):
                row = df_prob.loc[df_prob["ID"] == exp_id]
                door_probs = {}
                for k in door_keys:
                    col = f"Door_{k}"
                    door_probs[k] = (row.iloc[0][col] if not row.empty and col in row.columns else 0.0)
                door_probs_for_plot = {
                    "Left": door_probs["Left"],
                    "Up": door_probs["Up"],
                    "Right": door_probs["Right"],
                    "Down": door_probs["Down"]
                }
                buf = plot_doors(exp_id, door_probs_for_plot)
                c = j * col_width_unit
                worksheet_doors.insert_image(r, c, f"{exp_id}_doors.png", {"image_data": buf})
            group_index += 1

        # -------- 方向图页 --------
        worksheet_dirs = workbook.add_worksheet("方向图")
        writer.sheets["方向图"] = worksheet_dirs

        groups = {}
        for exp_id in sorted_ids:
            m = re.match(r"(\d+)", exp_id)
            num = m.group(1) if m else exp_id
            groups.setdefault(num, []).append(exp_id)

        row_offset = 0
        for num, exp_ids in groups.items():
            col_offset = 0
            for exp_id in exp_ids:
                row = df_prob.loc[df_prob["ID"] == exp_id]
                probs = {}
                for col in dir_cols:
                    probs[col] = (row.iloc[0][col] if not row.empty and col in row.columns else 0.0)
                buf = plot_grid(exp_id, probs)
                worksheet_dirs.insert_image(row_offset, col_offset, exp_id + ".png", {"image_data": buf})
                col_offset += 5
            row_offset += 18

    print(f"{out_file} 已生成.")
