from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "output" / "manas_salt_lake_video"
VOICE_SCRIPT = Path(__file__).with_name("synthesize_manas_voice.ps1")
WIDTH = 1280
HEIGHT = 720
FPS = 12
PAD_SECONDS = 0.85

BG = (11, 24, 31)
PANEL = (20, 39, 47)
PANEL_2 = (27, 51, 59)
TEXT = (235, 243, 239)
MUTED = (151, 174, 177)
TEAL = (65, 190, 178)
BLUE = (69, 152, 214)
AMBER = (241, 183, 83)
CORAL = (235, 111, 92)
GREEN = (115, 184, 128)
PURPLE = (165, 132, 211)

SCENES = [
    {
        "title": "玛纳斯盐湖：13 年演变线索",
        "tag": "概念演示 | 非真实遥感重建",
        "kind": "opener",
        "caption": "基于用户提供的分镜 PDF 制作。以下地图与边界均为概念示意；许可证、开采量、湖体变化和因果关系仍需原始资料核验。",
        "voice": "这是依据所给分镜制作的概念演示，不是真实遥感重建；数据与因果均待核验。",
    },
    {
        "title": "研究范围与两处分场",
        "tag": "位置与分场 | 坐标仅为文档线索",
        "kind": "scope",
        "caption": "PDF 将研究对象描述为新疆玛纳斯盐湖，并列出新乌森、夏孜盖两处分场及近似坐标。",
        "voice": "材料指向新疆玛纳斯盐湖新乌森、夏孜盖两处分场；位置和边界以官方登记资料为准。",
    },
    {
        "title": "证照时间线：需要原件逐项核对",
        "tag": "证照节点 | 文档列示，不等于已独立核实",
        "kind": "timeline",
        "caption": "材料列示 2013、2018、2021、2022 等证照节点；证 3 与证 4 的时间区间有重叠，需查登记档案。",
        "voice": "文档列出二零一三、二零一八、二零二一、二零二二年证照节点；期限及变更关系须查登记档案。",
    },
    {
        "title": "同一湖区，多家权属线索",
        "tag": "权属示意 | 颜色不代表法定边界",
        "kind": "rights",
        "caption": "材料提及宏达夏孜盖、宏达新乌森、宜新和新雅泰。精确拐点坐标多处标为待公开或待核验。",
        "voice": "材料提及宏达、宜新、新雅泰等权属线索；本图分色仅为示意，不代表法定边界。",
    },
    {
        "title": "生产规模：单位不同，不能直接比较",
        "tag": "关键数字 | 证载与实际口径需核验",
        "kind": "production",
        "caption": "文档写有“23 万立方米/年”与“55 万吨/年”。两者单位不同，不能直接据此宣称翻番或超采。",
        "voice": "文档写二十三万立方米与五十五万吨；单位口径不同，不能直接称为翻番或超采。",
    },
    {
        "title": "1.67 米 → 0.17 米：指标定义待核",
        "tag": "深度变化 | 文档给值，不是独立测量结果",
        "kind": "depth",
        "caption": "PDF 给出 2013 年 1.67 米、2026 年 0.17 米（约下降 89.8%）；测量对象、方法和来源未在分镜中充分说明。",
        "voice": "一点六七米和零点一七米是文档给值；测量对象、方法、时点和来源尚待核实。",
    },
    {
        "title": "卫星与 GIS：让变化可复核",
        "tag": "核验方法 | 遥感不能替代登记边界",
        "kind": "method",
        "caption": "建议使用多期 Landsat/Sentinel 影像、统一季节和坐标，叠加官方拐点；2013 年不能使用 Sentinel-2 影像。",
        "voice": "用 Landsat 建立二零一三年基线，再比对后续影像，并用官方拐点坐标做 GIS 核验。",
    },
    {
        "title": "结论先待证，再制作正式成片",
        "tag": "待办：证照原件 · 拐点坐标 · 产量口径 · 实测深度",
        "kind": "conclusion",
        "caption": "当前材料适合做待核验的概念分镜。取得官方档案、生产统计、测量记录和遥感分析后，才能形成事实性结论。",
        "voice": "这只是待核验的研究框架，不能据此认定越界、超采或资源枯竭因果。",
    },
    {
        "title": "B3 · 浅水、盐壳与残深示意",
        "tag": "分镜 B3 | 储量归零为视觉示意，非实测结论",
        "kind": "b3_resource_depletion",
        "caption": "分镜构想：盐湖收缩为浅碟薄水，盐壳泛白，残深标注 0.17 米。真实储量与湖面状态需由实测/遥感资料确认。",
        "voice": "分镜 B3 以盐壳泛白、浅碟薄水和零点一七米残深收尾。储量归零是视觉示意，不是经测量确认的事实，仍需钻孔与储量资料核实。",
    },
]


