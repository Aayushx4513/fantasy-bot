import os
import json

DATA_DIR = "data/trivia/categories"
OUTPUT_FILE = "data/trivia_questions.json"

def parse_trivia_file(filepath):
    questions = []

    # 🔥 FIX: Try multiple encodings
    content = None
    for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            with open(filepath, "r", encoding=encoding, errors="ignore") as f:
                content = f.read()
            break
        except Exception:
            continue

    if not content:
        return []

    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 3:
            continue

        question = lines[0]
        answer = lines[1]
        choices = lines[2:]

        # Skip if any line has issues
        if not question or not answer or not choices:
            continue

        questions.append({
            "question": question,
            "answer": answer,
            "choices": choices
        })

    return questions


def main():
    all_questions = []

    for filename in os.listdir(DATA_DIR):
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.isfile(filepath):
            category = filename
            try:
                questions = parse_trivia_file(filepath)

                for q in questions:
                    q["category"] = category
                    all_questions.append(q)

                print(f"✅ {category}: {len(questions)} questions")
            except Exception as e:
                print(f"⚠️ {category}: SKIPPED ({e})")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Total: {len(all_questions)} questions saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
