import random
from pathlib import Path


class HistoricalPromptGenerator:
    def __init__(self):
        self.figure_types = {
            "emperor": {
                "keywords": ["皇帝", "帝王", "君主", "天子", "皇上", "陛下", "汉武帝", "唐太宗", "康熙", "乾隆"],
                "styles": [
                    "宫殿场景,龙袍加身,威严庄重,历史厚重感",
                    "朝堂之上,文武百官,气势恢宏,帝王风范",
                    "御花园中,悠闲自得,皇家气派,岁月静好",
                    "批阅奏章,运筹帷幄,治国平天下,帝王智慧",
                ],
                "transitions": [
                    "镜头缓慢推近,帝王威严逐渐显现,一镜到底,历史厚重感,无大幅移动",
                    "平滑的镜头环绕,宫殿场景自然过渡,一镜到底,保持画面稳定,气势恢宏",
                    "缓慢的镜头平移,朝堂画面流畅衔接,一镜到底,无跳跃感,庄严肃穆",
                    "柔和的镜头运动,帝王形象平滑过渡,一镜到底,保持视觉连贯,威严渐显",
                ],
            },
            "poet": {
                "keywords": ["诗人", "词人", "文人", "李白", "杜甫", "苏轼", "辛弃疾", "李清照", "王维"],
                "styles": [
                    "书房场景,笔墨纸砚,文人雅趣,诗意盎然",
                    "山水之间,吟诗作对,潇洒飘逸,文人风骨",
                    "月下独酌,诗兴大发,意境深远,文人情怀",
                    "庭院深深,抚琴吟诗,高雅脱俗,文人气质",
                ],
                "transitions": [
                    "镜头缓慢推近,文人气质逐渐流露,一镜到底,诗意盎然,无大幅移动",
                    "平滑的镜头环绕,书房场景自然过渡,一镜到底,保持画面稳定,文人雅趣",
                    "缓慢的镜头平移,山水画面流畅衔接,一镜到底,无跳跃感,意境深远",
                    "柔和的镜头运动,诗人形象平滑过渡,一镜到底,保持视觉连贯,潇洒飘逸",
                ],
            },
            "warrior": {
                "keywords": ["将军", "武士", "英雄", "岳飞", "关羽", "张飞", "赵云", "吕布", "项羽"],
                "styles": [
                    "战场场景,披甲执锐,英姿飒爽,英雄气概",
                    "军营之中,运筹帷幄,将帅风范,军事智慧",
                    "单骑救主,勇猛无敌,忠义千秋,英雄本色",
                    "凯旋归来,威风凛凛,战功赫赫,英雄荣光",
                ],
                "transitions": [
                    "镜头缓慢推近,英雄气概逐渐显现,一镜到底,气势磅礴,无大幅移动",
                    "平滑的镜头环绕,战场场景自然过渡,一镜到底,保持画面稳定,英姿飒爽",
                    "缓慢的镜头平移,军营画面流畅衔接,一镜到底,无跳跃感,将帅风范",
                    "柔和的镜头运动,武士形象平滑过渡,一镜到底,保持视觉连贯,勇猛无敌",
                ],
            },
            "scholar": {
                "keywords": ["学者", "思想家", "孔子", "孟子", "老子", "庄子", "韩非子", "墨子"],
                "styles": [
                    "学堂场景,传道授业,思想深邃,学者风范",
                    "辩论之中,思想碰撞,智慧光芒,学术氛围",
                    "著书立说,潜心研究,学识渊博,思想传承",
                    "游历四方,观察民情,心系天下,学者情怀",
                ],
                "transitions": [
                    "镜头缓慢推近,学者风范逐渐流露,一镜到底,思想深邃,无大幅移动",
                    "平滑的镜头环绕,学堂场景自然过渡,一镜到底,保持画面稳定,传道授业",
                    "缓慢的镜头平移,辩论画面流畅衔接,一镜到底,无跳跃感,思想碰撞",
                    "柔和的镜头运动,学者形象平滑过渡,一镜到底,保持视觉连贯,学识渊博",
                ],
            },
            "artist": {
                "keywords": ["画家", "书法家", "艺术家", "王羲之", "顾恺之", "吴道子", "齐白石", "张大千"],
                "styles": [
                    "画室场景,挥毫泼墨,艺术创作,匠心独运",
                    "山水之间,写生创作,灵感迸发,艺术境界",
                    "笔会雅集,切磋技艺,艺术交流,文人雅趣",
                    "作品展示,艺术鉴赏,审美体验,艺术传承",
                ],
                "transitions": [
                    "镜头缓慢推近,艺术气息逐渐弥漫,一镜到底,匠心独运,无大幅移动",
                    "平滑的镜头环绕,画室场景自然过渡,一镜到底,保持画面稳定,挥毫泼墨",
                    "缓慢的镜头平移,山水画面流畅衔接,一镜到底,无跳跃感,灵感迸发",
                    "柔和的镜头运动,艺术家形象平滑过渡,一镜到底,保持视觉连贯,艺术创作",
                ],
            },
            "beauty": {
                "keywords": ["美人", "佳人", "美女", "西施", "王昭君", "貂蝉", "杨玉环", "赵飞燕"],
                "styles": [
                    "宫廷场景,华丽服饰,倾国倾城,绝代风华",
                    "花园之中,翩翩起舞,优雅动人,美人如画",
                    "梳妆镜前,精心打扮,美丽动人,绝世容颜",
                    "月下独舞,舞姿曼妙,如梦如幻,美人风韵",
                ],
                "transitions": [
                    "镜头缓慢推近,美人风采逐渐展现,一镜到底,倾国倾城,无大幅移动",
                    "平滑的镜头环绕,宫廷场景自然过渡,一镜到底,保持画面稳定,华丽服饰",
                    "缓慢的镜头平移,花园画面流畅衔接,一镜到底,无跳跃感,翩翩起舞",
                    "柔和的镜头运动,美人形象平滑过渡,一镜到底,保持视觉连贯,优雅动人",
                ],
            },
        }

        self.era_styles = {
            "ancient": {
                "keywords": ["古代", "先秦", "秦汉", "三国", "两晋", "南北朝"],
                "modifiers": ["古朴典雅", "历史厚重", "古风古韵", "古典之美"],
            },
            "medieval": {
                "keywords": ["唐代", "宋代", "元代", "明清", "中世纪"],
                "modifiers": ["盛世风华", "文化繁荣", "精致典雅", "时代特色"],
            },
            "modern": {
                "keywords": ["近代", "民国", "现代", "当代"],
                "modifiers": ["时代变迁", "新旧交替", "现代气息", "历史转折"],
            },
        }

        self.mood_modifiers = {
            "majestic": ["威严", "庄重", "气势恢宏", "王者风范"],
            "elegant": ["优雅", "脱俗", "高雅", "文人气质"],
            "heroic": ["英勇", "豪迈", "气概非凡", "英雄本色"],
            "wise": ["智慧", "深邃", "思想深邃", "学者风范"],
            "artistic": ["艺术", "匠心", "审美", "艺术气息"],
            "beautiful": ["美丽", "动人", "倾国倾城", "绝代风华"],
        }

    def detect_figure_type(self, filename: str) -> str:
        filename_lower = filename.lower()
        for figure_type, data in self.figure_types.items():
            for keyword in data["keywords"]:
                if keyword in filename_lower:
                    return figure_type
        return "scholar"

    def detect_era(self, filename: str) -> str:
        filename_lower = filename.lower()
        for era, data in self.era_styles.items():
            for keyword in data["keywords"]:
                if keyword in filename_lower:
                    return era
        return "medieval"

    def detect_mood(self, filename: str) -> str:
        filename_lower = filename.lower()
        mood_keywords = {
            "majestic": ["威严", "庄重", "气势", "王"],
            "elegant": ["优雅", "文", "雅", "诗"],
            "heroic": ["英雄", "勇", "武", "将"],
            "wise": ["智慧", "思想", "学", "哲"],
            "artistic": ["艺术", "画", "书", "美"],
            "beautiful": ["美丽", "美", "佳人", "艳"],
        }
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return mood
        return random.choice(list(self.mood_modifiers.keys()))

    def generate_prompt(
        self,
        from_image: str,
        to_image: str,
        figure_type: str = None,
        era: str = None,
        mood: str = None,
        custom_style: str = None,
    ) -> str:
        if not figure_type:
            figure_type = self.detect_figure_type(from_image)
            if figure_type == "scholar":
                figure_type = self.detect_figure_type(to_image)

        if not era:
            era = self.detect_era(from_image)

        if not mood:
            mood = self.detect_mood(from_image)

        base_styles = self.figure_types.get(figure_type, self.figure_types["scholar"])["styles"]
        base_style = random.choice(base_styles)

        transitions = self.figure_types.get(figure_type, self.figure_types["scholar"])["transitions"]
        transition = random.choice(transitions)

        era_modifiers = self.era_styles.get(era, self.era_styles["medieval"])["modifiers"]
        era_modifier = random.choice(era_modifiers)

        mood_keywords = self.mood_modifiers.get(mood, self.mood_modifiers["wise"])
        mood_keyword = random.choice(mood_keywords)

        from_name = Path(from_image).stem
        to_name = Path(to_image).stem

        prompt = f"从{from_name}到{to_name},{base_style},{transition},{era_modifier},{mood_keyword}氛围"

        if custom_style:
            prompt += f",{custom_style}"

        return prompt

    def generate_prompts_batch(
        self,
        image_pairs: list[tuple[str, str]],
        figure_type: str = None,
        era: str = None,
        mood: str = None,
    ) -> list[str]:
        prompts = []
        for from_image, to_image in image_pairs:
            prompt = self.generate_prompt(from_image, to_image, figure_type, era, mood)
            prompts.append(prompt)
        return prompts

    def get_style_options(self) -> dict:
        return {
            "figure_types": list(self.figure_types.keys()),
            "eras": list(self.era_styles.keys()),
            "moods": list(self.mood_modifiers.keys()),
        }


def main():
    generator = HistoricalPromptGenerator()

    test_pairs = [
        ("emperor_tangtaizong.jpg", "poet_liubai.jpg"),
        ("warrior_yuefei.jpg", "scholar_kongzi.jpg"),
        ("artist_wangxizhi.jpg", "beauty_xishi.jpg"),
    ]

    print("Historical Figure Prompt Generation Examples:")
    print("=" * 60)

    for from_img, to_img in test_pairs:
        prompt = generator.generate_prompt(from_img, to_img)
        print(f"\n{from_img} -> {to_img}")
        print(f"Prompt: {prompt}")

    print("\n" + "=" * 60)
    print("Available styles:")
    styles = generator.get_style_options()
    print(f"  Figure types: {styles['figure_types']}")
    print(f"  Eras: {styles['eras']}")
    print(f"  Moods: {styles['moods']}")


if __name__ == "__main__":
    main()
