def answer_from_facts(message: str, facts: dict[str, str]) -> str:
    low = message.lower()
    keys = []
    for key, terms in {
        'name': ('tên', 'là ai'), 'location': ('ở đâu', 'nơi ở', 'huế', 'đà nẵng', 'hà nội'),
        'profession': ('nghề', 'làm nghề', 'product manager'),
        'favorite_drink': ('đồ uống',), 'favorite_food': ('món ăn',),
        'pet': ('nuôi',), 'response_style': ('style', 'kiểu trả lời'),
        'interests': ('quan tâm', 'kỹ thuật chính'),
    }.items():
        if any(term in low for term in terms):
            keys.append(key)
    if 'tóm tắt' in low:
        keys = list(facts)
    if not keys:
        return 'Đã ghi nhận. Bạn có thể hỏi lại thông tin trong cuộc trò chuyện.'
    known = [f'{key}: {facts[key]}' for key in keys if key in facts]
    missing = [key for key in keys if key not in facts]
    if missing:
        known.append('Chưa có thông tin: ' + ', '.join(missing))
    return '; '.join(known)
