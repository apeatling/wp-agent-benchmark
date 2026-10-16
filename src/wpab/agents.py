"""Harbor's agents for each harness, plus one simulated reply.

People often answer an agent's first questions with "just go ahead". If an agent stops before creating
or changing any files (usually to ask what the person wants), it gets that one reply in the same session,
and the run is marked as nudged. Nothing else about the agents is changed.

The nudge is recorded on the host, next to the step's logs, never inside the agent's container.
Harnesses that can't continue a session (Grok Build, Cursor) don't get the reply; their runs record
nudged as null. Antigravity can, through its conversation IDs; see AntigravityCli below.
"""
import asyncio
import json
import os
from pathlib import Path

from . import defs

from harbor.agents.capabilities import AgentCapabilities
from harbor.agents.installed.antigravity_cli import AntigravityCli as HarborAntigravityCli
from harbor.agents.installed.claude_code import ClaudeCode as HarborClaudeCode
from harbor.agents.installed.codex import Codex as HarborCodex
from harbor.agents.installed.cursor_cli import CursorCli as HarborCursorCli
from harbor.agents.installed.gemini_cli import GeminiCli as HarborGeminiCli
from harbor.agents.installed.grok_build import GrokBuild as HarborGrokBuild
from harbor.agents.installed.kimi_cli import KimiCli as HarborKimiCli
from harbor.agents.installed.kimi_code import KimiCode as HarborKimiCode
from harbor.agents.installed.opencode import OpenCode as HarborOpenCode
from harbor.agents.installed.qwen_code import QwenCode as HarborQwenCode

NUDGE = 'Use your best judgement and go ahead.'
# Site files in the working folder that are new or changed since the image was built. Hidden files (such as
# .git) and notes (.md, .txt) don't count, so an agent that stopped to ask and left a plan still gets the reply. The task's Dockerfile touches /var/lib/wpab/started after copying in any starting files.
CHANGED_FILES = ("find /app -type f -not -path '*/.*' -newer /var/lib/wpab/started "
                 "-not -iname '*.md' -not -iname '*.txt' -print -quit | wc -l")


def record(agent, **values):
    """Write run facts next to this step's logs on the host, where the agent can't reach them."""
    path = Path(agent.logs_dir).parent / 'wpab.json'
    data = json.loads(path.read_text()) if path.exists() else {}
    data.update(values)
    path.write_text(json.dumps(data, indent=2))


class NudgeOnce:
    async def run(self, instruction, environment, context):
        await super().run(instruction, environment, context)
        if self._resume or self._load:
            return  # a later turn in the same session, not the first request
        if not self.capabilities.resume:
            record(self, nudged=None)
            return
        result = await self.exec_as_root(environment, command=CHANGED_FILES)
        nudged = (result.stdout or '').strip() == '0'
        record(self, nudged=nudged)
        if nudged:
            await self.resume(NUDGE, environment, context)


class ClaudeCode(NudgeOnce, HarborClaudeCode):
    pass


class Codex(NudgeOnce, HarborCodex):
    pass


class GeminiCli(NudgeOnce, HarborGeminiCli):
    pass


class OpenCode(NudgeOnce, HarborOpenCode):
    pass


class QwenCode(NudgeOnce, HarborQwenCode):
    pass


class KimiCli(NudgeOnce, HarborKimiCli):
    pass


class KimiCode(NudgeOnce, HarborKimiCode):
    """Kimi Code, reaching the open-weight Kimi model through OpenRouter. The key comes from the host
    environment at run time, so it isn't written into the job's config the way --agent-env values are."""

    def _runtime_env(self):
        env = super()._runtime_env()
        key = os.environ.get('OPENROUTER_API_KEY')
        if key:
            # A 128K window, not the full 262K, so each request reserves less credit with OpenRouter.
            env.update({'KIMI_MODEL_BASE_URL': 'https://openrouter.ai/api/v1', 'KIMI_MODEL_API_KEY': key,
                        'KIMI_MODEL_MAX_CONTEXT_SIZE': '131072'})
        return env


class GrokBuild(NudgeOnce, HarborGrokBuild):
    """xAI's Grok Build, with sessions continued like the other harnesses.

    The grok CLI continues a session with `--resume <session id>`, but Harbor's integration starts a fresh
    session on every turn. This keeps the first turn's session ID in the trial folder and, on later turns,
    resumes it instead, so the follow-up questions reach the same conversation.
    """
    capabilities = AgentCapabilities(atif=True, resume=True)

    def __init__(self, *args, **kwargs):
        # Grok waits up to 10 minutes for background tasks before exiting, and agents often leave a preview
        # server running. A minute is enough for real work to finish; Harbor then stops what's left.
        kwargs.setdefault('background_wait_sec', 60)
        super().__init__(*args, **kwargs)

    def _id_file(self):
        return Path(self.logs_dir).parent / 'wpab-grok.json'

    def _build_run_script(self, escaped_instruction):
        if self._resume:
            saved = json.loads(self._id_file().read_text()).get('session_id') if self._id_file().exists() else None
            if not saved:
                raise RuntimeError('No Grok session ID to continue; the first turn may have failed.')
            self._session_id = saved
            script = super()._build_run_script(escaped_instruction)
            return script.replace(f'--session-id {saved}', f'--resume {saved}')
        return super()._build_run_script(escaped_instruction)

    async def run(self, instruction, environment, context):
        first = not self._resume and not self._load
        if first:
            # Saved before the turn, so a follow-up can continue it even if this turn times out.
            self._id_file().write_text(json.dumps({'session_id': self._session_id}))
        await super().run(instruction, environment, context)


