import sys
import os
from typing import Any, List, Optional
from PIL import Image, Image as PILImage


class Attribute:
    def __init__(self, key: str, value: Any):
        self.key: str = key
        self.type: type = type(value)
        self.value: Any = value

    def __repr__(self) -> str:
        return f"{self.key}={self.value}"


class Attributes:
    input_attr: Attribute = Attribute("-input", False)
    min_log: Attribute = Attribute("-s", False)
    cell_width: Attribute = Attribute("-cellW", 16)
    cell_height: Attribute = Attribute("-cellH", 16)

    _attr_list: List[Attribute] = [input_attr, min_log, cell_width, cell_height]

    def parse(self, args: List[str]) -> List[str]:
        def set_attr_value(attr: Attribute, value: str) -> None:
            try:
                attr.value = attr.type(value)
            except ValueError:
                print(f"❌ Неверное значение для {attr.key}: {value}")
                sys.exit(1)

        clean_args: List[str] = []
        i: int = 0
        while i < len(args):
            arg: str = args[i]
            matched_attr: Optional[Attribute] = next(
                (a for a in self._attr_list if a.key == arg), None
            )
            if matched_attr:
                if matched_attr.type == bool:
                    matched_attr.value = True
                    i += 1
                else:
                    if i + 1 < len(args):
                        set_attr_value(matched_attr, args[i + 1])
                        i += 2
                    else:
                        print(f"❌ Отсутствует значение для {matched_attr.key}")
                        sys.exit(1)
            else:
                clean_args.append(arg)
                i += 1
        return clean_args

    def keys(self) -> List[str]:
        return [attr.key for attr in self._attr_list]

    def values(self) -> List[Any]:
        return [attr.value for attr in self._attr_list]

    def as_dict(self) -> dict:
        return {attr.key: attr.value for attr in self._attr_list}

    def __getitem__(self, key: str) -> Any:
        attr = next((a for a in self._attr_list if a.key == key), None)
        return attr.value if attr else None

    def __str__(self) -> str:
        return ", ".join(f"{a.key}={a.value}" for a in self._attr_list)


def process_tile(
    img: PILImage.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    export_path: str,
    saved: int,
    attrs: Attributes,
) -> bool:
    box: tuple[int, int, int, int] = (
        x,
        y,
        min(x + attrs.cell_width.value, width),
        min(y + attrs.cell_height.value, height),
    )
    tile = img.crop(box)

    if tile.getbbox() is not None:
        tile_name = f"icon_{saved:03}.png"
        tile.save(os.path.join(export_path, tile_name))
        if not attrs.min_log.value:
            print(f"  ✅  Сохранён тайл {saved:03}: {tile_name}")
        return True
    else:
        if not attrs.min_log.value:
            print(f"  ⏩  Пропущен пустой тайл ({x},{y})")
        return False


def split_image(path: str, attrs: Attributes) -> None:
    try:
        export_path: str = os.path.join(
            os.path.dirname(os.path.abspath(path)),
            f"{os.path.splitext(os.path.basename(path))[0]}_export",
        )
        os.makedirs(export_path, exist_ok=True)

        img: PILImage.Image = Image.open(path)
        width, height = img.size

        width = width // attrs.cell_width.value * attrs.cell_width.value
        height = height // attrs.cell_height.value * attrs.cell_height.value

        print("=" * 60)
        print(f"🖼️  Файл:         {os.path.basename(path)}")
        print(f"📏 Размер:        {width}x{height} ({img.size[0]}x{img.size[1]})")
        print(f"🔪 Размер тайла:  {attrs.cell_width.value}x{attrs.cell_height.value}")
        print(f"📂 Экспорт:       {export_path}")
        print("=" * 60)

        saved: int = 0
        total: int = 0
        for y in range(0, height, attrs.cell_height.value):
            for x in range(0, width, attrs.cell_width.value):
                total += 1
                if process_tile(img, x, y, width, height, export_path, saved, attrs):
                    saved += 1

        print("=" * 60)
        print(f"🎉 Готово! Сохранено {saved} из {total} тайлов")
        if saved > 0:
            print(f"📂 Папка экспорта: {export_path}")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Ошибка при обработке файла {path}: {e}")


def main(args: List[str]) -> None:
    if not args:
        print("❗ Нет аргументов\n📒 Список возможных параметров:")
        attrs = Attributes()
        for k in attrs.keys():
            print(f"  {k}")
        args = input("Введите команду: ").split()

    attrs: Attributes = Attributes()
    args = attrs.parse(args)

    if attrs.input_attr:
        at = input("Ввод параметров (опционально): ").split()
        if at and len(at) != 0:
            attrs.parse(at)

    if not args:
        print("❗ Не указаны файлы изображений")
        return

    for path in args:
        if not os.path.isfile(path):
            print(f"⏩ Файл не найден: {path}")
            continue
        split_image(path, attrs)


if __name__ == "__main__":
    main(sys.argv[1:])
