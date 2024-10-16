def calculate_cost(prompt_tokens, completion_tokens):
    cost = (prompt_tokens / 1000000 * 0.15 + completion_tokens / 1000000 * 0.6) * 1380
    print(f"Cost : {cost}원")
    # return (prompt_tokens / 1000000 * 0.15 + completion_tokens / 1000000 * 0.6) * 1380