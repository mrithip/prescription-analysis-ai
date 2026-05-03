from pathlib import Path
from PIL import Image, ImageDraw

FIXTURE_PATH = Path(__file__).resolve().parent.parent / 'tests' / 'fixtures' / 'rx.jpg'
FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)

image = Image.new('RGB', (600, 300), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
draw.text((30, 40), 'Rx Prescription Sample', fill=(0, 0, 0))
draw.text((30, 120), 'Medication: MockDrug 5mg', fill=(0, 0, 0))
draw.text((30, 180), 'Dosage: 1 tablet once daily', fill=(0, 0, 0))
image.save(FIXTURE_PATH, quality=95)
print(f'Created fixture image: {FIXTURE_PATH}')
