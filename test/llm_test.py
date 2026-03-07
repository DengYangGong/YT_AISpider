from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = "./models/HY-MT1.5-1.8B"

tokenizer = AutoTokenizer.from_pretrained(model_path)

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype=torch.float16,
).cuda()

model.eval()

# 保存对话历史
messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

print("开始对话（输入 exit 退出）")

while True:
    user_input = input("\n你: ")

    if user_input.lower() == "exit":
        break

    # 追加用户消息
    messages.append({"role": "user", "content": user_input})

    # 构造模型输入
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).cuda()

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

    # 只取新生成的内容
    generated = outputs[0][inputs.shape[-1]:]
    reply = tokenizer.decode(generated, skip_special_tokens=True)

    print("\n助手:", reply)

    # 把助手回复加入历史
    messages.append({"role": "assistant", "content": reply})