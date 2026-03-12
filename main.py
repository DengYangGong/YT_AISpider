from core.agent import AISpiderAgent

agent = AISpiderAgent(
    model_path="./models/HY-MT1.5-1.8B",
    knowledge_files=[
        "./subtitle_translator/knowledge/other_terms.txt",
        "./subtitle_translator/knowledge/robotics.txt"
    ]
)

text = "AT AT is a walking vehicle"

result = agent.translate_sentence(text)

print(result)