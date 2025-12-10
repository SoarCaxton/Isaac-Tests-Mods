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
    """计算顺时针角度：左 -180/180°，上 -90°，右 0°，下 +90°"""
    ang = degrees(atan2(dy, dx))   # 数学角度：右0，上90，左±180，下-90
    return -ang                    # 转为顺时针

def get_direction(angle):
    """根据顺时针角度返回方向名称"""
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

    # 绘制格子
    for x in range(size):
        for y in range(size):
            dx, dy = x - cx, y - cy
            if dx == 0 and dy == 0:
                ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor="white", edgecolor="black", linewidth=0.5))
                continue
            ang_cw = angle_cw(dx, dy)
            dir_name = get_direction(ang_cw)
            face = colors[dir_name]
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=face, edgecolor="black", linewidth=0.5))

    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(exp_id)

    # 在对应方向标注概率（页2数据，百分数，两位小数，黑色字体）
    for d, (x_off, y_off) in label_pos.items():
        val = probs.get(f"Dir_{d}", None)
        if val is not None:
            ax.text(cx + x_off, cy + y_off, f"{val * 100:.2f}%",
                    fontsize=8, ha="center", va="center", color="black")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def plot_doors(exp_id, door_probs):
    """
    绘制一个实验的门概率图：左、上、右、下、中五格
    door_probs: dict {"Left": p, "Up": p, "Right": p, "Down": p}
    """
    fig, ax = plt.subplots(figsize=(2.4,2.4))
    ax.set_xlim(0,3)
    ax.set_ylim(0,3)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")

    # 定义五个格子的位置（以左下为(0,0)）
    positions = {
        "Up": (1,2),
        "Left": (0,1),
        "Right": (2,1),
        "Down": (1,0),
        "Center": (1,1)
    }

    # 绘制格子并标注
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

# 批处理当前目录下所有 .dat 文件
for dat_file in glob.glob("*.dat"):
    base_name = os.path.splitext(os.path.basename(dat_file))[0]
    out_file = f"{base_name}.xlsx"

    # 读取 JSON 数据
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
    for k in door_keys:
        df_prob[f"Door_{k}"] = df_data[f"Door_{k}"] / df_data["Total"]
    for k in direction_keys:
        df_prob[f"Dir_{k.replace('-', '_')}"] = df_data[f"Dir_{k.replace('-', '_')}"] / df_data["Total"]

    # -------- 第三页：概率与平均值的偏差（单位：百分比），忽略为0的列计算平均值，并新增方差列（百分比单位） --------
    df_norm = pd.DataFrame()
    df_norm["ID"] = df_prob["ID"]

    # 门的平均概率（忽略为0的列）
    door_cols = [f"Door_{k}" for k in door_keys]
    door_probs_nonzero = df_prob[door_cols].replace(0, np.nan)
    door_mean = door_probs_nonzero.mean(axis=1, skipna=True).fillna(0)
    df_norm["Door_mean"] = door_mean

    # 门偏差（%）
    for k in door_keys:
        col = f"Door_{k}"
        df_norm[f"{col}(%)"] = (df_prob[col] - df_norm["Door_mean"]) * 100

    # 门方差（以百分比的方差表示）
    door_var_pct2 = door_probs_nonzero.mul(100).var(axis=1, ddof=0, skipna=True).fillna(0)
    df_norm["Door_var(%^2)"] = door_var_pct2
    df_norm["Door_std(%)"] = np.sqrt(df_norm["Door_var(%^2)"])

    # 方向的平均概率（忽略为0的列）
    dir_cols = [f"Dir_{k.replace('-', '_')}" for k in direction_keys]
    dir_probs_nonzero = df_prob[dir_cols].replace(0, np.nan)
    dir_mean = dir_probs_nonzero.mean(axis=1, skipna=True).fillna(0)
    df_norm["Dir_mean"] = dir_mean

    # 方向偏差（%）
    for k in direction_keys:
        col = f"Dir_{k.replace('-', '_')}"
        df_norm[f"{col}(%)"] = (df_prob[col] - df_norm["Dir_mean"]) * 100

    # 方向方差（以百分比的方差表示）
    dir_var_pct2 = dir_probs_nonzero.mul(100).var(axis=1, ddof=0, skipna=True).fillna(0)
    df_norm["Dir_var(%^2)"] = dir_var_pct2
    df_norm["Dir_std(%)"] = np.sqrt(df_norm["Dir_var(%^2)"])

    # 保持列顺序，便于写入 Excel
    ordered_cols = ["ID", "Door_mean"] + [f"Door_{k}(%)" for k in door_keys] + ["Door_var(%^2)", "Door_std(%)", "Dir_mean"] + [f"Dir_{k.replace('-', '_')}(%)" for k in direction_keys] + ["Dir_var(%^2)", "Dir_std(%)"]
    df_norm = df_norm[ordered_cols]

    # -------- 保存到 Excel --------
    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        df_data.to_excel(writer, sheet_name="实验数据", index=False)
        df_prob.to_excel(writer, sheet_name="概率统计", index=False)
        df_norm.to_excel(writer, sheet_name="均值偏差(%)方差", index=False)

        workbook  = writer.book

        # 新增一页：门概率图（同编号数字的实验排在同一行）
        worksheet_doors = workbook.add_worksheet("门概率图")
        writer.sheets["门概率图"] = worksheet_doors

        # 按编号数字部分分组
        groups = {}
        for exp_id in sorted_ids:
            m = re.match(r"(\d+)", exp_id)
            num = m.group(1) if m else exp_id
            groups.setdefault(num, []).append(exp_id)

        row_height_unit = 10   # 每组占用的行数
        col_width_unit = 3     # 每个小图占用的列数

        group_index = 0
        for num, exp_ids in groups.items():
            r = group_index * row_height_unit
            for j, exp_id in enumerate(exp_ids):
                # 取该实验的门概率
                door_probs = {k: df_prob.loc[df_prob["ID"]==exp_id, f"Door_{k}"].values[0] for k in door_keys}
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

        # 原来的方向图页
        worksheet_dirs = workbook.add_worksheet("方向图")
        writer.sheets["方向图"] = worksheet_dirs

        groups = {}
        for exp_id in sorted_ids:
            num = re.match(r"(\d+)", exp_id).group(1)
            groups.setdefault(num, []).append(exp_id)

        row_offset = 0
        for num, exp_ids in groups.items():
            col_offset = 0
            for exp_id in exp_ids:
                # 使用页2的概率数据
                probs = {col: df_prob.loc[df_prob["ID"]==exp_id, col].values[0] for col in dir_cols}
                buf = plot_grid(exp_id, probs)
                worksheet_dirs.insert_image(row_offset, col_offset, exp_id+".png", {"image_data": buf})
                col_offset += 5
            row_offset += 18

    print(f"{out_file} 已生成.")