def load_fonts() -> tuple[ImageFont.FreeTypeFont, ...]:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    font_path = next((path for path in candidates if path.exists()), None)
    if font_path is None:
        raise FileNotFoundError("A Chinese font is required; install Microsoft YaHei or SimHei.")
    return tuple(ImageFont.truetype(str(font_path), size) for size in (21, 25, 30, 39, 52, 76))


FONTS = load_fonts()
FONT_SMALL, FONT_BODY, FONT_MEDIUM, FONT_TITLE, FONT_HERO, FONT_NUMBER = FONTS


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, int, int], radius: int = 18, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        lines.append(current)
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, fill, max_width: int, line_gap: int = 8) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def make_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(40, WIDTH, 64):
        draw.line((x, 0, x, HEIGHT), fill=(65, 112, 117, 24), width=1)
    for y in range(20, HEIGHT, 64):
        draw.line((0, y, WIDTH, y), fill=(65, 112, 117, 24), width=1)
    draw.ellipse((850, -300, 1480, 330), fill=(38, 127, 122, 24))
    draw.ellipse((-330, 380, 330, 1040), fill=(41, 107, 150, 17))
    return image


BACKGROUND = make_background()


def draw_lake(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], progress: float, dry: bool = False) -> None:
    x0, y0, x1, y1 = box
    lake = [
        (x0 + 0.06 * (x1 - x0), y0 + 0.43 * (y1 - y0)),
        (x0 + 0.19 * (x1 - x0), y0 + 0.14 * (y1 - y0)),
        (x0 + 0.45 * (x1 - x0), y0 + 0.08 * (y1 - y0)),
        (x0 + 0.72 * (x1 - x0), y0 + 0.23 * (y1 - y0)),
        (x0 + 0.92 * (x1 - x0), y0 + 0.50 * (y1 - y0)),
        (x0 + 0.76 * (x1 - x0), y0 + 0.78 * (y1 - y0)),
        (x0 + 0.49 * (x1 - x0), y0 + 0.91 * (y1 - y0)),
        (x0 + 0.22 * (x1 - x0), y0 + 0.79 * (y1 - y0)),
    ]
    cx = sum(point[0] for point in lake) / len(lake)
    cy = sum(point[1] for point in lake) / len(lake)
    shrink = 1.0 - 0.30 * progress if dry else 1.0
    points = [(cx + (x - cx) * shrink, cy + (y - cy) * shrink) for x, y in lake]
    draw.polygon(points, fill=(45, 145, 151, 220), outline=(118, 216, 202, 255))
    draw.line(points + [points[0]], fill=(134, 218, 204, 220), width=3, joint="curve")
    for i in range(3):
        inset = 0.12 + 0.12 * i
        inner = [(cx + (x - cx) * (1 - inset), cy + (y - cy) * (1 - inset)) for x, y in points]
        draw.line(inner + [inner[0]], fill=(179, 227, 213, 75), width=1)
    if progress > 0.5 or dry:
        salt_color = (224, 213, 173, 130)
        for i in range(8):
            px = x0 + (i * 0.117 + 0.08) * (x1 - x0)
            py = y0 + ((i * 0.237) % 0.78 + 0.10) * (y1 - y0)
            draw.ellipse((px, py, px + 7, py + 4), fill=salt_color)


