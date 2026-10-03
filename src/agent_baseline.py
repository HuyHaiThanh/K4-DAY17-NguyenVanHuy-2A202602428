from dataclasses import dataclass, field
from config import LabConfig, load_config
from memory_store import estimate_tokens, extract_profile_updates
from model_provider import build_chat_model
from offline_response import answer_from_facts

@dataclass
class SessionState:
    messages: list[dict[str, str]] = field(default_factory=list)
    token_usage: int = 0
    prompt_tokens_processed: int = 0


class BaselineAgent:
    def __init__(self, config: LabConfig | None = None, force_offline: bool = False):
        self.config = config or load_config()
        self.sessions = {}
        self.owners = {}
        self.langchain_agent = None if force_offline else self._maybe_build_langchain_agent()

    def _maybe_build_langchain_agent(self):
        # Live mode is explicit through force_offline=False; errors are not silently hidden.
        return build_chat_model(self.config.model)

    def reply(self, user_id: str, thread_id: str, message: str) -> dict:
        if thread_id in self.owners and self.owners[thread_id] != user_id:
            raise ValueError('Thread belongs to another user')
        self.owners[thread_id] = user_id
        return self._reply_offline(thread_id, message)

    def _reply_offline(self, thread_id: str, message: str) -> dict:
        state = self.sessions.setdefault(thread_id, SessionState())
        state.messages.append({'role': 'user', 'content': message})
        prompt_tokens = sum(estimate_tokens(m['content']) for m in state.messages)
        if self.langchain_agent is None:
            facts = {}
            for m in state.messages:
                if m['role'] == 'user':
                    facts.update(extract_profile_updates(m['content']))
            answer = answer_from_facts(message, facts)
        else:
            result = self.langchain_agent.invoke([(m['role'], m['content']) for m in state.messages])
            answer = result.content if isinstance(result.content, str) else str(result.content)
        state.messages.append({'role': 'assistant', 'content': answer})
        tokens = estimate_tokens(answer)
        state.token_usage += tokens
        state.prompt_tokens_processed += prompt_tokens
        return {'answer': answer, 'agent_tokens': tokens, 'prompt_tokens': prompt_tokens}

    def token_usage(self, thread_id: str) -> int:
        return self.sessions.get(thread_id, SessionState()).token_usage

    def prompt_token_usage(self, thread_id: str) -> int:
        return self.sessions.get(thread_id, SessionState()).prompt_tokens_processed

    def compaction_count(self, thread_id: str) -> int:
        return 0
