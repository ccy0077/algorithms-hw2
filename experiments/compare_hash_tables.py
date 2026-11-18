"""Compare separate chaining and linear probing across load factors."""

import csv
import math
import random
from pathlib import Path

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


TABLE_CAPACITY = 4093
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
REPETITIONS = 10
FAILED_SEARCHES_PER_REPETITION = 2000
RANDOM_SEED = 82026
TOKEN_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
OUTPUT_DIRECTORY = Path(__file__).resolve().parent


def _random_token(generator, length):
    return "".join(generator.choice(TOKEN_ALPHABET) for _ in range(length))


def _random_url(generator, kind, repetition, index):
    host = _random_token(generator, 12)
    path = _random_token(generator, 28)
    return f"https://{host}.example/{path}?kind={kind}&rep={repetition}&id={index}"


def _count_chaining_probes(table, key):
    index = table._hash(key)
    node = table.buckets[index]
    probes = 0
    while node is not None:
        probes += 1
        if node.key == key:
            return probes
        node = node.next
    return probes


def _count_linear_probes(table, key):
    index = table._hash(key)
    for probes in range(1, table.capacity + 1):
        entry = table.slots[index]
        if entry is None or entry.key == key:
            return probes
        index = (index + 1) % table.capacity
    raise AssertionError("query was not found and the linear table has no empty slot")


def _measure_load_factor(target_load_factor):
    item_count = int(target_load_factor * TABLE_CAPACITY + 0.5)
    actual_load_factor = item_count / TABLE_CAPACITY
    chaining_success_total = 0
    chaining_failure_total = 0
    linear_success_total = 0
    linear_failure_total = 0

    for repetition in range(REPETITIONS):
        generator = random.Random(RANDOM_SEED + repetition)
        chaining = HashTable(
            initial_capacity=TABLE_CAPACITY,
            auto_resize=False,
        )
        linear = LinearProbingHashTable(
            initial_capacity=TABLE_CAPACITY,
            auto_resize=False,
        )
        stored_urls = []
        for index in range(item_count):
            url = _random_url(generator, "stored", repetition, index)
            chaining.put(url, index)
            linear.put(url, index)
            stored_urls.append(url)

        successful_queries = stored_urls[:]
        generator.shuffle(successful_queries)
        failed_queries = [
            _random_url(generator, "missing", repetition, index)
            for index in range(FAILED_SEARCHES_PER_REPETITION)
        ]

        for url in successful_queries:
            chaining_success_total += _count_chaining_probes(chaining, url)
            linear_success_total += _count_linear_probes(linear, url)
        for url in failed_queries:
            chaining_failure_total += _count_chaining_probes(chaining, url)
            linear_failure_total += _count_linear_probes(linear, url)

    total_successful_queries = item_count * REPETITIONS
    total_failed_queries = FAILED_SEARCHES_PER_REPETITION * REPETITIONS
    chaining_success_average = chaining_success_total / total_successful_queries
    chaining_failure_average = chaining_failure_total / total_failed_queries
    linear_success_average = linear_success_total / total_successful_queries
    linear_failure_average = linear_failure_total / total_failed_queries

    chaining_success_theory = 1 + actual_load_factor / 2
    chaining_failure_theory = actual_load_factor
    linear_success_theory = 0.5 * (
        1 + 1 / (1 - actual_load_factor)
    )
    linear_failure_theory = 0.5 * (
        1 + 1 / (1 - actual_load_factor) ** 2
    )

    return (
        target_load_factor,
        actual_load_factor,
        chaining_success_average,
        chaining_success_theory,
        abs(chaining_success_average - chaining_success_theory),
        chaining_failure_average,
        chaining_failure_theory,
        abs(chaining_failure_average - chaining_failure_theory),
        linear_success_average,
        linear_success_theory,
        abs(linear_success_average - linear_success_theory),
        linear_failure_average,
        linear_failure_theory,
        abs(linear_failure_average - linear_failure_theory),
    )


