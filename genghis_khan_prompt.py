import random
from pathlib import Path


class GenghisKhanPromptGenerator:
    def __init__(self):
        self.scenes = {
            "steppe": {
                "keywords": ["草原", "蒙古", "大漠", "戈壁", "牧场", "蓝天", "白云", "蒙古包"],
                "styles": [
                    "辽阔草原,天高云淡,蒙古铁骑,驰骋疆场",
                    "大漠孤烟,长河落日,英雄远眺,壮志凌云",
                    "蒙古包前,篝火晚会,草原儿女,豪情万丈",
                    "蓝天白云,绿草如茵,万马奔腾,气势磅礴",
                ],
                "transitions": [
                    "镜头缓慢推近,草原辽阔逐渐展现,一镜到底,天高云淡,无大幅移动",
                    "平滑的镜头环绕,大漠场景自然过渡,一镜到底,保持画面稳定,壮志凌云",
                    "缓慢的镜头平移,蒙古包画面流畅衔接,一镜到底,无跳跃感,豪情万丈",
                    "柔和的镜头运动,草原风光平滑过渡,一镜到底,保持视觉连贯,气势磅礴",
                ],
            },
            "battle": {
                "keywords": ["战场", "战争", "征战", "征服", "军队", "骑兵", "弓箭", "刀剑"],
                "styles": [
                    "金戈铁马,气吞万里,英雄挥剑,征服四方",
                    "千军万马,势如破竹,铁蹄踏破,山河变色",
                    "弯弓射雕,百步穿杨,武艺高强,英雄本色",
                    "旌旗蔽日,战鼓雷鸣,士气如虹,所向披靡",
                ],
                "transitions": [
                    "镜头缓慢推近,战场气势逐渐显现,一镜到底,金戈铁马,无大幅移动",
                    "平滑的镜头环绕,千军万马自然过渡,一镜到底,保持画面稳定,势如破竹",
                    "缓慢的镜头平移,战争场面流畅衔接,一镜到底,无跳跃感,气吞万里",
                    "柔和的镜头运动,英雄形象平滑过渡,一镜到底,保持视觉连贯,征服四方",
                ],
            },
            "horseback": {
                "keywords": ["骑马", "战马", "驰骋", "奔腾", "马背", "骑射", "骏马"],
                "styles": [
                    "骏马奔驰,风驰电掣,英雄骑射,英姿飒爽",
                    "马背民族,纵横驰骋,天下无敌,英雄气概",
                    "万马奔腾,尘土飞扬,铁骑突出,势不可挡",
                    "单骑突阵,勇往直前,一骑当千,英雄本色",
                ],
                "transitions": [
                    "镜头缓慢推近,骏马奔驰逐渐展现,一镜到底,风驰电掣,无大幅移动",
                    "平滑的镜头环绕,马背英雄自然过渡,一镜到底,保持画面稳定,英姿飒爽",
                    "缓慢的镜头平移,驰骋场面流畅衔接,一镜到底,无跳跃感,纵横驰骋",
                    "柔和的镜头运动,骑射形象平滑过渡,一镜到底,保持视觉连贯,势不可挡",
                ],
            },
            "strategy": {
                "keywords": ["谋略", "战略", "地图", "营帐", "会议", "决策", "智慧"],
                "styles": [
                    "运筹帷幄,决胜千里,智慧超群,帝王谋略",
                    "沙盘推演,排兵布阵,战略眼光,雄才大略",
                    "营帐之中,指点江山,胸怀天下,王者风范",
                    "地图前沉思,深谋远虑,统帅之才,帝王智慧",
                ],
                "transitions": [
                    "镜头缓慢推近,谋略智慧逐渐流露,一镜到底,运筹帷幄,无大幅移动",
                    "平滑的镜头环绕,营帐场景自然过渡,一镜到底,保持画面稳定,决胜千里",
                    "缓慢的镜头平移,战略画面流畅衔接,一镜到底,无跳跃感,雄才大略",
                    "柔和的镜头运动,帝王形象平滑过渡,一镜到底,保持视觉连贯,王者风范",
                ],
            },
            "culture": {
                "keywords": ["文化", "传统", "节日", "庆典", "音乐", "舞蹈", "服饰"],
                "styles": [
                    "蒙古长调,悠扬动听,草原文化,源远流长",
                    "那达慕大会,热闹非凡,草原盛会,欢声笑语",
                    "蒙古服饰,华丽精美,民族特色,文化传承",
                    "马头琴声,如泣如诉,草原情怀,悠远绵长",
                ],
                "transitions": [
                    "镜头缓慢推近,文化底蕴逐渐展现,一镜到底,源远流长,无大幅移动",
                    "平滑的镜头环绕,节日场景自然过渡,一镜到底,保持画面稳定,热闹非凡",
                    "缓慢的镜头平移,文化画面流畅衔接,一镜到底,无跳跃感,悠扬动听",
                    "柔和的镜头运动,传统形象平滑过渡,一镜到底,保持视觉连贯,文化传承",
                ],
            },
            "portrait": {
                "keywords": ["肖像", "画像", "雕像", "纪念碑", "头像", "形象"],
                "styles": [
                    "威严肖像,目光如炬,帝王气度,天下归心",
                    "骑马雕像,英姿飒爽,英雄形象,永垂不朽",
                    "历史画像,神态威严,一代天骄,成吉思汗",
                    "纪念碑前,缅怀英雄,丰功伟绩,流芳百世",
                ],
                "transitions": [
                    "镜头缓慢推近,帝王威严逐渐显现,一镜到底,目光如炬,无大幅移动",
                    "平滑的镜头环绕,肖像场景自然过渡,一镜到底,保持画面稳定,帝王气度",
                    "缓慢的镜头平移,雕像画面流畅衔接,一镜到底,无跳跃感,英姿飒爽",
                    "柔和的镜头运动,英雄形象平滑过渡,一镜到底,保持视觉连贯,天下归心",
                ],
            },
        }

        self.mood_modifiers = {
            "majestic": ["威严", "庄重", "气势恢宏", "王者风范"],
            "heroic": ["英勇", "豪迈", "气概非凡", "英雄本色"],
            "wise": ["智慧", "深邃", "谋略过人", "帝王智慧"],
            "powerful": ["强大", "无敌", "势不可挡", "天下归心"],
            "cultural": ["文化", "传统", "民族特色", "源远流长"],
            "epic": ["史诗", "壮阔", "波澜壮阔", "历史厚重"],
        }

        self.era_styles = {
            "rise": {
                "keywords": ["崛起", "创业", "统一", "蒙古"],
                "modifiers": ["崛起之路", "统一草原", "创业维艰", "雄心壮志"],
            },
            "conquest": {
                "keywords": ["征服", "扩张", "战争", "西征"],
                "modifiers": ["征服世界", "扩张版图", "铁蹄西征", "所向披靡"],
            },
            "peak": {
                "keywords": ["鼎盛", "帝国", "巅峰", "盛世"],
                "modifiers": ["帝国鼎盛", "版图辽阔", "盛世辉煌", "天下一统"],
            },
            "legacy": {
                "keywords": ["遗产", "传承", "影响", "历史"],
                "modifiers": ["历史遗产", "文化传承", "深远影响", "流芳百世"],
            },
        }

    def detect_scene_type(self, filename: str) -> str:
        filename_lower = filename.lower()
        for scene_type, data in self.scenes.items():
            for keyword in data["keywords"]:
                if keyword in filename_lower:
                    return scene_type
        return "portrait"

    def detect_era(self, filename: str) -> str:
        filename_lower = filename.lower()
        for era, data in self.era_styles.items():
            for keyword in data["keywords"]:
                if keyword in filename_lower:
                    return era
        return "conquest"

    def detect_mood(self, filename: str) -> str:
        filename_lower = filename.lower()
        mood_keywords = {
            "majestic": ["威严", "庄重", "气势", "王"],
            "heroic": ["英雄", "勇", "武", "将"],
            "wise": ["智慧", "谋略", "战略", "智"],
            "powerful": ["强大", "无敌", "征服", "强"],
            "cultural": ["文化", "传统", "民族", "文"],
            "epic": ["史诗", "壮阔", "历史", "史"],
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
        scene_type: str = None,
        era: str = None,
        mood: str = None,
        custom_style: str = None,
    ) -> str:
        if not scene_type:
            scene_type = self.detect_scene_type(from_image)
            if scene_type == "portrait":
                scene_type = self.detect_scene_type(to_image)

        if not era:
            era = self.detect_era(from_image)

        if not mood:
            mood = self.detect_mood(from_image)

        base_styles = self.scenes.get(scene_type, self.scenes["portrait"])["styles"]
        base_style = random.choice(base_styles)

        transitions = self.scenes.get(scene_type, self.scenes["portrait"])["transitions"]
        transition = random.choice(transitions)

        era_modifiers = self.era_styles.get(era, self.era_styles["conquest"])["modifiers"]
        era_modifier = random.choice(era_modifiers)

        mood_keywords = self.mood_modifiers.get(mood, self.mood_modifiers["majestic"])
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
        scene_type: str = None,
        era: str = None,
        mood: str = None,
    ) -> list[str]:
        prompts = []
        for from_image, to_image in image_pairs:
            prompt = self.generate_prompt(from_image, to_image, scene_type, era, mood)
            prompts.append(prompt)
        return prompts

    def get_style_options(self) -> dict:
        return {
            "scene_types": list(self.scenes.keys()),
            "eras": list(self.era_styles.keys()),
            "moods": list(self.mood_modifiers.keys()),
        }


def main():
    generator = GenghisKhanPromptGenerator()

    test_pairs = [
        ("成吉思汗_草原.jpg", "成吉思汗_骑马.jpg"),
        ("成吉思汗_战场.jpg", "成吉思汗_谋略.jpg"),
        ("成吉思汗_肖像.jpg", "成吉思汗_文化.jpg"),
    ]

    print("Genghis Khan Prompt Generation Examples:")
    print("=" * 60)

    for from_img, to_img in test_pairs:
        prompt = generator.generate_prompt(from_img, to_img)
        print(f"\n{from_img} -> {to_img}")
        print(f"Prompt: {prompt}")

    print("\n" + "=" * 60)
    print("Available styles:")
    styles = generator.get_style_options()
    print(f"  Scene types: {styles['scene_types']}")
    print(f"  Eras: {styles['eras']}")
    print(f"  Moods: {styles['moods']}")


if __name__ == "__main__":
    main()
