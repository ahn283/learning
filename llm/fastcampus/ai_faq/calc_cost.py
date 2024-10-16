def calculate_cost(prompt_tokens, completion_tokens, type="chat"):
    if type == "embedding":
        cost = print(prompt_tokens / 1000000 * 0.13 + completion_tokens / 1000000 * 0) * 1380
        print(f"Cost : {cost}원")
    else:
        cost = (prompt_tokens / 1000000 * 0.15 + completion_tokens / 1000000 * 0.6) * 1380
        print(f"Cost : {cost}원")