def _write_csv(results):
    path = OUTPUT_DIRECTORY / "comparison_results.csv"
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "target_load_factor",
                "actual_load_factor",
                "chaining_success_avg_node_probes",
                "chaining_success_theoretical",
                "chaining_success_absolute_error",
                "chaining_failure_avg_node_probes",
                "chaining_failure_theoretical",
                "chaining_failure_absolute_error",
                "linear_success_avg_slot_probes",
                "linear_success_theoretical",
                "linear_success_absolute_error",
                "linear_failure_avg_slot_probes",
                "linear_failure_theoretical",
                "linear_failure_absolute_error",
                "capacity",
                "repetitions",
                "failed_searches_per_repetition",
            )
        )
        for result in results:
            writer.writerow(
                (
                    f"{result[0]:.1f}",
                    f"{result[1]:.6f}",
                    f"{result[2]:.6f}",
                    f"{result[3]:.6f}",
                    f"{result[4]:.6f}",
                    f"{result[5]:.6f}",
                    f"{result[6]:.6f}",
                    f"{result[7]:.6f}",
                    f"{result[8]:.6f}",
                    f"{result[9]:.6f}",
                    f"{result[10]:.6f}",
                    f"{result[11]:.6f}",
                    f"{result[12]:.6f}",
                    f"{result[13]:.6f}",
                    TABLE_CAPACITY,
                    REPETITIONS,
                    FAILED_SEARCHES_PER_REPETITION,
                )
            )
    return path


def _write_svg(results):
    width = 1280
    height = 680
    left = 88
    right = 350
    top = 62
    bottom = 82
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_value = max(
        result[index]
        for result in results
        for index in (2, 3, 5, 6, 8, 9, 11, 12)
    )
    y_max = max(1, math.ceil(max_value * 1.08))

    def x_position(load_factor):
        return left + load_factor * plot_width

    def y_position(value):
        return top + (y_max - value) / y_max * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>개별 체이닝과 선형 탐지의 평균 탐색 probe 비교</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="465" y="32" text-anchor="middle" font-size="18">해시 테이블 전략별 탐색 비용: 실험값과 이론값</text>',
    ]

    tick_step = max(1, math.ceil(y_max / 8))
    y_ticks = list(range(0, y_max + 1, tick_step))
    if y_ticks[-1] != y_max:
        y_ticks.append(y_max)
    for tick in y_ticks:
        y = y_position(tick)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" font-size="12">{tick}</text>'
        )

    for tick in range(11):
        load_factor = tick / 10
        x = x_position(load_factor)
        parts.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#eeeeee"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" font-size="12">{load_factor:.1f}</text>'
        )

    parts.extend(
        (
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222222"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222222"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 24}" text-anchor="middle" font-size="14">적재율 α (항목/칸)</text>',
            f'<text x="22" y="{top + plot_height / 2:.2f}" text-anchor="middle" font-size="14" transform="rotate(-90 22 {top + plot_height / 2:.2f})">평균 probe 수 (probe/탐색)</text>',
        )
    )

    series = (
        ("체이닝 성공 실험값", 2, "#2563eb", ""),
        ("체이닝 성공 이론값", 3, "#2563eb", "7 5"),
        ("체이닝 실패 실험값", 5, "#dc2626", ""),
        ("체이닝 실패 이론값", 6, "#dc2626", "7 5"),
        ("선형 성공 실험값", 8, "#059669", ""),
        ("선형 성공 이론값", 9, "#059669", "7 5"),
        ("선형 실패 실험값", 11, "#9333ea", ""),
        ("선형 실패 이론값", 12, "#9333ea", "7 5"),
    )
    for _, result_index, color, dash in series:
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

    legend_x = left + plot_width + 26
    legend_y = top + 20
    for index, (label, _, color, dash) in enumerate(series):
        y = legend_y + index * 25
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 28}" y2="{y}" stroke="{color}" stroke-width="2"{dash_attribute}/>'
        )
        parts.append(
            f'<text x="{legend_x + 36}" y="{y + 4}" font-size="12">{label}</text>'
        )

    parts.append("</svg>")
    path = OUTPUT_DIRECTORY / "comparison_graph.svg"
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def main():
    results = [_measure_load_factor(alpha) for alpha in LOAD_FACTORS]
    csv_path = _write_csv(results)
    svg_path = _write_svg(results)

    print(
        f"M={TABLE_CAPACITY}, seed={RANDOM_SEED}, repetitions={REPETITIONS}, "
        f"failed searches per repetition={FAILED_SEARCHES_PER_REPETITION}"
    )
    print(
        "α | chain success exp/theory/error | chain failure exp/theory/error | "
        "linear success exp/theory/error | linear failure exp/theory/error"
    )
    for result in results:
        print(
            f"{result[1]:.6f} | "
            f"{result[2]:.3f}/{result[3]:.3f}/{result[4]:.3f} | "
            f"{result[5]:.3f}/{result[6]:.3f}/{result[7]:.3f} | "
            f"{result[8]:.3f}/{result[9]:.3f}/{result[10]:.3f} | "
            f"{result[11]:.3f}/{result[12]:.3f}/{result[13]:.3f}"
        )
    print(f"CSV: {csv_path}")
    print(f"SVG: {svg_path}")


if __name__ == "__main__":
    main()