class CursorCli(NudgeOnce, HarborCursorCli):
    """Cursor's CLI (cursor-agent), with sessions continued like the other harnesses.

    cursor-agent can continue a chat (`--resume <chatId>`), and reports the ID in its stream output's init
    event, but Harbor 0.23's integration doesn't use it. This reads the ID from the first turn and passes it
    on later turns. It also records the model Cursor says it served, since Cursor can route to another model.
    """
    capabilities = AgentCapabilities(atif=True, resume=True)
    _chat_id = None

    def _read_init(self):
        """The init event from the stream log of the turn that just ran."""
        log = Path(self.logs_dir) / self._OUTPUT_FILENAME
        if not log.exists():
            return {}
        for line in log.read_text(errors='ignore').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'system' and event.get('subtype') == 'init':
                return event
        return {}

    def _id_file(self):
        return Path(self.logs_dir).parent / 'wpab-cursor.json'

    def build_cli_flags(self):
        flags = super().build_cli_flags()
        if self._resume:
            saved = json.loads(self._id_file().read_text()).get('chat_id') if self._id_file().exists() else None
            cid = self._chat_id or saved or self._read_init().get('session_id')
            if not cid:
                raise RuntimeError('No Cursor chat ID to continue; the first turn may have failed.')
            flags = f"{flags} --resume {cid}".strip()
        return flags

    async def run(self, instruction, environment, context):
        first = not self._resume and not self._load
        try:
            await HarborCursorCli.run(self, instruction, environment, context)
        finally:
            # Kept even when the turn times out, so the follow-up can still reach the same chat.
            if first:
                init = self._read_init()
                self._chat_id = init.get('session_id')
                self._id_file().write_text(json.dumps({'chat_id': self._chat_id}))
                record(self, served_model=init.get('model'))
        if first:
            result = await self.exec_as_root(environment, command=CHANGED_FILES)
            nudged = (result.stdout or '').strip() == '0'
            record(self, nudged=nudged)
            if nudged:
                await self.resume(NUDGE, environment, context)


class AntigravityCli(NudgeOnce, HarborAntigravityCli):
    """Antigravity's CLI (agy), with sessions continued like the other harnesses.

    agy can continue a conversation (`--conversation <id>`), and reports the ID in its stream output, but
    Harbor 0.23's integration doesn't use it (harbor-framework/harbor#2803). This reads the ID from the
    first turn and passes it on later turns, so the nudge and the follow-up go to the same conversation.
    """
    capabilities = AgentCapabilities(atif=True, resume=True)
    _conversation_id = None
    # agy waits for background tasks such as a dev server it started, so a turn can hang until the run's
    # time limit. Ten minutes is plenty for a turn and leaves time for the follow-up questions.
    _PRINT_TIMEOUT = '10m'

    def _read_conversation_id(self):
        """The conversation ID from the stream log of the turn that just ran."""
        log = Path(self.logs_dir) / self._STREAM_LOG_FILENAME
        if not log.exists():
            return None
        for line in log.read_text(errors='ignore').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            cid = event.get('conversation_id') or (event.get('init') or {}).get('conversation_id')
            if cid:
                return cid
        return None

    def build_cli_flags(self):
        flags = super().build_cli_flags()
        if self._resume:
            saved = json.loads(self._id_file().read_text()).get('conversation_id') if self._id_file().exists() else None
            # The first turn's stream log is still there until this turn runs, even if that turn timed out.
            cid = self._conversation_id or saved or self._read_conversation_id()
            if not cid:
                raise RuntimeError('No Antigravity conversation ID to continue; the first turn may have failed.')
            flags = f"{flags} --conversation {cid}".strip()
        return flags

    def _id_file(self):
        return Path(self.logs_dir).parent / 'wpab-antigravity.json'

    async def run(self, instruction, environment, context):
        resuming = self._resume
        try:
            await HarborAntigravityCli.run(self, instruction, environment, context)
        finally:
            # Kept even when the turn times out, so the follow-up can still reach the same conversation.
            if not resuming and not self._load:
                self._conversation_id = self._read_conversation_id()
                self._id_file().write_text(json.dumps({'conversation_id': self._conversation_id}))
        if not resuming and not self._load:
            # The nudge, as for the other harnesses.
            result = await self.exec_as_root(environment, command=CHANGED_FILES)
            nudged = (result.stdout or '').strip() == '0'
            record(self, nudged=nudged)
            if nudged:
                await self.resume(NUDGE, environment, context)


