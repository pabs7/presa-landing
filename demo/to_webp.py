# Optimiza las capturas de la landing: PNG de e2e/capture-output/ -> WebP en landing/img/.
# Uso: python to_webp.py <carpeta de PNG> <carpeta de salida> (ver landing/demo/README.md).
import sys
from pathlib import Path

from PIL import Image

# Ancho final de cada captura: las del móvil van en un marco de unos 300 px (x2 para pantallas nítidas).
WIDTHS = {'panel-importar': 1100}
PHONE_WIDTH = 600


def convert(*, source: Path, target_dir: Path) -> Path:
    """Redimensiona la captura a su ancho final y la guarda en WebP."""
    width = WIDTHS.get(source.stem, PHONE_WIDTH)
    image = Image.open(source).convert('RGB')
    height = round(image.height * width / image.width)
    target = target_dir / f'{source.stem}.webp'
    image.resize((width, height), Image.LANCZOS).save(target, 'WEBP', quality=82, method=6)
    return target


if __name__ == '__main__':
    source_dir, target_dir = (Path(arg) for arg in (sys.argv[1:3] if len(sys.argv) > 2 else ('/in', '/out')))
    target_dir.mkdir(parents=True, exist_ok=True)
    for png in sorted(source_dir.glob('*.png')):
        print(convert(source=png, target_dir=target_dir))
