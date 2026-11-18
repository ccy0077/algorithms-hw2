"""Measure separate-chaining probe counts across load factors."""

import csv
import math
import random
from pathlib import Path

from src.hash_table import HashTable


TABLE_CAPACITY = 4093
LOAD_FACTORS = (0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4)
REPETITIONS = 10
FAILED_SEARCHES_PER_REPETITION = 2000
RANDOM_SEED = 62026
TOKEN_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
OUTPUT_DIRECTORY = Path(__file__).resolve().parent


def _random_token(generator, length):
    return "".join(generator.choice(TOKEN_ALPHABET) for _ in range(length))


def _random_url(generator, kind, repetition, index):
    host = _random_token(generator, 12)
    path = _random_token(generator, 28)
    return f"https://{host}.example/{path}?kind={kind}&rep={repetition}&id={index}"


def _count_probes(table, key):
    index = table._hash(key)
    node = table.buckets[index]
    comparisons = 0
    while node is not None:
        comparisons += 1
        if node.key == key:
            return comparisons
        node = node.next
    return comparisons


def _measure_load_factor(target_load_factor):
    item_count = int(target_load_factor * TABLE_CAPACITY + 0.5)
    actual_load_factor = item_count / TABLE_CAPACITY
    successful_means = []
    failed_means = []

    for repetition in range(REPETITIONS):
        generator = random.Random(RANDOM_SEED + repetition)
        table = HashTable(
            initial_capacity=TABLE_CAPACITY,
            auto_resize=False,
        )
        stored_urls = []
        for index in range(item_count):
            url = _random_url(generator, "stored", repetition, index)
            table.put(url, index)
            stored_urls.append(url)

        generator.shuffle(stored_urls)
        successful_comparisons = math.fsum(
            _count_probes(table, url) for url in stored_urls
        )
        successful_means.append(successful_comparisons / item_count)

        failed_comparisons = 0
        for index in range(FAILED_SEARCHES_PER_REPETITION):
            url = _random_url(generator, "missing", repetition, index)
            failed_comparisons += _count_probes(table, url)
        failed_means.append(
            failed_comparisons / FAILED_SEARCHES_PER_REPETITION
        )

    successful_average = math.fsum(successful_means) / REPETITIONS
    failed_average = math.fsum(failed_means) / REPETITIONS
    successful_theory = 1 + actual_load_factor / 2
    failed_theory = actual_load_factor

    return (
        target_load_factor,
        actual_load_factor,
        successful_average,
        successful_theory,
        abs(successful_average - successful_theory),
        failed_average,
        failed_theory,
        abs(failed_average - failed_theory),
    )


def _write_csv(results):
    path = OUTPUT_DIRECTORY / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "target_load_factor",
                "actual_load_factor",
                "success_avg_node_comparisons",
                "success_theoretical",
                "success_absolute_error",
                "failure_avg_node_comparisons",
                "failure_theoretical",
                "failure_absolute_error",
                "repetitions",
                "failed_searches_per_repetition",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result[0]:.2f}",
                    f"{result[1]:.6f}",
                    f"{result[2]:.6f}",
                    f"{result[3]:.6f}",
                    f"{result[4]:.6f}",
                    f"{result[5]:.6f}",
                    f"{result[6]:.6f}",
                    f"{result[7]:.6f}",
                    REPETITIONS,
                    FAILED_SEARCHES_PER_REPETITION,
                )
            )
    return path


def _write_svg(results):
    width = 960
    height = 600
    left = 88
    right = 38
    top = 58
    bottom = 82
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_value = max(
        max(result[2], result[3], result[5], result[6])
        for result in results
    )
    y_max = max(1, math.ceil(max_value))

    def x_position(load_factor):
        return left + load_factor / 4 * plot_width

    def y_position(value):
        return top + (y_max - value) / y_max * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>평균 탐색 노드 비교 수: 실험값과 이론값</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="480" y="30" text-anchor="middle" font-size="18">개별 체이닝 탐색 비용</text>',
    ]

    for tick in range(y_max + 1):
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="12">{tick}</text>'
        )

    for tick in range(5):
        x = x_position(tick)
        parts.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#eeeeee"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" font-size="12">{tick}</text>'
        )

    parts.extend(
        (
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222222"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222222"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 24}" text-anchor="middle" font-size="14">적재율 α (항목/버킷)</text>',
            f'<text x="22" y="{top + plot_height / 2:.2f}" text-anchor="middle" font-size="14" transform="rotate(-90 22 {top + plot_height / 2:.2f})">평균 비교 노드 수 (노드/탐색)</text>',
        )
    )

    series = (
        ("성공 탐색 실험값", 2, "#2563eb", ""),
        ("성공 탐색 이론값", 3, "#2563eb", "7 5"),
        ("실패 탐색 실험값", 5, "#dc2626", ""),
        ("실패 탐색 이론값", 6, "#dc2626", "7 5"),
    )
    for label, result_index, color, dash in series:
        points = " ".join(
            f"{x_position(result[1]):.2f},{y_position(result[result_index]):.2f}"
            for result in results
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"{dash_attribute}/>'
        )
        for result in results:
            parts.append(
                f'<circle cx="{x_position(result[1]):.2f}" cy="{y_position(result[result_index]):.2f}" r="3" fill="{color}"/>'
            )

    legend_x = left + 18
    legend_y = top + 18
    for index, (label, _, color, dash) in enumerate(series):
        y = legend_y + index * 22
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 28}" y2="{y}" stroke="{color}" stroke-width="2"{dash_attribute}/>'
        )
        parts.append(
            f'<text x="{legend_x + 36}" y="{y + 4}" font-size="12">{label}</text>'
        )

    parts.append("</svg>")
    path = OUTPUT_DIRECTORY / "probe_graph.svg"
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def main():
    results = [_measure_load_factor(alpha) for alpha in LOAD_FACTORS]
    csv_path = _write_csv(results)
    svg_path = _write_svg(results)

    print(
        f"M={TABLE_CAPACITY}, seed={RANDOM_SEED}, repetitions={REPETITIONS}, "
        f"failed searches per load factor per repetition={FAILED_SEARCHES_PER_REPETITION}"
    )
    print(
        "target α | actual α | success avg/theory/abs err | "
        "failure avg/theory/abs err"
    )
    for result in results:
        print(
            f"{result[0]:8.2f} | {result[1]:8.6f} | "
            f"{result[2]:7.4f} / {result[3]:7.4f} / {result[4]:7.4f} | "
            f"{result[5]:7.4f} / {result[6]:7.4f} / {result[7]:7.4f}"
        )
    print(f"CSV: {csv_path}")
    print(f"SVG: {svg_path}")


if __name__ == "__main__":
    main()