class SiteOwner:
    """Building: the site owner replies between turns (see wpab.owner and benchmarks/build/owner.toml).

    After each turn: keep a copy of the turn's output, run the checks as a snapshot, and ask the owner for a
    reply. The conversation ends when the owner has nothing to say or has replied max_replies times. Everything
    is written next to the step's logs on the host (owner-dialogue.json, with the agent's messages, so it's a
    transcript: never committed), and a summary goes in wpab.json.

    A Building task is recognised by its instruction (tasks/build/*/*/instruction.md); its checks run in the task's
    checker, not here (see _snapshot).
    """
    STREAM = None  # the file the harness writes each turn's output to, in logs_dir

    def _last_message(self, text):
        raise NotImplementedError

    def _task_dir(self, instruction):
        return next((f.parent for f in sorted((defs.ROOT / 'tasks' / 'build').glob('*/*/instruction.md'))
                     if f.read_text().strip() == instruction.strip()), None)

    async def _snapshot(self, environment):
        """The checks right now, run in the task's checker beside the site (environment/checker) while the agent is
        between turns. The checks and their login are only ever in the checker, never in the agent's sandbox, so
        nothing the agent leaves running can read them or change what they find."""
        result = await environment.service_exec('python3 /checks/checks.py --snapshot 2>&1', service='checker', timeout_sec=180)
        lines = [l for l in (result.stdout or '').splitlines() if l.startswith('{')]
        return json.loads(lines[-1]) if lines else {'error': (result.stdout or '')[-300:]}

    async def run(self, instruction, environment, context):
        if self._resume or self._load:
            return await super().run(instruction, environment, context)
        await super().run(instruction, environment, context)
        from . import owner  # imported here: owner imports classify, which the agents don't otherwise need
        logs = Path(self.logs_dir)
        task_dir = self._task_dir(instruction)
        request_id, facts, follow = owner.card(instruction)
        max_replies = owner.rules()['max_replies']
        dialogue, replies, end, turn = [], 0, None, 1
        path = logs.parent / 'owner-dialogue.json'
        while True:
            stream = logs / self.STREAM
            text = stream.read_text(errors='replace') if stream.exists() else ''
            (logs / f'turn-{turn}-{self.STREAM}').write_text(text)
            message = self._last_message(text) or ''
            entry = {'turn': turn, 'message': message, 'checks': await self._snapshot(environment) if task_dir else None}
            dialogue.append(entry)
            if replies >= max_replies:
                end = 'reply_limit'
            else:
                try:
                    model, probs, fact = await asyncio.to_thread(owner.classify_turn, message, facts)
                    sent = any('follow_up' in (e.get('reply_ids') or []) for e in dialogue)
                    if owner.satisfied(probs, follow, sent):
                        entry.update(classifier=model, answers=probs, fact=fact, reply_ids=[], unsure=[], reply=None, lines=[])
                        end = 'done'
                        path.write_text(json.dumps({'request_id': request_id, 'turns': dialogue, 'end': end}, indent=2, ensure_ascii=False))
                        break
                    said, ids, unsure = owner.reply(probs, fact, facts, already={l for e in dialogue for l in e.get('lines', [])})
                    lines = owner.lines(ids, fact, facts)
                    more = owner.follow_up(probs, follow, sent)
                    if more:
                        said, ids, lines = owner.with_follow_up(ids, lines, more)
                    entry.update(classifier=model, answers=probs, fact=fact, reply_ids=ids, unsure=unsure, reply=said, lines=lines)
                    end = None if said else 'owner_has_nothing_to_say'
                except Exception as e:  # the run keeps what it has; the classifier failing is recorded
                    entry['error'] = str(e)[:300]
                    end = 'classifier_error'
            path.write_text(json.dumps({'request_id': request_id, 'turns': dialogue, 'end': end}, indent=2, ensure_ascii=False))
            if end:
                break
            replies += 1
            turn += 1
            await self.resume(entry['reply'], environment, context)
        found, mcp = owner.workarounds((logs / f'turn-{n}-{self.STREAM}').read_text(errors='replace') for n in range(1, turn + 1))
        record(self, owner={'request_id': request_id, 'turns': turn, 'replies': replies, 'end': end,
                            'workarounds': found, 'connector_calls': mcp,
                            'reply_ids': [e.get('reply_ids') for e in dialogue],
                            'success_by_turn': [(e.get('checks') or {}).get('success') for e in dialogue]})


class ClaudeCodeWithOwner(SiteOwner, HarborClaudeCode):
    STREAM = 'claude-code.txt'

    def _last_message(self, text):
        out = None
        for line in text.splitlines():
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get('type') == 'result':
                out = m.get('result')
        return out


class CodexWithOwner(SiteOwner, HarborCodex):
    STREAM = 'codex.txt'

    def _last_message(self, text):
        out = None
        for line in text.splitlines():
            try:
                m = json.loads(line)
            except ValueError:
                continue
            item = m.get('item') or {}
            if m.get('type') == 'item.completed' and item.get('type') == 'agent_message':
                out = item.get('text')
        return out
