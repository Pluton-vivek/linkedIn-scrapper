import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from html import unescape
from html.parser import HTMLParser
from typing import List, Dict, Any
from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


@dataclass
class Experience:
    title: str = ""
    company: str = ""
    duration: str = ""
    location: str = ""
    description: str = ""


@dataclass
class Education:
    school: str = ""
    degree: str = ""
    duration: str = ""


def clean_text(value: str) -> str:
    text = unescape(value or "")
    return re.sub(r"\s+", " ", text).strip()


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: List[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = clean_text(data)
        if cleaned:
            self.text_parts.append(cleaned)


def strip_html(html_fragment: str) -> str:
    parser = SimpleHTMLTextExtractor()
    parser.feed(html_fragment)
    return " ".join(parser.text_parts)


def scrape_profile_html(profile_url: str) -> str:
    req = Request(profile_url, headers=DEFAULT_HEADERS)
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _extract_json_ld_person(html: str) -> Dict[str, Any]:
    script_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for block in script_blocks:
        raw = block.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Person":
                return item

    return {}


def _extract_h2_section_list_items(html: str, section_name: str) -> List[str]:
    pattern = re.compile(
        rf"<section[^>]*>.*?<h[1-3][^>]*>\s*{section_name}\s*</h[1-3]>.*?</section>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return []

    section_html = match.group(0)
    li_blocks = re.findall(r"<li[^>]*>(.*?)</li>", section_html, flags=re.IGNORECASE | re.DOTALL)
    values = [clean_text(strip_html(li)) for li in li_blocks]
    return [v for v in values if v]


def parse_linkedin_html(html: str) -> Dict[str, Any]:
    person = _extract_json_ld_person(html)

    name = clean_text(str(person.get("name", "")))
    headline = clean_text(str(person.get("jobTitle", "")))
    summary = clean_text(str(person.get("description", "")))

    if not name:
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
        if h1_match:
            name = clean_text(strip_html(h1_match.group(1)))

    experience_lines = _extract_h2_section_list_items(html, "Experience")
    education_lines = _extract_h2_section_list_items(html, "Education")
    skills_lines = _extract_h2_section_list_items(html, "Skills")

    experience: List[Experience] = [Experience(title=line) for line in experience_lines[:8]]
    education: List[Education] = [Education(school=line) for line in education_lines[:5]]

    return {
        "name": name,
        "headline": headline,
        "location": "",
        "summary": summary,
        "experience": [asdict(e) for e in experience],
        "education": [asdict(e) for e in education],
        "skills": skills_lines[:30],
    }


def build_ats_resume(profile: Dict[str, Any]) -> str:
    name = profile.get("name") or "Candidate Name"
    headline = profile.get("headline", "")
    location = profile.get("location", "")
    summary = profile.get("summary", "")

    lines = [f"# {name}"]
    if headline:
        lines.append(f"**{headline}**")
    if location:
        lines.append(location)

    lines.append("\n## Professional Summary")
    lines.append(summary or "Results-driven professional with demonstrated experience.")

    lines.append("\n## Experience")
    experiences = profile.get("experience", [])
    if experiences:
        for exp in experiences:
            title = exp.get("title", "Role")
            company = exp.get("company", "")
            duration = exp.get("duration", "")
            header = " — ".join([p for p in [title, company] if p])
            if duration:
                header += f" ({duration})"
            lines.append(f"- {header}".strip())
            if exp.get("description"):
                lines.append(f"  - {exp['description']}")
    else:
        lines.append("- Add your professional experience details here.")

    lines.append("\n## Education")
    education = profile.get("education", [])
    if education:
        for edu in education:
            school = edu.get("school", "")
            degree = edu.get("degree", "")
            duration = edu.get("duration", "")
            line = " — ".join([p for p in [school, degree] if p]) or "Education Entry"
            if duration:
                line += f" ({duration})"
            lines.append(f"- {line}")
    else:
        lines.append("- Add your education details here.")

    lines.append("\n## Skills")
    skills = profile.get("skills", [])
    lines.append(", ".join(skills) if skills else "Add your relevant ATS keywords and skills.")

    return "\n".join(lines).strip() + "\n"


def markdown_to_plain_text(markdown: str) -> str:
    text = re.sub(r"^#\s+", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"^##\s+", "", text, flags=re.MULTILINE)
    return text


def save_outputs(profile: Dict[str, Any], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "profile_data.json"), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    resume_md = build_ats_resume(profile)
    with open(os.path.join(out_dir, "resume.md"), "w", encoding="utf-8") as f:
        f.write(resume_md)

    with open(os.path.join(out_dir, "resume.txt"), "w", encoding="utf-8") as f:
        f.write(markdown_to_plain_text(resume_md))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape/parse a LinkedIn profile and generate an ATS-friendly resume."
    )
    parser.add_argument("--profile-url", help="Public LinkedIn profile URL.")
    parser.add_argument("--html-file", help="Path to saved LinkedIn profile HTML file.")
    parser.add_argument("--out-dir", default="output", help="Output directory.")
    args = parser.parse_args()

    if not args.profile_url and not args.html_file:
        raise SystemExit("Provide one of --profile-url or --html-file")

    if args.html_file:
        with open(args.html_file, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        html = scrape_profile_html(args.profile_url)

    profile = parse_linkedin_html(html)
    save_outputs(profile, args.out_dir)
    print(f"Saved ATS resume outputs to: {args.out_dir}")


if __name__ == "__main__":
    main()