def card(draw: ImageDraw.ImageDraw, box, title: str, body: str, color=TEAL) -> None:
    rounded(draw, box, PANEL, outline=(52, 80, 85), width=1)
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x0 + 7, y1), radius=4, fill=color)
    draw.text((x0 + 23, y0 + 17), title, font=FONT_MEDIUM, fill=TEXT)
    draw_wrapped(draw, (x0 + 23, y0 + 63), body, FONT_BODY, MUTED, x1 - x0 - 42, 7)


def draw_opener(draw, progress: float) -> None:
    draw_lake(draw, (570, 175, 1160, 474), progress, dry=True)
    draw.text((76, 194), "2013", font=FONT_MEDIUM, fill=TEAL)
    draw.text((76, 248), "→", font=FONT_TITLE, fill=MUTED)
    draw.text((76, 315), "2026", font=FONT_MEDIUM, fill=AMBER)
    rounded(draw, (70, 402, 490, 470), PANEL_2, outline=(85, 121, 121))
    draw.text((94, 420), "演变概念图 · 非实测影像", font=FONT_BODY, fill=AMBER)


def draw_scope(draw, progress: float) -> None:
    draw_lake(draw, (620, 172, 1150, 468), progress * 0.5)
    sites = [(766, 295, "夏孜盖"), (994, 360, "新乌森")]
    for x, y, name in sites:
        draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=AMBER, outline=TEXT, width=2)
        draw.text((x + 20, y - 18), name, font=FONT_BODY, fill=TEXT)
    card(draw, (74, 207, 532, 312), "研究区域", "新疆玛纳斯盐湖\n坐标与范围以官方资料核定", TEAL)
    card(draw, (74, 335, 532, 440), "材料中的分场", "夏孜盖盐场 · 新乌森盐场\n地理位置为示意", BLUE)


def draw_timeline(draw, progress: float) -> None:
    x0, x1, y = 110, 1170, 314
    draw.line((x0, y, x1, y), fill=(87, 127, 132), width=5)
    events = [
        (2013, "证 1", "23 万 m³/年"),
        (2018, "证 2", "续期"),
        (2021, "证 3", "续期"),
        (2022, "证 4", "55 万吨/年"),
        (2026, "材料终点", "待核"),
    ]
    for i, (year, label, detail) in enumerate(events):
        x = x0 + i * (x1 - x0) / (len(events) - 1)
        active = progress >= i / (len(events) - 1) - 0.08
        color = AMBER if year == 2022 else TEAL
        draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=color if active else PANEL_2, outline=color, width=3)
        draw.text((x - 42, y + 30), str(year), font=FONT_MEDIUM, fill=TEXT if active else MUTED)
        draw.text((x - 47, y - 76), label, font=FONT_BODY, fill=color)
        draw.text((x - 69, y + 78), detail, font=FONT_SMALL, fill=MUTED)
    rounded(draw, (180, 466, 1100, 493), (111, 67, 51), outline=(235, 142, 92))
    draw.text((206, 468), "体积单位与质量单位不同：不得直接比较为“翻番”", font=FONT_SMALL, fill=(255, 214, 169))


def draw_rights(draw, progress: float) -> None:
    draw_lake(draw, (635, 173, 1162, 470), progress * 0.3)
    colors = [(BLUE, "宏达 · 夏孜盖"), (AMBER, "宏达 · 新乌森"), (GREEN, "宜新"), (PURPLE, "新雅泰")]
    for i, (color, label) in enumerate(colors):
        y = 193 + i * 68
        rounded(draw, (81, y, 482, y + 49), PANEL, outline=color, width=2)
        draw.ellipse((100, y + 15, 120, y + 35), fill=color)
        draw.text((140, y + 10), label, font=FONT_BODY, fill=TEXT)
    draw.text((688, 432), "权属块仅为示意，非登记坐标", font=FONT_SMALL, fill=AMBER)


