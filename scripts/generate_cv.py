import html
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
index_path = root / 'index.html'
output_path = root / 'files' / 'Suren_Rana_CV.pdf'


def strip_tags(value: str) -> str:
    text = re.sub(r'<!--.*?-->', ' ', value, flags=re.S)
    text = re.sub(r'<script.*?</script>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_section(content: str, section_id: str, comment_tag: str) -> str:
    pattern = rf'<div[^>]*id="{re.escape(section_id)}"[^>]*>(.*?)<!-- /{comment_tag} -->'
    match = re.search(pattern, content, flags=re.S | re.I)
    if not match:
        return ''
    return strip_tags(match.group(1))


def build_pdf_text(index_html: str) -> list[str]:
    sections = {
        'home': extract_section(index_html, 'home', 'HOME'),
        'about': extract_section(index_html, 'about', 'ABOUT'),
        'credentials': extract_section(index_html, 'credentials', 'CREDENTIALS'),
        'timeline': extract_section(index_html, 'timeline', 'TIMELINE'),
    }

    lines = [
        'Suren Rana',
        'Software Engineer | Java | Spring Boot | Python | AWS',
        'surenrana113@gmail.com | linkedin.com/in/surensrm | github.com/dev-suren',
        '',
        'Professional Summary',
    ]
    lines.extend(wrap_text(sections['about'][:900], 90))
    lines.extend(['', 'Highlights',])
    lines.extend(wrap_text(sections['credentials'][:900], 90))
    lines.extend(['', 'Career Timeline'])
    lines.extend(wrap_text(sections['timeline'][:1400], 90))
    return lines


def wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ''
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = f'{current} {word}'.strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def escape_pdf_text(text: str) -> str:
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def write_pdf(output_path: Path, lines: list[str]) -> None:
    content_lines = ['BT', '/F1 12 Tf', '50 760 Td']
    for line in lines[:80]:
        content_lines.append(f'({escape_pdf_text(line)}) T*')
    content_lines.append('ET')
    content_stream = '\n'.join(content_lines)
    content_bytes = content_stream.encode('latin-1', 'replace')

    objects = [
        (1, b'<< /Type /Catalog /Pages 2 0 R >>'),
        (2, b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>'),
        (3, b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>'),
        (4, f'<< /Length {len(content_bytes)} >>\nstream\n'.encode('latin-1') + content_bytes + b'\nendstream'),
        (5, b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'),
    ]

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for obj_id, body in objects:
        offsets.append(len(pdf))
        pdf.extend(f'{obj_id} 0 obj\n'.encode('latin-1'))
        pdf.extend(body)
        pdf.extend(b'\nendobj\n')

    xref_position = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('latin-1'))
    pdf.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        pdf.extend(f'{offset:010d} 00000 n \n'.encode('latin-1'))

    pdf.extend(b'trailer\n')
    pdf.extend(f'<< /Size {len(objects) + 1} /Root 1 0 R >>\n'.encode('latin-1'))
    pdf.extend(f'startxref\n{xref_position}\n%%EOF\n'.encode('latin-1'))

    output_path.write_bytes(pdf)


if __name__ == '__main__':
    index_html = index_path.read_text(encoding='utf-8')
    lines = build_pdf_text(index_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_pdf(output_path, lines)
    print(f'Generated: {output_path}')
