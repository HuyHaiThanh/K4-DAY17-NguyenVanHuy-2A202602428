from config import LabConfig, load_config
from memory_store import CompactMemoryManager, UserProfileStore, estimate_tokens, extract_profile_updates
from model_provider import build_chat_model
from offline_response import answer_from_facts


class AdvancedAgent:
    def __init__(self, config: LabConfig | None = None, force_offline: bool = False):
        self.config = config or load_config()
        self.profile_store = UserProfileStore(self.config.state_dir / 'profiles')
        self.compact_memory = CompactMemoryManager(self.config.compact_threshold_tokens, self.config.compact_keep_messages)
        self.thread_tokens = {}
        self.thread_prompt_tokens = {}
        self.owners = {}
        self.langchain_agent = None if force_offline else self._maybe_build_langchain_agent()

    def _maybe_build_langchain_agent(self):
        return build_chat_model(self.config.model)

    def reply(self, user_id: str, thread_id: str, message: str) -> dict:
        if thread_id in self.owners and self.owners[thread_id] != user_id:
            raise ValueError('Thread belongs to another user')
        self.owners[thread_id] = user_id
        return self._reply_offline(user_id, thread_id, message)

    def _reply_offline(self, user_id: str, thread_id: str, message: str) -> dict:
        for key, value in extract_profile_updates(message).items():
            self.profile_store.upsert_fact(user_id, key, value)
        self.compact_memory.append(thread_id, 'user', message)
        prompt_tokens = self._estimate_prompt_context_tokens(user_id, thread_id)
        if self.langchain_agent is None:
            answer = self._offline_response(user_id, thread_id, message)
        else:
            context = self.compact_memory.context(thread_id)
            prompt = [('system', self.profile_store.read_text(user_id) + '\n' + context['summary'])]
            prompt.extend((m['role'], m['content']) for m in context['messages'])
            result = self.langchain_agent.invoke(prompt)
            answer = result.content if isinstance(result.content, str) else str(result.content)
        self.compact_memory.append(thread_id, 'assistant', answer)
        tokens = estimate_tokens(answer)
        self.thread_tokens[thread_id] = self.token_usage(thread_id) + tokens
        self.thread_prompt_tokens[thread_id] = self.prompt_token_usage(thread_id) + prompt_tokens
        return {'answer': answer, 'agent_tokens': tokens, 'prompt_tokens': prompt_tokens}

    def _estimate_prompt_context_tokens(self, user_id: str, thread_id: str) -> int:
        context = self.compact_memory.context(thread_id)
        return estimate_tokens(self.profile_store.read_text(user_id)) + estimate_tokens(context['summary']) + sum(estimate_tokens(m['content']) for m in context['messages'])

    def _offline_response(self, user_id: str, thread_id: str, message: str) -> str:
        facts = self.profile_store.facts(user_id)
        # Recent user assertions can also answer temporary facts in this thread.
        for m in self.compact_memory.context(thread_id)['messages']:
            if m['role'] == 'user':
                for key, value in extract_profile_updates(m['content']).items():
                    facts.setdefault(key, value)
        return answer_from_facts(message, facts)

    def token_usage(self, thread_id: str) -> int:
        return self.thread_tokens.get(thread_id, 0)

    def prompt_token_usage(self, thread_id: str) -> int:
        return self.thread_prompt_tokens.get(thread_id, 0)

    def memory_file_size(self, user_id: str) -> int:
        return self.profile_store.file_size(user_id)

    def compaction_count(self, thread_id: str) -> int:
        return self.compact_memory.compaction_count(thread_id)