def draw_production(draw, progress: float) -> None:
    x1, x2 = 120, 715
    rounded(draw, (82, 193, 597, 433), PANEL, outline=(75, 111, 115))
    rounded(draw, (670, 193, 1186, 433), PANEL, outline=(126, 86, 61))
    draw.text((117, 222), "文档列示 · 证载", font=FONT_BODY, fill=MUTED)
    draw.text((710, 222), "文档列示 · 后续规模", font=FONT_BODY, fill=MUTED)
    draw.text((x1, 278), "23 万", font=FONT_NUMBER, fill=TEAL)
    draw.text((x1 + 16, 374), "m³ / 年", font=FONT_BODY, fill=TEXT)
    draw.text((x2, 278), "55 万", font=FONT_NUMBER, fill=AMBER)
    draw.text((x2 + 16, 374), "吨 / 年", font=FONT_BODY, fill=TEXT)
    rounded(draw, (195, 456, 1084, 494), (102, 61, 46), outline=CORAL)
    draw.text((225, 462), "单位口径不同 · 需证照原件和密度/产品口径核算", font=FONT_SMALL, fill=(255, 220, 194))


def draw_depth(draw, progress: float) -> None:
    draw.text((92, 212), "文档给定值 · 测量口径待确认", font=FONT_BODY, fill=AMBER)
    bar_x, base_y, max_h = 350, 465, 220
    current = 1.67 + (0.17 - 1.67) * progress
    for x, value, label, color in [(445, 1.67, "2013", TEAL), (835, current, "演变示意", AMBER), (1044, 0.17, "2026", CORAL)]:
        h = max(18, int(max_h * value / 1.67))
        rounded(draw, (x, base_y - h, x + 116, base_y), color, radius=10)
        draw.text((x - 2, base_y + 15), label, font=FONT_BODY, fill=MUTED)
        draw.text((x - 5, base_y - h - 45), f"{value:.2f} m", font=FONT_MEDIUM, fill=TEXT)
    draw.line((bar_x, base_y, 1175, base_y), fill=(103, 139, 138), width=2)
    draw.text((571, 322), "−89.8%*", font=FONT_TITLE, fill=TEXT)
    draw.text((571, 372), "*仅按文档两端数值计算", font=FONT_SMALL, fill=MUTED)


def draw_method(draw, progress: float) -> None:
    labels = [
        ("Landsat", "2013 基线"),
        ("Sentinel", "后续可用年份"),
        ("官方坐标", "登记 polygon"),
        ("GIS 比对", "实测 vs 许可"),
    ]
    colors = [BLUE, TEAL, AMBER, GREEN]
    xs = [84, 377, 670, 963]
    for i, ((title, body), x, color) in enumerate(zip(labels, xs, colors)):
        y = 265
        rounded(draw, (x, y, x + 226, y + 136), PANEL, outline=color, width=2)
        draw.text((x + 22, y + 23), title, font=FONT_MEDIUM, fill=color)
        draw_wrapped(draw, (x + 22, y + 76), body, FONT_SMALL, TEXT, 190, 3)
        if i < len(xs) - 1:
            draw.line((x + 232, y + 68, x + 276, y + 68), fill=MUTED, width=3)
            draw.polygon([(x + 276, y + 62), (x + 286, y + 68), (x + 276, y + 74)], fill=MUTED)
    draw.text((121, 441), "2013 年没有 Sentinel-2 影像；卫星不能提供地下厚度或法定边界", font=FONT_SMALL, fill=AMBER)


def draw_conclusion(draw, progress: float) -> None:
    items = [
        ("01", "采矿许可证原件与变更关系", BLUE),
        ("02", "四矿拐点坐标与 GIS 边界", TEAL),
        ("03", "同口径产量、单位与统计时点", AMBER),
        ("04", "深度测量定义、方法及原始记录", CORAL),
    ]
    for i, (number, text, color) in enumerate(items):
        y = 181 + i * 70
        if progress * len(items) >= i * 0.82:
            rounded(draw, (112, y, 1155, y + 52), PANEL, outline=(50, 83, 90))
            draw.text((141, y + 9), number, font=FONT_MEDIUM, fill=color)
            draw.text((211, y + 11), text, font=FONT_BODY, fill=TEXT)
    draw.text((117, 481), "只有完成上述核验，才能将概念演示升级为事实性结论。", font=FONT_BODY, fill=AMBER)


