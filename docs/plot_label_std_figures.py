#!/usr/bin/env python3
"""Generate design-review figures from r17-interface label mf_info.out files."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

CV_NAMES = [
    "water_coord",
    "tail1_z.z",
    "tail2_z.z",
    "head_z.z",
    "r17_cso4_min",
    "r17_rg",
]

CV_LABELS = {
    "water_coord": "Water coordination",
    "tail1_z.z": "Tail1 z",
    "tail2_z.z": "Tail2 z",
    "head_z.z": "Head z",
    "r17_cso4_min": "R17-CSO4 min dist",
    "r17_rg": "R17 Rg",
}


def parse_mf_info(path: Path) -> tuple[list[float], list[float]] | None:
    force_values: list[float] | None = None
    std_values: list[float] | None = None
    with open(path) as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("mean force value"):
                force_values = [float(x) for x in stripped.split()[3:] if x]
            elif stripped.startswith("mean force std"):
                std_values = [float(x) for x in stripped.split()[3:] if x]
    if force_values is None or std_values is None:
        return None
    if len(force_values) != len(std_values):
        return None
    return force_values, std_values


def load_label_data(label_root: Path) -> dict[str, dict[str, np.ndarray]]:
    grouped: dict[str, list[tuple[list[float], list[float]]]] = {}
    for path in sorted(label_root.glob("iter*/**/mf_info.out")):
        parsed = parse_mf_info(path)
        if parsed is None:
            continue
        force, std = parsed
        iter_key = path.parts[path.parts.index("label") + 1]
        grouped.setdefault(iter_key, []).append((force, std))

    out: dict[str, dict[str, np.ndarray]] = {}
    for iter_key, rows in grouped.items():
        forces = np.array([row[0] for row in rows], dtype=float)
        stds = np.array([row[1] for row in rows], dtype=float)
        out[iter_key] = {"forces": forces, "stds": stds}
    return out


def would_discard(std_row: np.ndarray, thresholds: np.ndarray) -> bool:
    return bool(np.any(std_row > thresholds))


def retention_rate(data: np.ndarray, thresholds: np.ndarray) -> float:
    if len(data) == 0:
        return 0.0
    kept = sum(not would_discard(row, thresholds) for row in data)
    return kept / len(data)


def cv_titles(cv_dim: int) -> list[str]:
    titles = []
    for idx in range(cv_dim):
        name = CV_NAMES[idx] if idx < len(CV_NAMES) else f"cv{idx + 1}"
        titles.append(CV_LABELS.get(name, name))
    return titles


def plot_fig_a_force_std_by_cv(
    forces: np.ndarray,
    stds: np.ndarray,
    output: Path,
    iter_key: str,
) -> None:
    cv_dim = forces.shape[1]
    titles = cv_titles(cv_dim)
    fig, axes = plt.subplots(2, cv_dim, figsize=(3.0 * cv_dim, 6.2), squeeze=False)

    for col_idx in range(cv_dim):
        ax_force = axes[0, col_idx]
        ax_std = axes[1, col_idx]

        force_col = forces[:, col_idx]
        std_col = stds[:, col_idx]

        ax_force.hist(force_col, bins=18, color="#E45756", alpha=0.85, edgecolor="white")
        ax_std.hist(std_col, bins=18, color="#4C78A8", alpha=0.85, edgecolor="white")

        ax_force.set_title(titles[col_idx], fontsize=10)
        ax_force.set_xlabel("mean force")
        ax_std.set_xlabel("mf_std")

        if col_idx == 0:
            ax_force.set_ylabel(f"{iter_key}\nforce count")
            ax_std.set_ylabel(f"{iter_key}\nstd count")

        ax_force.axvline(0.0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)

    fig.suptitle(
        f"Fig A ({iter_key}): mean force and mf_std distribution by CV (n={len(forces)})",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_fig_force_magnitude_summary(
    forces: np.ndarray,
    stds: np.ndarray,
    output: Path,
    iter_key: str,
) -> None:
    cv_dim = forces.shape[1]
    titles = cv_titles(cv_dim)
    x = np.arange(cv_dim)
    width = 0.36

    force_abs_median = np.median(np.abs(forces), axis=0)
    force_abs_p90 = np.quantile(np.abs(forces), 0.90, axis=0)
    std_median = np.median(stds, axis=0)
    std_p90 = np.quantile(stds, 0.90, axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].bar(x - width / 2, force_abs_median, width, label="median |F|", color="#E45756")
    axes[0].bar(x + width / 2, force_abs_p90, width, label="p90 |F|", color="#F58518", alpha=0.85)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(titles, rotation=30, ha="right")
    axes[0].set_ylabel("kJ/(mol·unit)")
    axes[0].set_title(f"{iter_key}: mean force magnitude by CV")
    axes[0].legend(fontsize=8)
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x - width / 2, std_median, width, label="median std", color="#4C78A8")
    axes[1].bar(x + width / 2, std_p90, width, label="p90 std", color="#72B7B2", alpha=0.85)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(titles, rotation=30, ha="right")
    axes[1].set_ylabel("same unit as mean force")
    axes[1].set_title(f"{iter_key}: mf_std by CV")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)

    fig.suptitle(f"Force vs std magnitude comparison ({iter_key}, n={len(forces)})", fontsize=13)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_fig_b_retention_iter3(
    stds: np.ndarray,
    scalar_threshold: float,
    per_cv_threshold: np.ndarray,
    output: Path,
    iter_key: str,
) -> None:
    xs = np.linspace(0.2, 15.0, 80)
    ys = [retention_rate(stds, np.full(stds.shape[1], t)) for t in xs]
    per_cv_rate = retention_rate(stds, per_cv_threshold)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs, ys, marker="o", markersize=3, linewidth=1.8, color="#4C78A8", label=f"{iter_key} scalar sweep")
    ax.axvline(
        scalar_threshold,
        color="#E45756",
        linestyle="--",
        linewidth=1.5,
        label=f"current scalar={scalar_threshold}",
    )
    ax.scatter(
        [np.mean(per_cv_threshold)],
        [per_cv_rate],
        s=100,
        marker="*",
        color="#F58518",
        label=f"{iter_key} per-CV p90 ({per_cv_rate:.0%})",
        zorder=5,
    )

    ax.set_xlim(0, 15)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("scalar std_threshold")
    ax.set_ylabel("retention rate")
    ax.set_title(f"Fig B: retention rate vs threshold ({iter_key}, n={len(stds)})")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9, loc="best")
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_fig_c_heatmap(
    stds: np.ndarray,
    thresholds: np.ndarray,
    output: Path,
    title: str,
    cbar_label: str,
) -> None:
    ratio = stds / thresholds.reshape(1, -1)
    discard_mask = ratio > 1.0
    cv_dim = stds.shape[1]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    im = ax.imshow(ratio, aspect="auto", cmap="YlOrRd", vmin=0, vmax=max(2.0, ratio.max()))
    ax.set_xticks(range(cv_dim))
    ax.set_xticklabels(cv_titles(cv_dim), rotation=30, ha="right")
    ax.set_yticks(range(len(stds)))
    ax.set_yticklabels([str(i + 1) for i in range(len(stds))], fontsize=8)
    ax.set_ylabel("sample index")
    ax.set_title(title)

    for i in range(ratio.shape[0]):
        for j in range(ratio.shape[1]):
            if discard_mask[i, j]:
                ax.text(j, i, "×", ha="center", va="center", color="black", fontsize=8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def derive_per_cv_threshold(stds: np.ndarray, quantile: float = 0.90) -> np.ndarray:
    return np.quantile(stds, quantile, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--label-root",
        type=Path,
        default=Path("/personal/rid-reproduce/r17-interface/v1/result/label"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/personal/rid-reproduce/rid-kit/docs/figures"),
    )
    parser.add_argument("--focus-iter", type=str, default="iter3")
    parser.add_argument("--scalar-threshold", type=float, default=10.0)
    parser.add_argument(
        "--per-cv-threshold",
        type=str,
        default="auto",
        help='Comma-separated list or "auto" (p90 per CV from focus iter)',
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_by_iter = load_label_data(args.label_root)
    if not data_by_iter:
        raise SystemExit(f"No mf_info.out found under {args.label_root}")
    if args.focus_iter not in data_by_iter:
        raise SystemExit(f"{args.focus_iter} not found under {args.label_root}")

    forces = data_by_iter[args.focus_iter]["forces"]
    stds = data_by_iter[args.focus_iter]["stds"]

    if args.per_cv_threshold == "auto":
        per_cv = derive_per_cv_threshold(stds, quantile=0.90)
    else:
        per_cv = np.array([float(x) for x in args.per_cv_threshold.split(",")], dtype=float)

    plot_fig_a_force_std_by_cv(
        forces,
        stds,
        args.output_dir / f"fig_a_mf_std_hist_by_cv_{args.focus_iter}.png",
        iter_key=args.focus_iter,
    )
    plot_fig_force_magnitude_summary(
        forces,
        stds,
        args.output_dir / f"fig_force_std_magnitude_{args.focus_iter}.png",
        iter_key=args.focus_iter,
    )
    plot_fig_b_retention_iter3(
        stds,
        scalar_threshold=args.scalar_threshold,
        per_cv_threshold=per_cv,
        output=args.output_dir / "fig_b_retention_vs_threshold.png",
        iter_key=args.focus_iter,
    )
    plot_fig_c_heatmap(
        stds,
        thresholds=np.full(stds.shape[1], args.scalar_threshold),
        output=args.output_dir / f"fig_c_heatmap_{args.focus_iter}_scalar_{args.scalar_threshold:g}.png",
        title=(
            f"Fig C: mf_std/threshold heatmap ({args.focus_iter}, "
            f"scalar={args.scalar_threshold:g}, ×=discard)"
        ),
        cbar_label=f"mf_std / scalar threshold ({args.scalar_threshold:g}); >1 discards sample",
    )
    plot_fig_c_heatmap(
        stds,
        thresholds=per_cv,
        output=args.output_dir / f"fig_c_heatmap_{args.focus_iter}_per_cv.png",
        title=f"Fig C: mf_std/threshold heatmap ({args.focus_iter}, per-CV p90, ×=discard)",
        cbar_label="mf_std / per-CV p90 threshold (ratio; >1 discards sample)",
    )

    summary_path = args.output_dir / "figure_summary.txt"
    scalar_rate = retention_rate(stds, np.full(stds.shape[1], args.scalar_threshold))
    per_cv_rate = retention_rate(stds, per_cv)
    with open(summary_path, "w") as handle:
        handle.write(f"label_root={args.label_root}\n")
        handle.write(f"focus_iter={args.focus_iter}\n")
        handle.write(f"scalar_threshold={args.scalar_threshold}\n")
        handle.write(f"per_cv_threshold={np.array2string(per_cv, precision=4, separator=', ')}\n\n")
        handle.write(f"n={len(stds)}\n")
        handle.write(f"scalar_retention={scalar_rate:.3f}\n")
        handle.write(f"per_cv_retention={per_cv_rate:.3f}\n\n")
        handle.write("median_abs_force=")
        handle.write(np.array2string(np.median(np.abs(forces), axis=0), precision=4, separator=", "))
        handle.write("\nmedian_std=")
        handle.write(np.array2string(np.median(stds, axis=0), precision=4, separator=", "))
        handle.write("\n")

    print(f"Wrote figures to {args.output_dir}")
    print(summary_path.read_text())


if __name__ == "__main__":
    main()
