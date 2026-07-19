"""本文で使うランニング例の統計量を一元計算する.

入力は ``data/running_example.csv`` のみとし, 本文へ転記する前の丸めて
いない値をJSONで出力する. ``--check`` を付けると, ``docs/修正方針.md``
で確定した基準値に所定の桁で一致するかを検証する.

実行例:
  uv run python data_generation/recalculate_textbook_values.py
  uv run python data_generation/recalculate_textbook_values.py --check
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = ROOT / "data" / "running_example.csv"

VIEWS_PER_MAN = 10_000.0
YEN_PER_OKU = 100_000_000.0
IMPRESSIONS_PER_MAN = 10_000.0

REQUIRED_COLUMNS = {
    "movie_id",
    "has_source",
    "budget",
    "views_30d",
    "rec_impressions",
    "rating_count",
    "avg_rating",
}


def _float(value: float | np.floating[Any]) -> float:
    """NumPyの実数をJSONで扱えるPythonのfloatへ変換する."""

    return float(value)


def _bool_series(series: pd.Series) -> pd.Series:
    """CSVの真偽値列を明示的にboolへそろえる."""

    if pd.api.types.is_bool_dtype(series.dtype):
        return series.astype(bool)

    mapping = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }
    normalized = series.astype(str).str.strip().str.lower().map(mapping)
    if normalized.isna().any():
        invalid = sorted(series[normalized.isna()].astype(str).unique())
        raise ValueError(f"has_sourceに解釈できない値がある: {invalid}")
    return normalized.astype(bool)


def load_data(csv_path: Path) -> pd.DataFrame:
    """入力CSVを読み, 計算前提を検証する."""

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(f"必要な列がない: {sorted(missing_columns)}")
    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("計算対象の列に欠損値がある")
    if df["movie_id"].duplicated().any():
        raise ValueError("movie_idが重複している")

    df = df.copy()
    df["has_source"] = _bool_series(df["has_source"])
    return df


def _summary(values: np.ndarray) -> dict[str, Any]:
    """記述用sと推論用uを同時に計算する."""

    n = len(values)
    if n < 2:
        raise ValueError("分散の計算には2件以上必要")

    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
    mean = values.mean()
    variance_s = values.var(ddof=0)
    variance_u = values.var(ddof=1)
    u = math.sqrt(variance_u)
    se = u / math.sqrt(n)
    t_critical = stats.t.ppf(0.975, df=n - 1)

    return {
        "n": n,
        "mean": _float(mean),
        "median": _float(median),
        "q1": _float(q1),
        "q3": _float(q3),
        "iqr": _float(q3 - q1),
        "minimum": _float(values.min()),
        "maximum": _float(values.max()),
        "variance_s_n_divisor": _float(variance_s),
        "sd_s_n_divisor": _float(math.sqrt(variance_s)),
        "variance_u_n_minus_1_divisor": _float(variance_u),
        "sd_u_n_minus_1_divisor": _float(u),
        "se_mean_using_u": _float(se),
        "ci95_approx_2se": [
            _float(mean - 2.0 * se),
            _float(mean + 2.0 * se),
        ],
        "ci95_normal_1_96se": [
            _float(mean - 1.96 * se),
            _float(mean + 1.96 * se),
        ],
        "ci95_t": [
            _float(mean - t_critical * se),
            _float(mean + t_critical * se),
        ],
        "t_critical_df_n_minus_1": _float(t_critical),
    }


def _welch_comparison(group_true: np.ndarray, group_false: np.ndarray) -> dict[str, Any]:
    """原作あり群と原作なし群のWelch比較を計算する."""

    summary_true = _summary(group_true)
    summary_false = _summary(group_false)

    n_true = summary_true["n"]
    n_false = summary_false["n"]
    mean_true = summary_true["mean"]
    mean_false = summary_false["mean"]
    variance_true = summary_true["variance_u_n_minus_1_divisor"]
    variance_false = summary_false["variance_u_n_minus_1_divisor"]

    component_true = variance_true / n_true
    component_false = variance_false / n_false
    se_difference = math.sqrt(component_true + component_false)
    mean_difference = mean_true - mean_false
    t_value = mean_difference / se_difference
    df_welch = (component_true + component_false) ** 2 / (
        component_true**2 / (n_true - 1)
        + component_false**2 / (n_false - 1)
    )
    p_one_sided = stats.t.sf(t_value, df=df_welch)
    p_two_sided = 2.0 * stats.t.sf(abs(t_value), df=df_welch)
    t_critical = stats.t.ppf(0.975, df=df_welch)

    representative_u = math.sqrt((variance_true + variance_false) / 2.0)
    cohens_d = mean_difference / representative_u

    return {
        "has_source_true": summary_true,
        "has_source_false": summary_false,
        "mean_difference_true_minus_false": _float(mean_difference),
        "se_difference_using_u": _float(se_difference),
        "welch_t": _float(t_value),
        "welch_satterthwaite_df": _float(df_welch),
        "p_one_sided": _float(p_one_sided),
        "p_two_sided": _float(p_two_sided),
        "ci95_approx_2se": [
            _float(mean_difference - 2.0 * se_difference),
            _float(mean_difference + 2.0 * se_difference),
        ],
        "ci95_welch_t": [
            _float(mean_difference - t_critical * se_difference),
            _float(mean_difference + t_critical * se_difference),
        ],
        "representative_u_sqrt_mean_group_variances": _float(representative_u),
        "cohens_d_using_mean_group_variances": _float(cohens_d),
    }


def _correlation(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """n-1割りのu_xy, u_x, u_yと相関係数を計算する."""

    u_xy = np.cov(x, y, ddof=1)[0, 1]
    u_x = x.std(ddof=1)
    u_y = y.std(ddof=1)
    r_from_u = u_xy / (u_x * u_y)
    r_direct = np.corrcoef(x, y)[0, 1]
    if not math.isclose(r_from_u, r_direct, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError("u_xy/(u_x u_y)と相関係数が一致しない")

    return {
        "u_xy_n_minus_1_divisor": _float(u_xy),
        "u_x_n_minus_1_divisor": _float(u_x),
        "u_y_n_minus_1_divisor": _float(u_y),
        "r": _float(r_from_u),
    }


def _regression(
    movie_ids: pd.Series,
    budget_oku_yen: np.ndarray,
    views_man: np.ndarray,
) -> dict[str, Any]:
    """製作費（億円）から視聴回数（万回）への単回帰を計算する."""

    result = stats.linregress(budget_oku_yen, views_man)
    fitted = result.intercept + result.slope * budget_oku_yen
    residuals = views_man - fitted
    x_deviations = budget_oku_yen - budget_oku_yen.mean()
    y_deviations = views_man - views_man.mean()
    sum_cross_deviations = np.sum(x_deviations * y_deviations)
    sum_x_squared_deviations = np.sum(x_deviations**2)

    residual_tolerance = 1e-12
    residual_sign_counts = {
        "positive": int(np.sum(residuals > residual_tolerance)),
        "negative": int(np.sum(residuals < -residual_tolerance)),
        "zero_within_tolerance": int(
            np.sum(np.abs(residuals) <= residual_tolerance)
        ),
    }

    rows = []
    for movie_id, x, y, y_hat, residual in zip(
        movie_ids,
        budget_oku_yen,
        views_man,
        fitted,
        residuals,
        strict=True,
    ):
        rows.append(
            {
                "movie_id": str(movie_id),
                "budget_oku_yen": _float(x),
                "views_man": _float(y),
                "fitted_views_man": _float(y_hat),
                "residual_views_man": _float(residual),
            }
        )

    return {
        "x_unit": "億円",
        "y_unit": "万回",
        "n": len(budget_oku_yen),
        "x_minimum": _float(budget_oku_yen.min()),
        "x_maximum": _float(budget_oku_yen.max()),
        "x_mean": _float(budget_oku_yen.mean()),
        "y_mean": _float(views_man.mean()),
        "sum_cross_deviations": _float(sum_cross_deviations),
        "sum_x_squared_deviations": _float(sum_x_squared_deviations),
        "intercept_a": _float(result.intercept),
        "slope_b_per_oku_yen": _float(result.slope),
        "r": _float(result.rvalue),
        "r_squared": _float(result.rvalue**2),
        "p_two_sided_for_slope": _float(result.pvalue),
        "se_slope": _float(result.stderr),
        "prediction_at_5_oku_yen": _float(result.intercept + result.slope * 5.0),
        "prediction_at_20_oku_yen": _float(result.intercept + result.slope * 20.0),
        "prediction_at_30_oku_yen": _float(result.intercept + result.slope * 30.0),
        "residual_sd": _float(residuals.std(ddof=1)),
        "residual_sign_counts": residual_sign_counts,
        "rows": rows,
    }


def calculate_values(df: pd.DataFrame) -> dict[str, Any]:
    """本文で使う値を丸めずにまとめて返す."""

    views_man = df["views_30d"].to_numpy(dtype=float) / VIEWS_PER_MAN
    budget_oku_yen = df["budget"].to_numpy(dtype=float) / YEN_PER_OKU
    impressions_man = (
        df["rec_impressions"].to_numpy(dtype=float) / IMPRESSIONS_PER_MAN
    )
    avg_rating = df["avg_rating"].to_numpy(dtype=float)
    rating_count = df["rating_count"].to_numpy(dtype=float)

    has_source = df["has_source"].to_numpy(dtype=bool)
    group_true = views_man[has_source]
    group_false = views_man[~has_source]

    rating_4_or_higher_count = int((avg_rating >= 4.0).sum())
    rating_4_or_higher_p = rating_4_or_higher_count / len(df)
    rating_4_or_higher_se = math.sqrt(
        rating_4_or_higher_p * (1.0 - rating_4_or_higher_p) / len(df)
    )

    return {
        "source": str(DEFAULT_CSV_PATH.relative_to(ROOT)),
        "units": {
            "views": "万回",
            "budget": "億円",
            "rec_impressions": "万回",
        },
        "views_30d_man": _summary(views_man),
        "rating_4_or_higher": {
            "n": len(df),
            "count": rating_4_or_higher_count,
            "proportion": _float(rating_4_or_higher_p),
            "se": _float(rating_4_or_higher_se),
            "ci95_approx_2se": [
                _float(rating_4_or_higher_p - 2.0 * rating_4_or_higher_se),
                _float(rating_4_or_higher_p + 2.0 * rating_4_or_higher_se),
            ],
        },
        "has_source_welch_comparison_views_man": _welch_comparison(
            group_true,
            group_false,
        ),
        "correlations": {
            "budget_oku_yen_vs_views_man": _correlation(
                budget_oku_yen,
                views_man,
            ),
            "rec_impressions_man_vs_views_man": _correlation(
                impressions_man,
                views_man,
            ),
            "avg_rating_vs_views_man": _correlation(avg_rating, views_man),
            "rating_count_vs_views_man": _correlation(rating_count, views_man),
        },
        "regression_budget_oku_yen_to_views_man": _regression(
            df["movie_id"],
            budget_oku_yen,
            views_man,
        ),
    }


BENCHMARKS: tuple[tuple[str, tuple[str, ...], float, int], ...] = (
    ("視聴回数平均", ("views_30d_man", "mean"), 209.386, 3),
    ("視聴回数中央値", ("views_30d_man", "median"), 107.084, 3),
    (
        "視聴回数u",
        ("views_30d_man", "sd_u_n_minus_1_divisor"),
        240.785,
        3,
    ),
    (
        "製作費と視聴回数のr",
        ("correlations", "budget_oku_yen_vs_views_man", "r"),
        0.3650,
        4,
    ),
    (
        "おすすめ表示回数と視聴回数のr",
        ("correlations", "rec_impressions_man_vs_views_man", "r"),
        0.8033,
        4,
    ),
    (
        "平均評価と視聴回数のr",
        ("correlations", "avg_rating_vs_views_man", "r"),
        0.2057,
        4,
    ),
    (
        "原作あり件数",
        ("has_source_welch_comparison_views_man", "has_source_true", "n"),
        37,
        0,
    ),
    (
        "原作あり平均",
        ("has_source_welch_comparison_views_man", "has_source_true", "mean"),
        274.082,
        3,
    ),
    (
        "原作ありu",
        (
            "has_source_welch_comparison_views_man",
            "has_source_true",
            "sd_u_n_minus_1_divisor",
        ),
        260.637,
        3,
    ),
    (
        "原作なし件数",
        ("has_source_welch_comparison_views_man", "has_source_false", "n"),
        43,
        0,
    ),
    (
        "原作なし平均",
        ("has_source_welch_comparison_views_man", "has_source_false", "mean"),
        153.717,
        3,
    ),
    (
        "原作なしu",
        (
            "has_source_welch_comparison_views_man",
            "has_source_false",
            "sd_u_n_minus_1_divisor",
        ),
        209.680,
        3,
    ),
    (
        "平均差",
        (
            "has_source_welch_comparison_views_man",
            "mean_difference_true_minus_false",
        ),
        120.365,
        3,
    ),
    (
        "差のSE",
        (
            "has_source_welch_comparison_views_man",
            "se_difference_using_u",
        ),
        53.464,
        3,
    ),
    (
        "Welchのt値",
        ("has_source_welch_comparison_views_man", "welch_t"),
        2.251,
        3,
    ),
    (
        "Welch--Satterthwaite自由度",
        (
            "has_source_welch_comparison_views_man",
            "welch_satterthwaite_df",
        ),
        68.936,
        3,
    ),
    (
        "回帰の偏差積和",
        ("regression_budget_oku_yen_to_views_man", "sum_cross_deviations"),
        12343.872,
        3,
    ),
    (
        "回帰のx偏差平方和",
        (
            "regression_budget_oku_yen_to_views_man",
            "sum_x_squared_deviations",
        ),
        249.763,
        3,
    ),
    (
        "回帰の傾き",
        ("regression_budget_oku_yen_to_views_man", "slope_b_per_oku_yen"),
        49.422,
        3,
    ),
    (
        "回帰の切片",
        ("regression_budget_oku_yen_to_views_man", "intercept_a"),
        108.410,
        3,
    ),
    (
        "回帰の決定係数",
        ("regression_budget_oku_yen_to_views_man", "r_squared"),
        0.1332,
        4,
    ),
    (
        "30億円での外挿値",
        (
            "regression_budget_oku_yen_to_views_man",
            "prediction_at_30_oku_yen",
        ),
        1591.082,
        3,
    ),
    (
        "正の残差の本数",
        (
            "regression_budget_oku_yen_to_views_man",
            "residual_sign_counts",
            "positive",
        ),
        24,
        0,
    ),
    (
        "負の残差の本数",
        (
            "regression_budget_oku_yen_to_views_man",
            "residual_sign_counts",
            "negative",
        ),
        56,
        0,
    ),
)


def _get_path(values: dict[str, Any], path: tuple[str, ...]) -> float:
    current: Any = values
    for key in path:
        current = current[key]
    return float(current)


def check_benchmarks(values: dict[str, Any]) -> bool:
    """確定基準値との丸め後一致を表示する."""

    all_passed = True
    for label, path, expected, digits in BENCHMARKS:
        actual = _get_path(values, path)
        actual_text = f"{actual:.{digits}f}"
        expected_text = f"{expected:.{digits}f}"
        passed = actual_text == expected_text
        status = "PASS" if passed else "FAIL"
        print(f"{status} {label}: {actual_text} (expected {expected_text})")
        all_passed = all_passed and passed
    return all_passed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="入力CSVのパス",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="docs/修正方針.mdの確定基準値と照合する",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = args.csv.resolve()
    df = load_data(csv_path)
    values = calculate_values(df)
    values["source"] = str(csv_path)

    if args.check:
        return 0 if check_benchmarks(values) else 1

    print(json.dumps(values, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