def draw_b3(draw, progress: float) -> None:
    draw_lake(draw, (644, 174, 1172, 444), progress, dry=True)

    rounded(draw, (91, 188, 535, 441), PANEL, outline=(89, 112, 102), width=1)
    draw.text((121, 213), "储量体积 · 示意动画", font=FONT_MEDIUM, fill=TEXT)
    draw.text((121, 257), "不代表实测储量", font=FONT_SMALL, fill=AMBER)
    base_y = 411
    full_height = 116
    current_height = max(4, int(full_height * (1.0 - progress)))
    rounded(draw, (177, base_y - full_height, 285, base_y), (170, 132, 63), radius=12)
    rounded(draw, (343, base_y - current_height, 451, base_y), CORAL if progress > 0.78 else AMBER, radius=12)
    draw.text((180, 418), "起始", font=FONT_SMALL, fill=MUTED)
    draw.text((332, 418), "演变示意", font=FONT_SMALL, fill=MUTED)
    draw.text((481, base_y - current_height - 18), "▸", font=FONT_MEDIUM, fill=AMBER)

    draw.text((695, 446), "湖体/盐壳为概念图，不是卫星影像", font=FONT_SMALL, fill=AMBER)
    draw.text((92, 474), "残深", font=FONT_BODY, fill=MUTED)
    ruler_left, ruler_right = 220, 1150
    draw.line((ruler_left, 481, ruler_right, 481), fill=(105, 142, 141), width=3)
    for tick in range(0, 5):
        x = ruler_left + tick * (ruler_right - ruler_left) / 4
        draw.line((x, 471, x, 491), fill=(105, 142, 141), width=2)
        draw.text((x - 18, 496), f"{tick * 0.5:.1f}", font=FONT_SMALL, fill=MUTED)
    marker = ruler_left + (1.67 + (0.17 - 1.67) * progress) / 2.0 * (ruler_right - ruler_left)
    draw.line((marker, 459, marker, 491), fill=CORAL, width=5)
    draw.text((marker - 47, 443), f"{1.67 + (0.17 - 1.67) * progress:.2f} m", font=FONT_SMALL, fill=TEXT)


DRAWERS = [
    draw_opener,
    draw_scope,
    draw_timeline,
    draw_rights,
    draw_production,
    draw_depth,
    draw_method,
    draw_conclusion,
    draw_b3,
]


def draw_frame(
    scene_index: int,
    progress: float,
    elapsed: float,
    duration: float,
    scenes: list[dict[str, str]] = SCENES,
    drawers=DRAWERS,
) -> np.ndarray:
    scene = scenes[scene_index]
    image = BACKGROUND.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((68, 44), "MANAS SALT LAKE  /  EVIDENCE-LED STORYBOARD", font=FONT_SMALL, fill=TEAL)
    draw.text((68, 79), scene["title"], font=FONT_TITLE, fill=TEXT)
    rounded(draw, (860, 51, 1208, 99), PANEL_2, outline=(68, 109, 113))
    draw.text((882, 64), f"{scene_index + 1:02d} / {len(scenes):02d}  ·  概念演示", font=FONT_SMALL, fill=AMBER)
    draw.text((70, 140), scene["tag"], font=FONT_SMALL, fill=MUTED)
    drawers[scene_index](draw, progress)

    rounded(draw, (54, 532, 1226, 672), (15, 32, 39), outline=(62, 91, 96), width=1)
    draw_wrapped(draw, (80, 556), scene["caption"], FONT_BODY, TEXT, 1115, 9)
    draw.text((70, 686), "资料性概念演示  ·  权属/产量/深度/因果待核验  ·  不代表法律或遥感认定", font=FONT_SMALL, fill=(184, 191, 174))
    draw.rectangle((0, 712, int(WIDTH * (scene_index + progress) / len(scenes)), HEIGHT), fill=TEAL)
    return np.asarray(image)


