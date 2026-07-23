from dreamina_video import DreaminaVideoClient
from config import DREAMINA_API_KEY, DREAMINA_BASE_URL


def generate_video_example():
    client = DreaminaVideoClient(
        api_key=DREAMINA_API_KEY,
        base_url=DREAMINA_BASE_URL,
    )

    task_id = client.text_to_video(
        prompt="一条小河流淌在森林中,鸟儿在树枝上歌唱",
        model="v30",
        resolution="720p",
        ratio="16:9",
        duration=5,
    )
    print(f"Task submitted: {task_id}")

    result = client.wait_result(task_id)
    video_url = result["data"]["data"]["content"]["video_url"]
    print(f"Video URL: {video_url}")
    return video_url


def image_to_video_example():
    client = DreaminaVideoClient(
        api_key=DREAMINA_API_KEY,
        base_url=DREAMINA_BASE_URL,
    )

    task_id = client.image_to_video(
        prompt="女孩抱着狐狸,女孩睁开眼,温柔地看向镜头",
        images=["https://example.com/first_frame.png"],
        model="v30",
        resolution="720p",
        ratio="16:9",
        duration=5,
    )
    print(f"Task submitted: {task_id}")

    result = client.wait_result(task_id)
    video_url = result["data"]["data"]["content"]["video_url"]
    print(f"Video URL: {video_url}")
    return video_url


def camera_video_example():
    client = DreaminaVideoClient(
        api_key=DREAMINA_API_KEY,
        base_url=DREAMINA_BASE_URL,
    )

    task_id = client.camera_video(
        prompt="一辆跑车停在赛道上,阳光照在车身上",
        images=["https://example.com/car.png"],
        template_id="dynamic_orbit",
        camera_strength="strong",
        model="v30",
        resolution="720p",
        ratio="16:9",
        duration=5,
    )
    print(f"Task submitted: {task_id}")

    result = client.wait_result(task_id)
    video_url = result["data"]["data"]["content"]["video_url"]
    print(f"Video URL: {video_url}")
    return video_url


if __name__ == "__main__":
    generate_video_example()
