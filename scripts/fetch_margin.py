"""
抓取台灣期交所股價指數類保證金公告，寫成 margin-data.json 供前端讀取。
資料來源：https://www.taifex.com.tw/cht/5/indexMargingDown（Big5 編碼 CSV）
"""
import csv
import io
import json
import sys
import urllib.request

SOURCE_URL = "https://www.taifex.com.tw/cht/5/indexMargingDown"
OUTPUT_PATH = "margin-data.json"

# CSV 商品別欄位名稱 -> margin-data.json 裡對應的 key
ROW_MAP = {
    "小型臺指": "mtx",
    "微型臺指期貨": "tmf",
    "臺指選擇權風險保證金(A)值": "txo_a",
    "臺指選擇權風險保證金(B)值": "txo_b",
    "臺指選擇權風險保證金(C)值": "txo_c",
}


def fetch_csv_text() -> str:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
    return raw.decode("big5", errors="replace")


def parse(csv_text: str) -> dict:
    lines = csv_text.splitlines()
    if not lines:
        raise ValueError("empty response from TAIFEX")

    updated = ""
    first_line = lines[0].strip()
    if first_line.startswith("更新日期"):
        updated = first_line.split(":", 1)[-1].strip()
        lines = lines[1:]

    result = {"updated": updated}
    reader = csv.reader(lines)
    for row in reader:
        if not row:
            continue
        name = row[0].strip()
        key = ROW_MAP.get(name)
        if key is None:
            continue
        try:
            settle, maintain, initial = (int(row[1]), int(row[2]), int(row[3]))
        except (ValueError, IndexError):
            continue
        result[key] = {"settle": settle, "maintain": maintain, "initial": initial}

    missing = [k for k in ROW_MAP.values() if k not in result]
    if missing:
        raise ValueError(f"missing expected rows in TAIFEX CSV: {missing}")
    return result


def main():
    csv_text = fetch_csv_text()
    data = parse(csv_text)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {OUTPUT_PATH}: {data}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"fetch_margin.py failed: {e}", file=sys.stderr)
        sys.exit(1)
