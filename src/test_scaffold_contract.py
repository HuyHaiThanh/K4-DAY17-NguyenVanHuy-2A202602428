"""Check public scaffold declarations without requiring a Git checkout or live API."""
import ast
import json
from dataclasses import replace
from pathlib import Path
import pytest
from config import load_config
from agent_advanced import AgentContext, AdvancedAgent
from agent_baseline import BaselineAgent
from memory_store import UserProfileStore


def test_original_scaffold_declarations():
    root = Path(__file__).parent
    expected = json.loads((root / 'scaffold_contract.json').read_text(encoding='utf-8'))
    for filename, declarations in expected.items():
        actual = {}
        def visit(nodes, prefix=''):
            for node in nodes:
                if isinstance(node, ast.FunctionDef):
                    actual[prefix + node.name] = [ast.dump(node.args, include_attributes=False), ast.dump(node.returns, include_attributes=False) if node.returns else None]
                elif isinstance(node, ast.ClassDef):
                    actual[prefix + node.name] = [ast.dump(x, include_attributes=False) for x in node.body if isinstance(x, ast.AnnAssign)]
                    visit(node.body, prefix + node.name + '.')
        visit(ast.parse((root / filename).read_text(encoding='utf-8')).body)
        for name, signature in declarations.items():
            assert actual.get(name) == signature, (filename, name)


@pytest.mark.parametrize('agent_class', [BaselineAgent, AdvancedAgent])
def test_default_constructor_without_credentials(tmp_path, monkeypatch, agent_class):
    import importlib
    config = load_config()
    config = replace(config, state_dir=tmp_path, model=replace(config.model, provider='openai', api_key=None))
    module = importlib.import_module(agent_class.__module__)
    def unexpected_model_call(*args):
        pytest.fail('Default construction without credentials must stay offline')
    monkeypatch.setattr(module, 'build_chat_model', unexpected_model_call)
    agent = agent_class(config)
    assert agent.force_offline is False
    assert agent.langchain_agent is None
    assert isinstance(agent.reply('user', 'thread', 'Mình tên là Lan.'), dict)
    offline = agent_class(config, force_offline=True)
    assert offline.force_offline is True


def test_original_context_and_markdown_path(tmp_path):
    context = AgentContext(user_id='dungct', memory_path='User.md')
    assert context.user_id == 'dungct'
    store = UserProfileStore(tmp_path)
    assert store.path_for('dungct') == tmp_path / 'dungct' / 'User.md'
    store.write_text('dungct', '# User\n- name: Lan\n')
    assert store.facts('dungct')['name'] == 'Lan'
    assert store.path_for('../user').is_relative_to(tmp_path)
