from pathlib import Path

from PIL import Image, ImageDraw


def build_icon(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    size = 512
    image = Image.new("RGBA", (size, size), "#0f172a")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((32, 32, size - 32, size - 32), radius=96, fill="#1d4ed8")
    draw.rounded_rectangle((96, 96, size - 96, size - 96), radius=72, fill="#0ea5e9")
    draw.rounded_rectangle((160, 160, size - 160, size - 160), radius=48, fill="#f8fafc")

    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    image.save(output_path, format="ICO", sizes=icon_sizes)


if __name__ == "__main__":
    build_icon(Path("assets/app.ico"))
    print("Generated assets/app.ico")
