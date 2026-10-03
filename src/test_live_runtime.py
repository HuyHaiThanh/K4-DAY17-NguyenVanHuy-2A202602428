from dataclasses import replace
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from config import load_config
from agent_baseline import BaselineAgent
from agent_advanced import AdvancedAgent
from live_runtime import LiveRuntime


class ToolReadyFakeModel(FakeListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_graph_checkpoint_thread_isolation(tmp_path):
    config = replace(load_config(), state_dir=tmp_path)
    runtime = LiveRuntime(ToolReadyFakeModel(responses=['Lan', 'Không biết']), config)
    runtime.reply('u', 'first', 'Mình tên là Lan.')
    runtime.reply('u', 'second', 'Mình tên gì?')
    first = runtime.graph.get_state({'configurable': {'thread_id': 'first'}}).values['messages']
    second = runtime.graph.get_state({'configurable': {'thread_id': 'second'}}).values['messages']
    assert 'Lan' in first[0].content
    assert all('Lan' not in m.content for m in second)
    assert runtime.totals['first']['prompt'] > 0


def test_advanced_graph_summarizes_and_injects_profile(tmp_path):
    config = replace(load_config(), state_dir=tmp_path, compact_threshold_tokens=100, compact_keep_messages=2)
    agent = AdvancedAgent(config, True)
    model = ToolReadyFakeModel(responses=['Tóm tắt: thảo luận hệ thống.', 'Đã ghi nhận.'])
    runtime = LiveRuntime(model, config, advanced=agent)
    agent.langchain_agent = runtime
    agent.force_offline = False
    agent.reply('u', 't', 'Mình tên là Lan.')
    for _ in range(4):
        agent.reply('u', 't', 'Ngữ cảnh dài về hệ thống. ' * 100)
    assert agent.compaction_count('t') > 0
    assert runtime.totals['t']['aux_prompt'] > 0
    assert runtime.totals['t']['aux_output'] > 0
    assert agent.prompt_token_usage('t') > 0
    assert agent.profile_store.facts('u')['name'] == 'Lan'
    assert runtime.graph.get_state({'configurable': {'thread_id': 't'}}).values['messages']


def test_baseline_live_reply_uses_graph(tmp_path):
    config = replace(load_config(), state_dir=tmp_path)
    agent = BaselineAgent(config, True)
    agent.langchain_agent = LiveRuntime(ToolReadyFakeModel(responses=['Xin chào']), config)
    agent.force_offline = False
    result = agent.reply('u', 't', 'Chào bạn')
    assert result['answer'] == 'Xin chào'
    assert agent.token_usage('t') == result['agent_tokens']


def test_profile_tools_execute_and_reject_fabricated_corrections(tmp_path):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage, ToolMessage
    class ToolMessages(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self
    config = replace(load_config(), state_dir=tmp_path)
    agent = AdvancedAgent(config, True)
    agent.reply('u', 'offline', 'Mình tên là Lan. Mình đang ở Huế.')
    model = ToolMessages(responses=[
        AIMessage(content='', tool_calls=[{'id': 'read', 'name': 'read_user_profile', 'args': {}}, {'id': 'edit', 'name': 'edit_user_profile', 'args': {'key': 'location', 'value': 'Hà Nội'}}, {'id': 'write', 'name': 'write_user_profile', 'args': {}}]),
        AIMessage(content='Lan ở Huế.')])
    runtime = LiveRuntime(model, config, advanced=agent)
    result = runtime.reply('u', 'live', 'Mình đang ở đâu?')
    assert result['answer'] == 'Lan ở Huế.'
    state = runtime.graph.get_state({'configurable': {'thread_id': 'live'}}).values
    tools = {m.name: m.content for m in state['messages'] if isinstance(m, ToolMessage)}
    assert 'Lan' in tools['read_user_profile']
    assert 'Rejected' in tools['edit_user_profile']
    assert 'No new' in tools['write_user_profile']
    assert agent.profile_store.facts('u')['location'] == 'Huế'


def test_dynamic_prompt_and_sdk_token_usage(tmp_path):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    from pydantic import Field
    class RecordingModel(FakeMessagesListChatModel):
        prompts: list = Field(default_factory=list)
        def bind_tools(self, tools, **kwargs):
            return self
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.prompts.append(messages)
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
    config = replace(load_config(), state_dir=tmp_path)
    agent = AdvancedAgent(config, True)
    agent.reply('u', 'offline', 'Mình tên là Lan.')
    model = RecordingModel(responses=[AIMessage(content='Lan', usage_metadata={'input_tokens': 80, 'output_tokens': 10, 'total_tokens': 90})])
    result = LiveRuntime(model, config, advanced=agent).reply('u', 't', 'Mình tên gì?')
    assert 'Lan' in model.prompts[0][0].content
    assert result['prompt_tokens'] == 80
    assert result['agent_tokens'] == 10


def test_live_benchmark_cli_with_judge(tmp_path, monkeypatch, capsys):
    import sys
    import benchmark
    import agent_baseline
    import agent_advanced
    import model_provider
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    config = replace(load_config(), state_dir=tmp_path)
    config.model = replace(config.model, provider='openai', api_key='fake-key')
    dataset = [{'id': 'one', 'user_id': 'u', 'turns': ['Mình tên là Lan.'], 'recall_questions': [{'question': 'Mình tên gì?', 'expected_contains': ['Lan']}]}]
    monkeypatch.setattr(benchmark, 'load_config', lambda: config)
    monkeypatch.setattr(benchmark, 'load_conversations', lambda path: dataset)
    monkeypatch.setattr(agent_baseline, 'build_chat_model', lambda c: ToolReadyFakeModel(responses=['Lan']))
    monkeypatch.setattr(agent_advanced, 'build_chat_model', lambda c: ToolReadyFakeModel(responses=['Lan']))
    monkeypatch.setattr(model_provider, 'build_chat_model', lambda c: FakeMessagesListChatModel(responses=[AIMessage(content='{"score": 0.75}')]))
    monkeypatch.setattr(sys, 'argv', ['benchmark.py', '--live', '--judge'])
    benchmark.main()
    output = capsys.readouterr().out
    assert 'Standard Benchmark' in output
    assert 'Long-Context Stress Benchmark' in output
    assert '75.0%' in output
    assert 'summarization overhead' in output
    assert 'Judge calls: 4' in output
