import json
from memory_store import CompactMemoryManager, summarize_messages


def test_repeated_compaction_preserves_earliest_identity_and_latest_correction():
    memory = CompactMemoryManager(300, 2)
    memory.append('t', 'user', 'Mình tên là Lan. Mình đang ở Huế.')
    for _ in range(5):
        memory.append('t', 'user', 'Nội dung tạm thời về hệ thống. ' * 100)
    memory.append('t', 'user', 'Giờ mình đang ở Đà Nẵng chứ không còn ở Huế.')
    for _ in range(5):
        memory.append('t', 'user', 'Thảo luận tiếp về chi phí. ' * 100)
    summary = memory.context('t')['summary']
    facts = json.loads(summary.split('\nContext: ')[0][7:])
    assert facts['name'] == 'Lan'
    assert facts['location'] == 'Đà Nẵng'
    assert memory.compaction_count('t') > 2
    assert len(summary) <= 400


def test_question_does_not_change_summary_fact():
    summary = summarize_messages([{'role': 'user', 'content': 'Mình tên là Lan.'}, {'role': 'user', 'content': 'Tên mình là gì?'}])
    assert json.loads(summary.split('\nContext: ')[0][7:])['name'] == 'Lan'
