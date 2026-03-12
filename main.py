from config.model_config import TRANSLATION_MODEL_PATH
from pipelines.translation_pipeline import TranslationPipeline


def main():

    url = input("请输入YouTube视频链接：")

    pipeline = TranslationPipeline(TRANSLATION_MODEL_PATH)

    pipeline.run(url)


if __name__ == "__main__":
    main()