def synthesize_voice(temp_dir: Path, scenes: list[dict[str, str]] = SCENES) -> list[Path]:
    segment_data = [{"id": i + 1, "text": scene["voice"]} for i, scene in enumerate(scenes)]
    json_path = temp_dir / "voice_segments.json"
    json_path.write_text(json.dumps(segment_data, ensure_ascii=True), encoding="ascii")
    audio_dir = temp_dir / "voice"
    command = [
        "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(VOICE_SCRIPT), str(json_path), str(audio_dir),
    ]
    subprocess.run(command, check=True)
    return [audio_dir / f"scene_{i + 1:02d}.wav" for i in range(len(scenes))]


def read_audio(path: Path) -> tuple[wave._wave_params, bytes, float]:
    with wave.open(str(path), "rb") as audio:
        params = audio.getparams()
        frames = audio.readframes(audio.getnframes())
    duration = len(frames) / (params.framerate * params.nchannels * params.sampwidth)
    return params, frames, duration


def write_combined_audio(paths: list[Path], destination: Path) -> list[float]:
    combined = bytearray()
    durations = []
    params_ref = None
    scene_lengths = []
    for path in paths:
        params, frames, duration = read_audio(path)
        if params_ref is None:
            params_ref = params
        elif (params.nchannels, params.sampwidth, params.framerate) != (params_ref.nchannels, params_ref.sampwidth, params_ref.framerate):
            raise ValueError("Speech segments have inconsistent audio formats")
        combined.extend(frames)
        silence_frames = int(params.framerate * PAD_SECONDS)
        combined.extend(b"\x00" * silence_frames * params.nchannels * params.sampwidth)
        durations.append(duration + PAD_SECONDS)
        scene_lengths.append(duration)

    with wave.open(str(destination), "wb") as output:
        output.setparams(params_ref)
        output.writeframes(bytes(combined))
    return durations


def write_subtitles(scene_durations: list[float], destination: Path, scenes: list[dict[str, str]] = SCENES) -> None:
    def stamp(seconds: float) -> str:
        millis = int(round(seconds * 1000))
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    lines = []
    cursor = 0.0
    for index, (scene, duration) in enumerate(zip(scenes, scene_durations), 1):
        lines.extend([str(index), f"{stamp(cursor)} --> {stamp(cursor + duration)}", scene["voice"], ""])
        cursor += duration
    destination.write_text("\n".join(lines), encoding="utf-8-sig")


def render(
    scenes: list[dict[str, str]] = SCENES,
    drawers=DRAWERS,
    output_stem: str = "manas_salt_lake_evolution",
) -> tuple[Path, Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUTPUT_DIR / f"{output_stem}.mp4"
    subtitle_path = OUTPUT_DIR / f"{output_stem}.srt"
    voice_path = OUTPUT_DIR / f"{output_stem}_voiceover.wav"
    silent_path = OUTPUT_DIR / f"{output_stem}_silent.mp4"
    with tempfile.TemporaryDirectory(prefix="manas_video_") as temporary:
        temporary_dir = Path(temporary)
        voice_segments = synthesize_voice(temporary_dir, scenes)
        durations = write_combined_audio(voice_segments, voice_path)
        write_subtitles(durations, subtitle_path, scenes)

        with imageio.get_writer(
            str(silent_path),
            fps=FPS,
            codec="libx264",
            quality=7,
            macro_block_size=None,
            ffmpeg_params=["-movflags", "+faststart"],
        ) as writer:
            for scene_index, duration in enumerate(durations):
                frame_count = max(1, int(round(duration * FPS)))
                for frame_index in range(frame_count):
                    elapsed = frame_index / FPS
                    progress = min(1.0, elapsed / duration)
                    writer.append_data(draw_frame(scene_index, progress, elapsed, duration, scenes, drawers))

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([
            ffmpeg, "-y", "-i", str(silent_path), "-i", str(voice_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart", str(video_path),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        silent_path.unlink(missing_ok=True)
    return video_path, subtitle_path, voice_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render the Manas Salt Lake storyboard or the B3 depletion shot.")
    parser.add_argument("--scene", choices=("full", "b3"), default="full")
    arguments = parser.parse_args()
    if arguments.scene == "b3":
        outputs = render([SCENES[-1]], [DRAWERS[-1]], "B3_resource_depletion")
    else:
        outputs = render()
    for path in outputs:
        print(path)