import random
from pathlib import Path


class TransitionPromptGenerator:
    def __init__(self):
        self.base_styles = {
            "nature": {
                "keywords": ["森林", "河流", "山川", "湖泊", "草原", "花海", "日落", "星空", "云海", "瀑布"],
                "transitions": [
                    "镜头缓慢推近,画面柔和过渡,一镜到底,自然光线变化,无大幅移动",
                    "平滑的镜头平移,画面流畅衔接,一镜到底,保持画面稳定,光线渐变",
                    "缓慢的镜头环绕,画面自然过渡,一镜到底,无跳跃感,色调和谐",
                    "柔和的镜头运动,画面平滑过渡,一镜到底,保持视觉连贯,光影变化",
                ],
            },
            "city": {
                "keywords": ["城市", "街道", "建筑", "夜景", "霓虹", "车流", "人群", "商场", "地铁", "天际线"],
                "transitions": [
                    "镜头缓慢推进,城市景观平滑过渡,一镜到底,灯光渐变,无大幅移动",
                    "平滑的镜头平移,街景流畅衔接,一镜到底,保持画面稳定,光影流动",
                    "缓慢的镜头环绕,建筑轮廓自然过渡,一镜到底,无跳跃感,色调统一",
                    "柔和的镜头运动,城市天际线平滑过渡,一镜到底,保持视觉连贯,光线变化",
                ],
            },
            "portrait": {
                "keywords": ["人物", "肖像", "表情", "动作", "姿态", "眼神", "微笑", "沉思", "回眸", "侧脸"],
                "transitions": [
                    "镜头缓慢推近,人物表情平滑过渡,一镜到底,情感自然流露,无大幅移动",
                    "平滑的镜头移动,人物姿态流畅衔接,一镜到底,保持画面稳定,情绪渐变",
                    "缓慢的镜头环绕,人物轮廓自然过渡,一镜到底,无跳跃感,神态变化",
                    "柔和的镜头运动,人物神态平滑过渡,一镜到底,保持视觉连贯,情感递进",
                ],
            },
            "abstract": {
                "keywords": ["抽象", "艺术", "色彩", "光影", "纹理", "几何", "流动", "渐变", "梦幻", "超现实"],
                "transitions": [
                    "镜头缓慢移动,色彩平滑过渡,一镜到底,光影流动,无大幅移动",
                    "平滑的镜头运动,纹理流畅衔接,一镜到底,保持画面稳定,渐变自然",
                    "缓慢的镜头环绕,几何形态自然过渡,一镜到底,无跳跃感,色调和谐",
                    "柔和的镜头推移,抽象元素平滑过渡,一镜到底,保持视觉连贯,梦幻效果",
                ],
            },
            "cinematic": {
                "keywords": ["电影", "戏剧", "故事", "情节", "氛围", "悬疑", "浪漫", "史诗", "动作", "冒险"],
                "transitions": [
                    "电影感镜头推近,画面戏剧性过渡,一镜到底,氛围营造,无大幅移动",
                    "平滑的镜头平移,场景流畅衔接,一镜到底,保持画面稳定,情绪递进",
                    "缓慢的镜头环绕,叙事自然过渡,一镜到底,无跳跃感,张力变化",
                    "柔和的镜头运动,情节平滑过渡,一镜到底,保持视觉连贯,情感升华",
                ],
            },
        }

        self.mood_modifiers = {
            "calm": ["宁静", "平和", "安详", "舒缓", "静谧"],
            "dynamic": ["动感", "活力", "激情", "奔放", "热烈"],
            "mysterious": ["神秘", "朦胧", "深邃", "幽暗", "玄妙"],
            "romantic": ["浪漫", "温馨", "柔美", "甜蜜", "梦幻"],
            "epic": ["史诗", "壮观", "磅礴", "恢弘", "震撼"],
        }

        self.time_of_day = {
            "dawn": "晨光熹微,光线柔和",
            "morning": "阳光明媚,光线充足",
            "noon": "阳光直射,光影分明",
            "afternoon": "斜阳西照,光线温暖",
            "dusk": "暮色降临,光线渐暗",
            "night": "夜幕笼罩,灯光闪烁",
            "midnight": "深夜寂静,月光如水",
        }

    def detect_scene_type(self, filename: str) -> str:
        filename_lower = filename.lower()
        for scene_type, data in self.base_styles.items():
            for keyword in data["keywords"]:
                if keyword in filename_lower:
                    return scene_type
        return "cinematic"

    def detect_mood(self, filename: str) -> str:
        filename_lower = filename.lower()
        mood_keywords = {
            "calm": ["安静", "平静", "宁静", "平和", "静"],
            "dynamic": ["动态", "运动", "活力", "动"],
            "mysterious": ["神秘", "暗", "深", "幽"],
            "romantic": ["浪漫", "爱", "甜蜜", "温"],
            "epic": ["史诗", "壮观", "大", "宏"],
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
        mood: str = None,
        custom_style: str = None,
    ) -> str:
        if not scene_type:
            scene_type = self.detect_scene_type(from_image)
            if scene_type == "cinematic":
                scene_type = self.detect_scene_type(to_image)

        if not mood:
            mood = self.detect_mood(from_image)

        base_transitions = self.base_styles.get(scene_type, self.base_styles["cinematic"])["transitions"]
        base_transition = random.choice(base_transitions)

        mood_keywords = self.mood_modifiers.get(mood, self.mood_modifiers["calm"])
        mood_keyword = random.choice(mood_keywords)

        from_name = Path(from_image).stem
        to_name = Path(to_image).stem

        prompt = f"从{from_name}到{to_name},{base_transition},{mood_keyword}氛围"

        if custom_style:
            prompt += f",{custom_style}"

        return prompt

    def generate_prompts_batch(
        self,
        image_pairs: list[tuple[str, str]],
        scene_type: str = None,
        mood: str = None,
    ) -> list[str]:
        prompts = []
        for from_image, to_image in image_pairs:
            prompt = self.generate_prompt(from_image, to_image, scene_type, mood)
            prompts.append(prompt)
        return prompts

    def get_style_options(self) -> dict:
        return {
            "scene_types": list(self.base_styles.keys()),
            "moods": list(self.mood_modifiers.keys()),
        }


def main():
    generator = TransitionPromptGenerator()

    test_pairs = [
        ("forest_sunrise.jpg", "mountain_lake.jpg"),
        ("city_night.jpg", "street_neon.jpg"),
        ("portrait_smile.jpg", "portrait_thoughtful.jpg"),
        ("abstract_color.jpg", "abstract_flow.jpg"),
    ]

    print("Prompt Generation Examples:")
    print("=" * 60)

    for from_img, to_img in test_pairs:
        prompt = generator.generate_prompt(from_img, to_img)
        print(f"\n{from_img} -> {to_img}")
        print(f"Prompt: {prompt}")

    print("\n" + "=" * 60)
    print("Available styles:")
    styles = generator.get_style_options()
    print(f"  Scene types: {styles['scene_types']}")
    print(f"  Moods: {styles['moods']}")


if __name__ == "__main__":
    main()
